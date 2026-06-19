"""The output-review gate: compose N independent checks into one fail-closed verdict.

What this does
--------------
Implements :class:`OutputReviewGate`, the P2 composition root of the output-review
lane. Constructed with an already-populated
:class:`~autofirm.output_review.review_check_protocol.CheckRegistry` and an injected
``clock``, its :meth:`review` runs every registered check over a single
:class:`~autofirm.output_review.reviewable_artifact_contract.ReviewableArtifact`,
collects their findings in a deterministic order, and returns one typed
:class:`~autofirm.output_review.review_verdict_contract.ReviewVerdict` whose
``passed`` flag the verdict itself *derives* from the findings (the false-pass
guard) — the gate never sets ``passed`` directly.

Why it exists / where it sits
-----------------------------
``docs/research/B16-output-review-and-verification/SYNTHESIS.md`` §2.2/§3 makes the
deterministic floor a set of INDEPENDENT checks, and the ratified plan §B.3 makes the
gate their pure composer: it discovers checks via the registry (no check imports
another), runs each, and aggregates. Acceptance is never the builder's word — the gate
is the independent evaluator that stands between a built artifact and any human.

Security / compliance invariants upheld (CLAUDE.md §5.6, §3.11)
--------------------------------------------------------------
* **Fail closed on an empty registry:** a gate with zero checks would vacuously pass
  every artifact, so :meth:`review` refuses to run one (a no-op reviewer is the exact
  false-confidence failure this lane exists to prevent).
* **Fail closed on a raising check:** a check that raises does NOT crash the gate and
  is NEVER silently skipped — its failure is converted into one BLOCKING finding (so
  the verdict cannot pass) and the remaining checks still run. No exception escapes.
* **Deterministic:** checks run in registry order; findings preserve (registry order,
  then each check's own finding order); ``reviewed_at`` comes from the injected clock,
  never ``datetime.now()`` — so the same artifact + clock yields a byte-identical
  verdict (CLAUDE.md §3.11).
* **Omission defence:** ``checks_run`` records exactly which checks executed, so an
  omitted-but-mandatory check is detectable from the verdict alone.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from autofirm.output_review.output_review_errors import OutputReviewError
from autofirm.output_review.review_finding_and_severity_contracts import (
    CHECK_DEFECT_CLASSES,
    CheckSeverity,
    ReviewCheckId,
    ReviewFinding,
)
from autofirm.output_review.review_verdict_contract import ReviewVerdict

if TYPE_CHECKING:
    from collections.abc import Callable
    from datetime import datetime

    from autofirm.output_review.review_check_protocol import CheckRegistry
    from autofirm.output_review.reviewable_artifact_contract import ReviewableArtifact

__all__ = ["OutputReviewGate"]

# Fail-closed (CLAUDE.md §5.6): a gate with no checks would "pass" every artifact by
# default. That is the manufactured-false-confidence failure mode this whole lane
# exists to prevent, so reviewing through an empty registry is refused outright.
_EMPTY_REGISTRY_MESSAGE = (
    "output-review gate has no registered checks — a gate with no checks would "
    "vacuously pass every artifact (fail-closed)"
)


class OutputReviewGate:
    """Compose an injected registry of checks into one derived, fail-closed verdict.

    The gate is a PURE composer: it owns no checks of its own, holds no mutable state
    between reviews, and never sets ``passed`` — it hands the findings to
    :class:`ReviewVerdict`, which derives ``passed`` and refuses any false pass. The
    ``clock`` is injected (never ``datetime.now()``) so a verdict's ``reviewed_at`` is
    fully controlled by the caller and reviews are reproducible (CLAUDE.md §3.11).

    Inputs
    ------
    * ``registry`` — an already-populated
      :class:`~autofirm.output_review.review_check_protocol.CheckRegistry`; the gate
      runs every check it holds, in registration order.
    * ``clock`` — a zero-argument callable returning the ``datetime`` stamped onto the
      verdict. Injected, so the gate never reads the wall clock directly.
    """

    def __init__(
        self, registry: CheckRegistry, clock: Callable[[], datetime]
    ) -> None:
        """Store the populated registry and the injected clock (no validation here).

        The empty-registry refusal lives in :meth:`review` (fail-closed at use), so a
        gate is cheap to construct and the guard fires exactly where a review would
        otherwise vacuously pass.
        """
        self._registry = registry
        self._clock = clock

    def review(self, artifact: ReviewableArtifact) -> ReviewVerdict:
        """Run every registered check over ``artifact`` and return a derived verdict.

        Iterates the registry IN ORDER, runs each check, and concatenates their
        findings (preserving registry order, then each check's own finding order). A
        check that RAISES is converted to a single BLOCKING finding rather than
        crashing the gate or being skipped, and the remaining checks still run. The
        verdict's ``passed`` is left for :class:`ReviewVerdict` to derive — the gate
        never asserts a pass.

        Raises:
            OutputReviewError: if the registry holds no checks (fail-closed — a gate
                with nothing to run would otherwise pass every artifact).
        """
        if len(self._registry) == 0:
            # fail-closed: refuse to "review" with zero checks — see module constant.
            raise OutputReviewError(_EMPTY_REGISTRY_MESSAGE)

        findings: list[ReviewFinding] = []
        for check_id in self._registry.ids():
            # Deterministic order: registry order outer, each check's findings inner.
            findings.extend(self._run_one_check(check_id, artifact))

        return ReviewVerdict(
            artifact_ref=artifact.artifact_ref,
            findings=tuple(findings),
            # Omission defence: record exactly which checks ran (registry order), so an
            # absent mandatory check is detectable from the verdict alone.
            checks_run=self._registry.ids(),
            # Injected clock — never datetime.now() — so reviews are reproducible.
            reviewed_at=self._clock(),
            # passed is intentionally NOT supplied: the verdict derives it (false-pass
            # guard). The gate never manufactures a pass.
        )

    def _run_one_check(
        self, check_id: ReviewCheckId, artifact: ReviewableArtifact
    ) -> tuple[ReviewFinding, ...]:
        """Run one check, converting any exception into a BLOCKING crash finding.

        Returns the check's own findings on success. If the check raises ANY
        exception, returns a one-tuple holding a synthetic BLOCKING finding so the
        verdict cannot pass and the gate keeps running the remaining checks — the
        failure is recorded, never swallowed (fail-closed, CLAUDE.md §5.6).
        """
        check = self._registry.get(check_id)
        try:
            return check.run(artifact)
        except Exception as exc:  # fail-closed: a raising check is a BLOCKING defect.
            # Do NOT crash the gate and do NOT skip silently: a check that blows up is
            # itself a defect that must block delivery and be surfaced for a fix.
            return (self._crash_finding(check_id, artifact.artifact_ref, exc),)

    @staticmethod
    def _crash_finding(
        check_id: ReviewCheckId, artifact_ref: str, exc: Exception
    ) -> ReviewFinding:
        """Build the BLOCKING finding that stands in for a check that raised.

        The defect class is the deterministic minimum (by enum value) of the check's
        registered class set — a fixed choice so a crash for a given check always
        produces the byte-identical finding (CLAUDE.md §3.11). The locator is the
        artifact ref (the whole artifact is suspect — there is no in-check site), and
        the message names the exception type so a fix can target the real failure.
        """
        # min-by-value over the (always non-empty, total) class set is deterministic:
        # a multi-class check (e.g. FAST_LINT -> {MECHANICAL, OMISSION}) always picks
        # the same member, so the crash finding never varies between runs.
        defect_class = min(CHECK_DEFECT_CLASSES[check_id], key=lambda d: d.value)
        return ReviewFinding(
            check_id=check_id,
            severity=CheckSeverity.BLOCKING,  # fail-closed: a crashed check blocks.
            defect_class=defect_class,
            message=(
                f"check {check_id.value!r} raised {type(exc).__name__} during "
                "review — treated as a BLOCKING defect (fail-closed)"
            ),
            locator=artifact_ref,
        )
