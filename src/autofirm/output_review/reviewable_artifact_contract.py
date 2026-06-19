"""The handle a review check operates on: file + originating spec + recomputed values.

What this does
--------------
Defines :class:`ArtifactKind` (the closed set of deliverable kinds the gate reviews)
and :class:`ReviewableArtifact` — the frozen handle every :class:`ReviewCheck` reads
from. It carries:

* ``kind`` — what the artifact is (spreadsheet model / slide deck / document), so a
  check can decline kinds it does not apply to.
* ``path`` — where the built file lives on disk (the bytes the FILE_OPENS_CLEAN probe
  reads); together with ``kind`` it is everything that check needs.
* ``originating_spec`` — the builder spec the artifact was generated from; kept
  OPAQUE (``object``) so ``output_review`` never imports an artifacts-lane spec type
  and stays fully decoupled. The round-trip check reads the by-value
  :class:`~autofirm.output_review.reviewable_artifact_facts.SpecRoundTrip` instead.
* the five typed, by-value, frozen fact bundles the deterministic checks read —
  populated by the CALLER, never derived here — one per check family:
  ``balance_sheet`` (ACCOUNTING_IDENTITY), ``numeric_claims`` (NUMERIC_RECOMPUTE),
  ``spec_round_trip`` (SPEC_ROUND_TRIP), ``model_lint`` (FAST_LINT), and
  ``deck_facts`` (IBCS_SUCCESS + VISUAL_INTEGRITY). Each is optional (``None`` when
  the check does not apply to this ``kind``), so a check refuses fail-closed if its
  fact bundle is absent.

Why it exists / where it sits
-----------------------------
``SYNTHESIS.md`` §2.2 makes the deterministic floor a *pure function of by-value
data*. This contract is exactly that input bundle, passed by value (frozen) so a
check cannot mutate the artifact under another check (independence — plan §B.3), and
so the seven P1 checks can be built in parallel as PURE functions with no further
contract edits. It sits upstream of every check and the gate that composes them.

Security / compliance invariants upheld (CLAUDE.md §5.6, §3.12)
--------------------------------------------------------------
* **No real PII — synthetic/opaque only:** the fact bundles hold opaque, synthetic,
  string-keyed scalars / Decimals / flags, never real client data or document bytes.
  Real artifact content stays on disk behind ``path``; this handle never inlines it.
* **Decoupled:** ``originating_spec`` is opaque ``object`` — ``output_review`` imports
  no artifacts-lane type, so the contract surface is frozen against external churn.
* **Fail closed on blanks / missing file context:** a blank ``artifact_ref`` is
  refused at construction; ``path`` is a real ``Path`` (type-checked), so the
  FILE_OPENS_CLEAN probe can never be handed an empty reference.
* **Frozen & immutable:** checks receive the same handle and cannot mutate shared
  state, so the gate's composition of independent checks stays deterministic.
"""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, ConfigDict, field_validator

from autofirm.output_review.output_review_errors import OutputReviewError
from autofirm.output_review.reviewable_artifact_facts import (
    BalanceSheetFigures,
    DeckStructuralFacts,
    ModelLintFacts,
    NumericClaimSet,
    SpecRoundTrip,
)

__all__ = [
    "ArtifactKind",
    "ReviewableArtifact",
]


class ArtifactKind(StrEnum):
    """The closed set of deliverable kinds the gate reviews.

    A check inspects ``kind`` to decide whether it applies (e.g. ACCOUNTING_IDENTITY
    applies to a financial model, not a slide deck). A fixed enumeration so a check
    can never be handed an unclassifiable artifact.
    """

    FINANCIAL_MODEL = "FINANCIAL_MODEL"  # spreadsheet model (xlsx)
    SLIDE_DECK = "SLIDE_DECK"  # presentation deck (pptx)
    BUSINESS_DOCUMENT = "BUSINESS_DOCUMENT"  # narrative document (docx/pdf)


class ReviewableArtifact(BaseModel):
    """A frozen, by-value handle a deterministic check reads from.

    Inputs
    ------
    * ``artifact_ref`` — opaque, stable reference to the artifact (e.g. a content
      hash or store key) used in verdicts and audit records — never raw content.
    * ``kind`` — the :class:`ArtifactKind` (with ``path``, all FILE_OPENS_CLEAN needs).
    * ``path`` — on-disk location of the built file the FILE_OPENS_CLEAN probe reads.
    * ``originating_spec`` — the builder spec; OPAQUE ``object`` so this layer imports
      no artifacts-lane type. Optional for kinds without a spec; the round-trip check
      reads ``spec_round_trip`` (by value), never this object.
    * ``balance_sheet`` — :class:`BalanceSheetFigures` for ACCOUNTING_IDENTITY.
    * ``numeric_claims`` — :class:`NumericClaimSet` for NUMERIC_RECOMPUTE.
    * ``spec_round_trip`` — :class:`SpecRoundTrip` for SPEC_ROUND_TRIP.
    * ``model_lint`` — :class:`ModelLintFacts` for FAST_LINT.
    * ``deck_facts`` — :class:`DeckStructuralFacts` for IBCS_SUCCESS + VISUAL_INTEGRITY.
    Each fact bundle is optional (``None`` when the check does not apply to ``kind``);
    a check that needs an absent bundle refuses fail-closed in P1.

    Failure modes
    -------------
    Raises :class:`OutputReviewError` on a blank ``artifact_ref`` (an unidentifiable
    artifact cannot be audited — fail-closed, CLAUDE.md §5.6).
    """

    # arbitrary_types_allowed: ``originating_spec`` is an opaque builder spec object
    # whose concrete type lives in another lane; the contract layer never inspects it.
    model_config = ConfigDict(frozen=True, extra="forbid", arbitrary_types_allowed=True)

    artifact_ref: str
    kind: ArtifactKind
    path: Path
    originating_spec: object | None = None
    balance_sheet: BalanceSheetFigures | None = None
    numeric_claims: NumericClaimSet | None = None
    spec_round_trip: SpecRoundTrip | None = None
    model_lint: ModelLintFacts | None = None
    deck_facts: DeckStructuralFacts | None = None

    @field_validator("artifact_ref")
    @classmethod
    def _non_blank_ref(cls, value: str) -> str:
        # fail-closed: an unidentifiable artifact cannot be referenced in a verdict
        # or audit record — refuse it rather than review something we cannot name.
        if not value or not value.strip():
            raise OutputReviewError("ReviewableArtifact artifact_ref must be non-blank")
        return value
