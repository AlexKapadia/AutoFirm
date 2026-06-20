"""Deck-structural fact bundles for the IBCS_SUCCESS + VISUAL_INTEGRITY checks.

What this does
--------------
Frozen, by-value structural facts of a deck the IBCS/VISUAL_INTEGRITY checks read:
per-element inventory, notation/units-present flags, and overlap/clipping/axis
flags.

Why it exists / where it sits
-----------------------------
One slice of the per-family split of the by-value fact surface (CLAUDE.md §5.7);
re-exported through :mod:`reviewable_artifact_facts` as the single stable import
point so importers are unchanged.

Security / compliance invariants upheld (CLAUDE.md §5.6, §3.11)
--------------------------------------------------------------
* **Fail closed on blanks / emptiness:** blank element ids/kinds and empty/duplicate
  element sets are refused at construction via :func:`require_non_blank`.
* **Frozen & by-value:** ``frozen=True``/``extra="forbid"`` — checks share immutable
  data and cannot mutate each other's view.
* **No PII:** opaque string locators and flags only — never raw deck bytes.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from autofirm.output_review.fact_value_guards import require_non_blank
from autofirm.output_review.output_review_errors import OutputReviewError

__all__ = [
    "DeckElementFacts",
    "DeckStructuralFacts",
]


class DeckElementFacts(BaseModel):
    """Structural facts of one deck element — the IBCS/VISUAL_INTEGRITY checks' unit.

    Inputs
    ------
    * ``element_id`` — opaque element/slide locator (e.g. ``"slide#3/chart#1"``).
    * ``element_kind`` — opaque element-kind label (e.g. ``"BAR_CHART"`` / ``"TITLE"``);
      kept a free string so the deck checks stay general across notations (no overfit).
    * ``has_notation`` — ``True`` iff IBCS notation is present where required.
    * ``has_units`` — ``True`` iff axis/value units are labelled.
    * ``has_overlap`` — ``True`` iff this element overlaps another (a layout defect).
    * ``has_clipping`` — ``True`` iff content is clipped/truncated (a layout defect).
    * ``axis_truncated`` — ``True`` iff a value axis does not start at zero / is
      misleadingly truncated (IBCS visual-integrity defect).

    Failure modes
    -------------
    Raises :class:`OutputReviewError` on a blank ``element_id`` or ``element_kind``.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    element_id: str
    element_kind: str
    has_notation: bool = False
    has_units: bool = False
    has_overlap: bool = False
    has_clipping: bool = False
    axis_truncated: bool = False

    @field_validator("element_id", "element_kind")
    # @classmethod removal is equivalent: pydantic v2 auto-wraps a @field_validator
    # as a classmethod, so dropping the explicit decorator is behaviourally identical.
    @classmethod  # pragma: no mutate
    def _ids_non_blank(cls, value: str) -> str:
        return require_non_blank(value, field="DeckElementFacts id/kind")


class DeckStructuralFacts(BaseModel):
    """The deck-wide structural inventory the IBCS/VISUAL_INTEGRITY checks verify.

    Inputs
    ------
    * ``elements`` — one :class:`DeckElementFacts` per slide element; at least one
      (an empty deck has nothing to verify — refused fail-closed).

    Failure modes
    -------------
    Raises :class:`OutputReviewError` on an empty ``elements`` or duplicate element ids.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    elements: tuple[DeckElementFacts, ...]

    @model_validator(mode="after")
    def _non_empty_unique_ids(self) -> DeckStructuralFacts:
        if not self.elements:
            raise OutputReviewError("DeckStructuralFacts.elements must be non-empty")
        ids = [e.element_id for e in self.elements]
        if len(set(ids)) != len(ids):
            raise OutputReviewError("DeckStructuralFacts element ids must be unique")
        return self
