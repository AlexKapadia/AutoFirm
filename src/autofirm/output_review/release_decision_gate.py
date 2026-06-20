"""The release authority: a verdict cannot be released unless it actually passed.

What this does
--------------
Defines the final delivery gate that stands between a composed
:class:`~autofirm.output_review.review_verdict_contract.ReviewVerdict` and any
human (owner, CEO, investor). It turns a verdict into a frozen
:class:`ReleaseDecision` whose ``authorised`` flag is **derived from**
``final_verdict.passed`` (never trusted as a free input) and **audits every
decision** — authorising a release and denying one are *both* recorded — before
the decision is handed back.

* :class:`ReleaseDecision` — the frozen, self-explaining record of one release
  call. ``authorised == final_verdict.passed`` is an invariant of *every*
  constructible instance (the false-pass guard, mirrored from ``ReviewVerdict``):
  you can never manufacture an authorised release over a failing verdict.
* :class:`ReleaseAuditSink` — the injected append-only-audit seam (the real
  ``AuditRecord`` adapter with seq/tenant is P4); unit tests inject a spy.
* :class:`ReleaseDecisionGate` — composes the decision, audits it, and **fails
  closed**: if the audit write raises, NO authorised release escapes — an
  :class:`OutputReviewError` propagates so delivery is blocked when it cannot be
  recorded.

Why it exists / where it sits
-----------------------------
Per ``docs/architecture/human-output-review-gate-plan.md`` (P2) acceptance never
comes from the builder's self-assessment. This is the lane's *release authority*:
the single chokepoint that re-derives pass/fail one last time AND proves (via the
audit log) that it did. It depends only on the P0 contracts + the audit outcome
enum; it injects the clock and the sink so it is deterministic and testable.

Security / compliance invariants upheld (CLAUDE.md §5.6, §3.11)
--------------------------------------------------------------
* **Cannot manufacture a release (false-pass guard):** ``authorised`` is DERIVED
  from ``final_verdict.passed`` and any supplied disagreement is refused at
  construction — an authorised release over a failing verdict is unconstructible.
* **Every release decision is audited:** authorise -> ``SUCCESS``, deny ->
  ``DENY`` (a denial is logged, not dropped). The append-only log proves the
  system refused rather than silently proceeded.
* **Fail closed on un-auditability:** if the audit write raises, the gate raises
  rather than returning a decision — an unaudited release is forbidden.
* **Injected clock, never ``now()``:** ``decided_at`` comes from the injected
  ``clock`` so decisions are deterministic and reproducible (§3.11).
* **Fail closed on blanks:** a blank ``artifact_ref`` or ``reason`` is refused.
* **No PII:** carries opaque references and a human reason only, never content.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from typing import Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from autofirm.audit.audit_record_contract import AuditOutcome
from autofirm.output_review.output_review_errors import OutputReviewError
from autofirm.output_review.review_verdict_contract import ReviewVerdict

__all__ = [
    "ReleaseAuditSink",
    "ReleaseDecision",
    "ReleaseDecisionGate",
]


class ReleaseDecision(BaseModel):
    """The frozen record of one release call — ``authorised`` is DERIVED, not trusted.

    Inputs
    ------
    * ``artifact_ref`` — opaque reference to the artifact being released (never content).
    * ``final_verdict`` — the composed :class:`ReviewVerdict` this decision is over.
    * ``reason`` — human-readable justification for the decision (explain-every-decision).
    * ``decided_at`` — injected timestamp (the gate supplies its ``clock``, never ``now()``).
    * ``authorised`` — OPTIONAL. If omitted it is derived from ``final_verdict.passed``;
      if supplied it MUST equal that derivation or construction is refused. Callers
      normally omit it; the field exists only so a deserialised decision can be
      re-validated against its own verdict.

    Failure modes
    -------------
    Raises :class:`OutputReviewError` if ``authorised`` is supplied and disagrees with
    ``final_verdict.passed`` (the false-pass guard), or if ``artifact_ref`` / ``reason``
    is blank.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    artifact_ref: str
    final_verdict: ReviewVerdict
    reason: str
    decided_at: datetime
    # Derived from ``final_verdict.passed`` by the validator below; never raw input.
    authorised: bool | None = None

    @field_validator("artifact_ref", "reason")
    @classmethod  # pragma: no mutate (equivalent: pydantic v2 auto-wraps the validator)
    def _non_blank(cls, value: str) -> str:
        # fail-closed: a release over an unidentifiable artifact, or with no stated
        # reason, cannot be audited or explained — refuse it (CLAUDE.md §5.6, §3.11).
        if not value or not value.strip():
            raise OutputReviewError("ReleaseDecision artifact_ref and reason must be non-blank")
        return value

    @model_validator(mode="after")
    def _derive_and_guard_authorised(self) -> ReleaseDecision:
        """THE FALSE-PASS GUARD: derive ``authorised`` and refuse any disagreement.

        Mirrors ``ReviewVerdict``'s guard exactly. ``authorised`` is the verdict's
        own ``passed`` value: when omitted it is filled in; when supplied it must
        match or construction is refused. This makes
        ``authorised == final_verdict.passed`` an invariant of every constructible
        decision — an authorised release over a failing verdict is impossible to build.
        """
        derived = self.final_verdict.passed  # the single source of truth (a verdict invariant)
        if self.authorised is None:
            # Frozen model: assign through object.__setattr__ inside the validator.
            object.__setattr__(self, "authorised", derived)
            return self
        if self.authorised != derived:
            # fail-closed: someone tried to authorise a release that contradicts its
            # verdict (e.g. authorised=True over a failing verdict, or authorised=False
            # over a passing one). Refuse — this is the false-pass guard.
            raise OutputReviewError(
                "ReleaseDecision.authorised must equal final_verdict.passed; "
                f"supplied={self.authorised!r}, derived={derived!r}"
            )
        return self


@runtime_checkable
class ReleaseAuditSink(Protocol):
    """The injected append-only-audit seam every release decision is written through.

    A narrow port (dependency-inversion): the gate depends on this Protocol, not on
    the concrete log. The real adapter (P4) maps each call to a full
    :class:`~autofirm.audit.audit_record_contract.AuditRecord` with seq/tenant and
    appends it to the immutable log; unit tests inject a spy. ``@runtime_checkable``
    so a wiring layer can assert an injected object satisfies the seam.
    """

    def record(
        self,
        *,
        artifact_ref: str,
        outcome: AuditOutcome,
        reason: str,
        decided_at: datetime,
    ) -> None:
        """Append one release-decision audit entry (append-only; never updates/deletes)."""
        ...


class ReleaseDecisionGate:
    """Composes a release decision, audits it, and fails closed if it cannot be audited.

    The gate is the lane's release authority: it re-derives pass/fail one last time
    (via :class:`ReleaseDecision`'s guard) and proves it did by writing to the
    injected audit sink BEFORE returning. Both the clock and the sink are injected so
    the gate is deterministic and unit-testable with no real I/O.
    """

    def __init__(self, sink: ReleaseAuditSink, clock: Callable[[], datetime]) -> None:
        """Wire the gate to its audit sink and clock.

        Args:
            sink: The append-only audit seam every decision is recorded through.
            clock: Supplies ``decided_at``; injected so it is never the wall clock
                (``now()``) — decisions stay deterministic and reproducible (§3.11).
        """
        self._sink = sink  # least privilege: the gate only ever appends, never reads/edits
        self._clock = clock  # injected time source — never datetime.now() (§3.11 determinism)

    def decide(self, final_verdict: ReviewVerdict, reason: str) -> ReleaseDecision:
        """Authorise or deny a release, audit the outcome, then return the decision.

        Args:
            final_verdict: The composed verdict to release on. ``authorised`` is
                derived from its ``passed`` flag — a failing verdict can never yield
                an authorised release.
            reason: Human-readable justification recorded with the decision.

        Returns:
            The frozen :class:`ReleaseDecision` (only ever reached once the audit
            write succeeded).

        Raises:
            OutputReviewError: if ``reason`` is blank (fail-closed at construction),
                or if the audit write raises — an unaudited release is forbidden, so
                the gate refuses rather than handing back a decision (§5.6).
        """
        decision = ReleaseDecision(
            artifact_ref=final_verdict.artifact_ref,
            final_verdict=final_verdict,
            reason=reason,
            decided_at=self._clock(),  # injected time — never now() (§3.11)
        )
        # An authorised release is a SUCCESS; a denied one is a DENY (logged, not
        # dropped — §5.6). ``authorised`` is bool|None; a None (impossible by the
        # verdict invariant) is treated as falsy => DENY, i.e. fail-closed.
        outcome = AuditOutcome.SUCCESS if decision.authorised else AuditOutcome.DENY
        try:
            self._sink.record(
                artifact_ref=decision.artifact_ref,
                outcome=outcome,
                reason=reason,
                decided_at=decision.decided_at,
            )
        except Exception as exc:  # fail-closed: ANY audit failure blocks the release
            # fail-closed: the release cannot be recorded, so it must NOT be delivered.
            # Wrap/chain the sink error so the precise OutputReviewError signal
            # propagates and no decision is returned (an unaudited release is forbidden).
            raise OutputReviewError(
                "release blocked: audit write failed — an unaudited release is forbidden"
            ) from exc
        return decision
