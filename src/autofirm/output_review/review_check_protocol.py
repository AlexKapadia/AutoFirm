"""The ReviewCheck Protocol and a fail-closed registry mapping id -> check.

What this does
--------------
Defines the seam every deterministic review check implements and the registry the
gate composes them through:

* :class:`ReviewCheck` — a runtime-checkable Protocol: a check exposes its
  :class:`ReviewCheckId` and a ``run(artifact) -> tuple[ReviewFinding, ...]`` that is
  **pure and deterministic** (same artifact -> same findings) and returns an empty
  tuple when clean. A check is handed only the :class:`ReviewableArtifact` — never
  another check's findings or the verdict, so checks stay independent.
* :class:`CheckRegistry` — a small frozen-at-use mapping from
  :class:`ReviewCheckId` to its check. Registration is fail-closed: a duplicate id
  is refused, and lookup of an unknown id raises rather than returning ``None``.

Why it exists / where it sits
-----------------------------
``SYNTHESIS.md`` §2.2/§3 makes the floor a set of *independent* deterministic
checks; plan §B.3 requires each to be single-responsibility and unable to see another
check's result. The Protocol is that contract; the registry is how the gate discovers
which checks to run without any check importing another. Both ship in P0 so the
checks (P1) and gate (P2) can be built against a stable seam.

Security / compliance invariants upheld (CLAUDE.md §5.6)
-------------------------------------------------------
* **Independence:** ``run`` receives only the artifact; a check cannot read peers'
  findings or the verdict, so one check can never relax another's blocking finding.
* **Fail closed on duplicate registration:** registering two checks under one id is
  refused (an ambiguous registry could silently shadow a mandatory check).
* **Fail closed on unknown lookup:** ``get`` of an unregistered id raises
  :class:`OutputReviewError` rather than returning ``None`` (no silent skip).
* **Id consistency:** a check registered under an id whose ``id`` attribute differs
  is refused, so the registry key always matches the check's self-declared id.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from autofirm.output_review.output_review_errors import OutputReviewError
from autofirm.output_review.review_finding_and_severity_contracts import (
    ReviewCheckId,
    ReviewFinding,
)
from autofirm.output_review.reviewable_artifact_contract import ReviewableArtifact

__all__ = [
    "CheckRegistry",
    "ReviewCheck",
]


@runtime_checkable
class ReviewCheck(Protocol):
    """One independent, pure, deterministic deterministic-floor check.

    A check declares the :class:`ReviewCheckId` it owns and implements ``run``. ``run``
    is a pure function of the artifact: it reads the file bytes + spec + recomputed
    values, returns the findings it raises (empty tuple == clean), and never mutates
    the artifact or consults any other check's result (independence — plan §B.3).
    Determinism is mandatory (CLAUDE.md §3.11): the same artifact must always yield
    the same findings, so verdicts are reproducible.
    """

    @property
    def id(self) -> ReviewCheckId:
        """The closed-set id this check owns (used as its registry key)."""
        ...

    def run(self, artifact: ReviewableArtifact) -> tuple[ReviewFinding, ...]:
        """Inspect ``artifact`` and return the findings raised (empty == clean)."""
        ...


class CheckRegistry:
    """A fail-closed map from :class:`ReviewCheckId` to its single owning check.

    The gate composes the floor by registering each check once and iterating the
    registry. Registration and lookup are both fail-closed (CLAUDE.md §5.6) so a
    mandatory check can neither be silently shadowed nor silently skipped.
    """

    def __init__(self) -> None:
        """Create an empty registry."""
        self._checks: dict[ReviewCheckId, ReviewCheck] = {}

    def register(self, check: ReviewCheck) -> None:
        """Register ``check`` under its self-declared ``id``.

        Raises :class:`OutputReviewError` if the id is already taken (fail-closed:
        an ambiguous registry could silently shadow a mandatory check). The check's
        ``id`` is the key, so the registry can never disagree with the check.
        """
        check_id = check.id
        if check_id in self._checks:
            # fail-closed: two checks under one id is ambiguous — refuse rather than
            # let a late registration silently replace a mandatory floor check.
            raise OutputReviewError(
                f"duplicate registration for check id {check_id!r}"
            )
        self._checks[check_id] = check

    def get(self, check_id: ReviewCheckId) -> ReviewCheck:
        """Return the check for ``check_id``.

        Raises :class:`OutputReviewError` if no check is registered (fail-closed: an
        unknown id is refused, never silently treated as a no-op skip).
        """
        try:
            return self._checks[check_id]
        except KeyError:
            # fail-closed: silently skipping an unregistered check would let a defect
            # in that class escape unreviewed — refuse the lookup instead.
            raise OutputReviewError(f"no check registered for id {check_id!r}") from None

    def ids(self) -> tuple[ReviewCheckId, ...]:
        """The ids currently registered, in registration order (for ``checks_run``)."""
        return tuple(self._checks)

    def __contains__(self, check_id: ReviewCheckId) -> bool:
        """True iff a check is registered under ``check_id``."""
        return check_id in self._checks

    def __len__(self) -> int:
        """The number of registered checks."""
        return len(self._checks)
