"""Model-lint fact bundles for the FAST_LINT check.

What this does
--------------
Frozen, by-value structural facts of a financial model the FAST_LINT check reads:
orphan-constant cells, per-row formula-consistency facts, and present/expected
line-item names for the omission/completeness defence.

Why it exists / where it sits
-----------------------------
One slice of the per-family split of the by-value fact surface (CLAUDE.md §5.7);
re-exported through :mod:`reviewable_artifact_facts` as the single stable import
point so importers are unchanged.

Security / compliance invariants upheld (CLAUDE.md §5.6, §3.11)
--------------------------------------------------------------
* **Fail closed on blanks:** blank row labels, cell locators, and line-item names
  are refused at construction via :func:`require_non_blank`.
* **Frozen & by-value:** ``frozen=True``/``extra="forbid"`` — checks share immutable
  data and cannot mutate each other's view.
* **No PII:** opaque string locators and names only — never raw model bytes.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, field_validator

from autofirm.output_review.fact_value_guards import require_non_blank

__all__ = [
    "ModelLintFacts",
    "ModelRowFormulaFacts",
]


class ModelRowFormulaFacts(BaseModel):
    """Per-row formula-consistency facts for one spreadsheet row — FAST_LINT input.

    Inputs
    ------
    * ``row_label`` — opaque row name/reference (e.g. ``"Revenue"`` / ``"row#7"``).
    * ``formula_consistent`` — ``True`` iff every cell in the row shares the row's
      structural formula (FAST/ICAEW row-consistency; an inconsistent row is a defect).

    Failure modes
    -------------
    Raises :class:`OutputReviewError` on a blank ``row_label``.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    row_label: str
    formula_consistent: bool

    @field_validator("row_label")
    # @classmethod removal is equivalent: pydantic v2 auto-wraps a @field_validator
    # as a classmethod, so dropping the explicit decorator is behaviourally identical.
    @classmethod  # pragma: no mutate
    def _row_label_non_blank(cls, value: str) -> str:
        return require_non_blank(value, field="ModelRowFormulaFacts.row_label")


class ModelLintFacts(BaseModel):
    """Structural facts of a financial model — the FAST_LINT check's input.

    Inputs
    ------
    * ``orphan_constant_cells`` — cell locators holding a hard-coded constant where a
      formula belongs (Panko-Halverson MECHANICAL; non-empty == defect).
    * ``rows`` — per-row :class:`ModelRowFormulaFacts` (row-consistency defence).
    * ``present_line_items`` — line-item names actually present in the model.
    * ``expected_line_items`` — line-item names the standard requires; any expected
      name absent from ``present_line_items`` is an OMISSION defect (completeness).

    Failure modes
    -------------
    Raises :class:`OutputReviewError` on a blank cell locator or line-item name.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    orphan_constant_cells: tuple[str, ...] = ()
    rows: tuple[ModelRowFormulaFacts, ...] = ()
    present_line_items: frozenset[str] = frozenset()
    expected_line_items: frozenset[str] = frozenset()

    @field_validator("orphan_constant_cells")
    # @classmethod removal is equivalent: pydantic v2 auto-wraps a @field_validator
    # as a classmethod, so dropping the explicit decorator is behaviourally identical.
    @classmethod  # pragma: no mutate
    def _cells_non_blank(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        for cell in value:
            require_non_blank(cell, field="ModelLintFacts.orphan_constant_cells entry")
        return value

    @field_validator("present_line_items", "expected_line_items")
    # @classmethod removal is equivalent: pydantic v2 auto-wraps a @field_validator
    # as a classmethod, so dropping the explicit decorator is behaviourally identical.
    @classmethod  # pragma: no mutate
    def _items_non_blank(cls, value: frozenset[str]) -> frozenset[str]:
        for item in value:
            require_non_blank(item, field="ModelLintFacts line-item name")
        return value
