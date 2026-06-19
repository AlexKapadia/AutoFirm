"""Severity, check-id, defect-class, and finding contracts for the review gate.

What this does
--------------
Defines the shared, frozen vocabulary every deterministic review check speaks:

* :class:`CheckSeverity` — ``BLOCKING`` (fails the verdict) vs ``ADVISORY``
  (recorded, never blocks). The fail-closed default is ``BLOCKING``.
* :class:`ReviewCheckId` — the closed set of checks the gate can run. An unknown
  id cannot be constructed (a fixed set of audit buckets — omission defence).
* :class:`DefectClass` — the Panko-Halverson spreadsheet-error taxonomy
  (MECHANICAL / PURE_LOGIC / EUREKA / OMISSION) every finding is classified into,
  so detection can be reported *by defect class* (CLAUDE.md §3.10 evidence).
* :class:`ReviewFinding` — one defect a check raised: which check, how severe,
  which taxonomy class, a human-readable message, and a machine-actionable locator.

Why it exists / where it sits
-----------------------------
Per ``docs/research/B16-output-review-and-verification/SYNTHESIS.md`` §3, the
independent gate must catch the mechanical / pure-logic / omission classes the
deterministic floor provably reaches, and route the Eureka/semantic residue to an
advisory model layer. Classifying each finding by the Panko-Halverson taxonomy
(SYNTHESIS src 03) is what lets the ``evidence/`` showcase report a per-class
defect-detection rate (SYNTHESIS §5). Findings carry an exact ``locator`` and
``expected``/``actual`` so a send-back is machine-actionable and every verdict
explains itself (CLAUDE.md §3.11 explain-every-decision).

Security / compliance invariants upheld (CLAUDE.md §5.6)
-------------------------------------------------------
* **Fail closed on blanks:** a blank ``message`` or ``locator`` would make a defect
  un-actionable and un-auditable; both are refused at construction.
* **Closed enums, not free strings:** an unknown check id / severity / defect class
  cannot be built, so a verdict can never carry an unclassifiable defect.
* **No PII:** findings carry opaque locators and synthetic ``expected``/``actual``
  strings only — never raw artifact content (hashes-not-PII, T1).
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, field_validator

from autofirm.output_review.output_review_errors import OutputReviewError

__all__ = [
    "CheckSeverity",
    "DefectClass",
    "ReviewCheckId",
    "ReviewFinding",
]


class CheckSeverity(StrEnum):
    """How a finding affects the verdict.

    ``BLOCKING`` — a single such finding fails the verdict and blocks delivery; it
    can never be cleared by any other layer (the false-pass guard, research §6).
    ``ADVISORY`` — recorded and surfaced, but does not block (e.g. the add-only
    model layer's semantic notes). The fail-closed default is ``BLOCKING``: when a
    check is unsure whether a defect is serious, it blocks rather than waves through.
    """

    BLOCKING = "BLOCKING"
    ADVISORY = "ADVISORY"


class ReviewCheckId(StrEnum):
    """The closed set of checks the gate can run.

    A fixed enumeration (not a free string) so every finding maps to one known,
    auditable bucket and an omitted-but-mandatory check is itself detectable
    (omission defence — plan §B.3). Members map to the deterministic floor in
    ``SYNTHESIS.md`` §2.2/§3 plus the add-only ``MODEL_ADVISORY`` layer (§2.3).
    """

    ACCOUNTING_IDENTITY = "ACCOUNTING_IDENTITY"  # A = L + E exact to the unit
    SPEC_ROUND_TRIP = "SPEC_ROUND_TRIP"  # every spec value present & correct in file
    NUMERIC_RECOMPUTE = "NUMERIC_RECOMPUTE"  # recomputed == cached, exact
    FILE_OPENS_CLEAN = "FILE_OPENS_CLEAN"  # valid OOXML/PDF, no repair
    FAST_LINT = "FAST_LINT"  # orphan const / row consistency / completeness
    IBCS_SUCCESS = "IBCS_SUCCESS"  # IBCS SUCCESS rubric + message<->chart match
    VISUAL_INTEGRITY = "VISUAL_INTEGRITY"  # no misleading axes / chartjunk
    MODEL_ADVISORY = "MODEL_ADVISORY"  # add-only model layer (advisory only)


class DefectClass(StrEnum):
    """The Panko-Halverson spreadsheet-error taxonomy (SYNTHESIS src 03).

    Every finding is classified so the gate can report a defect-detection rate *per
    class* (SYNTHESIS §5). The deterministic floor must KILL the mechanical /
    pure-logic / omission classes; the Eureka (domain-logic) residue is the *only*
    class the floor provably cannot reach and the sole justification for the
    add-only advisory model layer (SYNTHESIS §3, §4).
    """

    MECHANICAL = "MECHANICAL"  # typo / wrong reference / hard-coded where formula belongs
    PURE_LOGIC = "PURE_LOGIC"  # wrong formula, right structure
    EUREKA = "EUREKA"  # wrong domain model/approach — not deterministically catchable
    OMISSION = "OMISSION"  # missing line / statement / period


class ReviewFinding(BaseModel):
    """One defect raised by one check — frozen, self-explaining, machine-actionable.

    Inputs
    ------
    * ``check_id`` — which :class:`ReviewCheckId` produced it.
    * ``severity`` — :class:`CheckSeverity`; a ``BLOCKING`` finding fails the verdict.
    * ``defect_class`` — the :class:`DefectClass` (Panko-Halverson) this defect falls in.
    * ``message`` — human-readable explanation (CLAUDE.md §3.11 explain-every-decision).
    * ``locator`` — machine-actionable pointer to the defect site (e.g. ``"Sheet1!B7"``,
      ``"slide#3"``, ``"page#2"``) so a send-back targets regeneration, not a blind retry.
    * ``expected`` / ``actual`` — the exact mismatch (e.g. ``"A=100"`` vs ``"L+E=99"``),
      optional because some defects (a corrupt file) have no numeric pair.

    Failure modes
    -------------
    Raises :class:`OutputReviewError` on a blank ``message`` or ``locator`` (a defect
    with no site or explanation is un-actionable — fail-closed, CLAUDE.md §5.6).
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    check_id: ReviewCheckId
    severity: CheckSeverity
    defect_class: DefectClass
    message: str
    locator: str
    expected: str | None = None
    actual: str | None = None

    @field_validator("message", "locator")
    @classmethod
    def _non_blank(cls, value: str) -> str:
        # fail-closed: a blank message/locator makes the defect un-actionable and
        # un-auditable — refuse it rather than emit a finding nobody can act on.
        if not value or not value.strip():
            raise OutputReviewError("ReviewFinding message and locator must be non-blank")
        return value
