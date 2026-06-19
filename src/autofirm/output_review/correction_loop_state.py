"""Bounded correction-loop state + the send-back payload — looping forever is impossible.

What this does
--------------
Defines the two frozen contracts that drive the gate's correction loop (the
deterministic ``regenerate -> re-review`` cycle that runs when an artifact fails):

* :class:`CorrectionSendBack` — the payload handed back to a builder when a verdict
  fails. It carries the failing ``artifact_ref``, the **BLOCKING findings only**
  (each with its locator / expected / actual), and the attempt number, so the
  regeneration is *targeted at the exact defect sites* — never a blind retry.
* :class:`CorrectionLoopState` — the immutable budget that bounds the loop. Attempts
  are numbered ``1..max_attempts`` **inclusive**; once every attempt is spent the
  budget is *exhausted* and the state refuses to advance. This is the structural
  guarantee that the gate can never spin forever on an artifact it cannot fix.

Why it exists / where it sits
-----------------------------
Per ``docs/research/B16-output-review-and-verification/SYNTHESIS.md`` (the
generator/evaluator send-back loop) and the ratified gate plan: an independent
evaluator that fails an artifact must hand the builder an *actionable* defect list
and re-review the fix — but a correction loop with no bound is a denial-of-service
on itself. This module makes the bound a **type invariant**, not a convention.

Security / compliance invariants upheld (CLAUDE.md §5.6, §3.6)
-------------------------------------------------------------
* **Bounded by construction (no infinite loop):** ``record_and_advance`` refuses,
  fail-closed, to advance once ``budget_exhausted`` — there is no field combination
  that yields an unbounded loop.
* **A send-back is only ever for a real failure:** a :class:`CorrectionSendBack`
  with zero findings, or any non-BLOCKING finding, is refused — you cannot send back
  a clean (or merely advisory) artifact (fail-closed).
* **Functional / frozen:** ``record_and_advance`` returns a NEW state; the original
  is never mutated, so history and the budget cannot be tampered with in place.
* **No PII:** carries opaque ``artifact_ref`` + findings only, never raw content.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from autofirm.output_review.output_review_errors import OutputReviewError
from autofirm.output_review.review_finding_and_severity_contracts import (
    CheckSeverity,
    ReviewFinding,
)
from autofirm.output_review.review_verdict_contract import ReviewVerdict

__all__ = ["CorrectionLoopState", "CorrectionSendBack"]


class CorrectionSendBack(BaseModel):
    """The actionable defect payload returned to a builder when a verdict fails.

    Inputs
    ------
    * ``artifact_ref`` — opaque reference to the failing artifact (non-blank).
    * ``blocking_findings`` — the BLOCKING findings that failed the verdict; each
      carries its locator / expected / actual so regeneration is *targeted*. Must be
      NON-EMPTY and EVERY member must be ``CheckSeverity.BLOCKING``.
    * ``attempt`` — the 1-based attempt number this send-back belongs to (``>= 1``).

    Failure modes
    -------------
    Raises :class:`OutputReviewError` on a blank ``artifact_ref``, an empty
    ``blocking_findings``, any non-BLOCKING member, or ``attempt < 1`` — a send-back
    that carries nothing actionable, or describes a non-failure, is meaningless and
    is refused fail-closed (CLAUDE.md §5.6).
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    artifact_ref: str
    blocking_findings: tuple[ReviewFinding, ...]
    attempt: int

    @field_validator("artifact_ref")
    @classmethod
    def _non_blank_ref(cls, value: str) -> str:
        # fail-closed: a send-back for an unidentifiable artifact cannot be routed.
        if not value or not value.strip():
            raise OutputReviewError("CorrectionSendBack artifact_ref must be non-blank")
        return value

    @field_validator("attempt")
    @classmethod
    def _attempt_at_least_one(cls, value: int) -> int:
        # fail-closed: attempts are 1-based; a 0/negative attempt is incoherent.
        if value < 1:
            raise OutputReviewError("CorrectionSendBack attempt must be >= 1")
        return value

    @field_validator("blocking_findings")
    @classmethod
    def _all_blocking_and_non_empty(
        cls, value: tuple[ReviewFinding, ...]
    ) -> tuple[ReviewFinding, ...]:
        # fail-closed: a send-back with no findings, or one carrying an ADVISORY
        # finding, would tell the builder to "fix" something that does not block
        # delivery — refuse it. Identity comparison against the enum member (not ==
        # on a free string) so a spoofed look-alike can never read as blocking.
        if not value:
            raise OutputReviewError(
                "CorrectionSendBack.blocking_findings must be non-empty: "
                "you never send back a passing artifact"
            )
        if any(f.severity is not CheckSeverity.BLOCKING for f in value):
            raise OutputReviewError(
                "CorrectionSendBack.blocking_findings must contain ONLY BLOCKING "
                "findings: advisory findings do not justify a send-back"
            )
        return value


class CorrectionLoopState(BaseModel):
    """The immutable, BOUNDED budget for the regenerate -> re-review loop.

    Attempts are numbered ``1..max_attempts`` **inclusive**. ``start`` opens the loop
    at attempt 1; each :meth:`record_and_advance` appends the just-seen verdict to
    ``history`` and returns a NEW state at the next attempt. Once every attempt has
    been spent the budget is *exhausted* (:attr:`budget_exhausted`) and advancing is
    refused — the structural guarantee against an infinite loop.

    Inputs
    ------
    * ``attempt`` — the current 1-based attempt (``>= 1``).
    * ``max_attempts`` — the inclusive ceiling on attempts (``>= 1``).
    * ``history`` — verdicts seen so far, in order (defaults empty).

    Failure modes
    -------------
    Raises :class:`OutputReviewError` if ``attempt < 1``, ``max_attempts < 1``, or
    ``attempt > max_attempts + 1`` (the post-exhaustion sentinel is the only state
    beyond the ceiling), or if :meth:`record_and_advance` is called once exhausted.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    attempt: int
    max_attempts: int
    history: tuple[ReviewVerdict, ...] = ()

    @field_validator("attempt")
    @classmethod
    def _attempt_at_least_one(cls, value: int) -> int:
        # fail-closed: the loop is 1-based; attempt 0/negative is incoherent.
        if value < 1:
            raise OutputReviewError("CorrectionLoopState attempt must be >= 1")
        return value

    @field_validator("max_attempts")
    @classmethod
    def _max_attempts_at_least_one(cls, value: int) -> int:
        # fail-closed: a budget of < 1 attempt could never review anything.
        if value < 1:
            raise OutputReviewError("CorrectionLoopState max_attempts must be >= 1")
        return value

    @model_validator(mode="after")
    def _attempt_within_budget(self) -> CorrectionLoopState:
        # Sanity bound: the only legal attempt past the ceiling is max_attempts + 1,
        # the sentinel reached *after* the final attempt is recorded (exhausted).
        # Anything higher is a corrupt/forged state — refuse it (fail-closed).
        if self.attempt > self.max_attempts + 1:
            raise OutputReviewError(
                "CorrectionLoopState attempt out of range: "
                f"attempt={self.attempt} > max_attempts+1={self.max_attempts + 1}"
            )
        return self

    @property
    def budget_exhausted(self) -> bool:
        """True once no attempt remains.

        Attempts are ``1..max_attempts`` inclusive, so the budget is exhausted
        exactly when ``attempt > max_attempts`` (i.e. the post-final sentinel
        ``max_attempts + 1`` has been reached). At ``attempt == max_attempts`` one
        attempt still remains, so this is ``False``.
        """
        return self.attempt > self.max_attempts

    def record_and_advance(self, verdict: ReviewVerdict) -> CorrectionLoopState:
        """Append ``verdict`` to history and return a NEW state at the next attempt.

        Functional and frozen-safe: the receiver is never mutated. Fail-closed — if
        the budget is already exhausted there is no attempt to record, so this
        refuses rather than looping past the ceiling (the anti-infinite-loop guard).
        """
        if self.budget_exhausted:
            # fail-closed: the loop is bounded — refuse to advance past exhaustion.
            raise OutputReviewError(
                "CorrectionLoopState budget exhausted: cannot advance past "
                f"max_attempts={self.max_attempts}"
            )
        return CorrectionLoopState(
            attempt=self.attempt + 1,
            max_attempts=self.max_attempts,
            history=(*self.history, verdict),
        )

    @classmethod
    def start(cls, max_attempts: int) -> CorrectionLoopState:
        """Open a fresh loop at attempt 1 with an empty history.

        ``max_attempts`` is validated (``>= 1``) by the model; a smaller budget is
        refused fail-closed.
        """
        return cls(attempt=1, max_attempts=max_attempts, history=())
