"""The review verdict — derives ``passed`` from findings; a false pass is impossible.

What this does
--------------
Defines :class:`ReviewVerdict`, the frozen aggregate of a single review pass. It
collects the findings every check raised and records which checks actually ran. Its
``passed`` flag is **not** a free input the caller sets — it is **derived from the
findings and validated**, so a verdict can never claim to pass while a BLOCKING
finding is present.

Why it exists / where it sits — THE SINGLE MOST IMPORTANT INVARIANT
-------------------------------------------------------------------
``SYNTHESIS.md`` finding #6 and CLAUDE.md §3.6: a green-but-wrong verdict is the
exact failure mode this whole lane exists to prevent (humans estimate ~18% error
rates against an actual ~86% — SYNTHESIS §A.1/src 02). So this contract makes it
**structurally impossible** to construct a passing verdict over any blocking defect.

THE FALSE-PASS GUARD (as implemented):
``passed`` is DERIVED, never trusted as input. A model validator computes
``derived = not any(f.severity is BLOCKING for f in findings)``. Then:
  * if the caller supplied no ``passed`` -> it is set to ``derived``;
  * if the caller supplied ``passed`` and it equals ``derived`` -> accepted;
  * if the caller supplied ``passed != derived`` (e.g. ``passed=True`` with a
    BLOCKING finding present, or ``passed=False`` with none) -> **refused**
    (:class:`OutputReviewError`).
The equivalence ``passed == (no BLOCKING finding present)`` therefore holds for
*every* constructible verdict. Fail-closed: ambiguity resolves to *not passed*,
because a blocking defect always forces ``derived=False`` and the only way to
``passed=True`` is the genuine absence of every blocking finding.

Security / compliance invariants upheld (CLAUDE.md §5.6, §3.11)
--------------------------------------------------------------
* **Cannot manufacture a false pass:** see above — the guard runs at construction
  on the frozen model, so no field combination, ordering, or duplicate can bypass it.
* **Explains itself / omission defence:** ``checks_run`` proves *which* checks
  executed, so an omitted-but-mandatory check is detectable downstream.
* **Fail closed on blanks:** a blank ``artifact_ref`` is refused.
* **No PII:** carries an opaque ``artifact_ref`` and findings only, never raw content.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from autofirm.output_review.output_review_errors import OutputReviewError
from autofirm.output_review.review_finding_and_severity_contracts import (
    CheckSeverity,
    ReviewCheckId,
    ReviewFinding,
)

__all__ = ["ReviewVerdict"]


def _has_blocking(findings: tuple[ReviewFinding, ...]) -> bool:
    """True iff any finding is BLOCKING — the sole determinant of a failed verdict."""
    # Identity comparison against the enum member (not == on a free string) so a
    # spoofed look-alike value can never read as non-blocking (fail-closed).
    return any(f.severity is CheckSeverity.BLOCKING for f in findings)


class ReviewVerdict(BaseModel):
    """A single review pass: findings + which checks ran + a DERIVED ``passed`` flag.

    Inputs
    ------
    * ``artifact_ref`` — opaque reference to the reviewed artifact (never content).
    * ``findings`` — every :class:`ReviewFinding` raised this pass (may be empty).
    * ``checks_run`` — the :class:`ReviewCheckId` set that actually executed
      (omission defence — an absent mandatory check is itself a defect downstream).
    * ``reviewed_at`` — injected timestamp (never ``now()`` inside the model).
    * ``passed`` — OPTIONAL. If omitted it is derived; if supplied it MUST equal the
      derived value or construction is refused. Callers should normally omit it and
      let the gate derive it; the field exists only so a deserialised verdict can be
      re-validated against its own findings.

    Failure modes
    -------------
    Raises :class:`OutputReviewError` if ``passed`` is supplied and disagrees with
    the derivation (the false-pass guard), or if ``artifact_ref`` is blank.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    artifact_ref: str
    findings: tuple[ReviewFinding, ...] = ()
    checks_run: tuple[ReviewCheckId, ...] = ()
    reviewed_at: datetime
    # Derived from findings by the validator below; never trusted as raw input.
    passed: bool | None = None

    @field_validator("artifact_ref")
    @classmethod  # pragma: no mutate  # equivalent: pydantic v2 auto-wraps validators, so removing @classmethod is behaviourally identical (blank still refused, valid still passes)
    def _non_blank_ref(cls, value: str) -> str:
        # fail-closed: a verdict over an unidentifiable artifact cannot be audited.
        if not value or not value.strip():
            raise OutputReviewError("ReviewVerdict artifact_ref must be non-blank")
        return value

    @model_validator(mode="after")
    def _derive_and_guard_passed(self) -> ReviewVerdict:
        """THE FALSE-PASS GUARD: derive ``passed`` and refuse any disagreement.

        Computes the only legitimate value of ``passed`` from the findings, then
        either fills it in (when omitted) or refuses construction if a supplied
        value disagrees. This makes ``passed == (no BLOCKING finding present)`` an
        invariant of every constructible verdict — no ordering, duplicate, or field
        trick can yield ``passed=True`` while a blocking defect exists.
        """
        derived = not _has_blocking(self.findings)  # the single source of truth
        if self.passed is None:
            # Frozen model: assign through object.__setattr__ inside the validator.
            object.__setattr__(self, "passed", derived)
            return self
        if self.passed != derived:
            # fail-closed: someone tried to manufacture a verdict whose pass/fail
            # contradicts its own findings (e.g. passed=True with a BLOCKING finding,
            # or passed=False with none). Refuse — this is the false-pass guard.
            raise OutputReviewError(
                "ReviewVerdict.passed must equal (no BLOCKING finding present); "
                f"supplied={self.passed!r}, derived={derived!r}"
            )
        return self

    @property
    def blocking_findings(self) -> tuple[ReviewFinding, ...]:
        """The blocking subset — the only findings that fail the verdict / send back."""
        return tuple(f for f in self.findings if f.severity is CheckSeverity.BLOCKING)
