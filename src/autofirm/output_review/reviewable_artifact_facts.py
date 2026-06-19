"""By-value, frozen fact sub-models the seven deterministic checks read from.

What this does
--------------
Defines the minimal, cohesive set of typed, frozen, BY-VALUE fact bundles the
caller populates so each P1 deterministic check is a PURE function over plain data
— never reaching back into the artifact builders or their specs. One sub-model per
check family:

* :class:`BalanceSheetPeriod` / :class:`BalanceSheetFigures` — ACCOUNTING_IDENTITY:
  per-period ``assets``/``liabilities``/``equity`` as :class:`~decimal.Decimal`, so
  the check asserts ``A == L + E`` EXACT to the unit (CLAUDE.md §3.11).
* :class:`NumericClaim` / :class:`NumericClaimSet` — NUMERIC_RECOMPUTE: each claim
  pairs a ``declared_value`` with an independently ``recomputed_value`` (both
  ``Decimal``); the check asserts exact equality.
* :class:`SpecRoundTrip` — SPEC_ROUND_TRIP: two by-value maps, ``declared_values``
  (from the spec) and ``extracted_values`` (re-read from the rendered artifact);
  the check asserts they match.
* :class:`ModelLintFacts` — FAST_LINT: structural facts of a model (orphan-constant
  cells, per-row formula-consistency facts, present/expected line-item names for the
  omission/completeness defence).
* :class:`DeckStructuralFacts` — IBCS_SUCCESS + VISUAL_INTEGRITY: per-element deck
  facts (element inventory, notation/units-present flags, overlap/clipping flags).

Why it exists / where it sits
-----------------------------
``SYNTHESIS.md`` §2.2 makes the deterministic floor a *pure function of by-value
data*. Extracting these facts into their own ≤300-line file (CLAUDE.md §5.7) keeps
:mod:`reviewable_artifact_contract` small and lets the seven P1 checks be built in
parallel as pure functions with NO further contract edits and NO cross-check file
collisions — each check imports only the fact bundle it needs.

Security / compliance invariants upheld (CLAUDE.md §5.6, §3.11, §3.12)
---------------------------------------------------------------------
* **Decimal-only money, NO float drift:** every monetary/numeric field forbids
  ``float`` at the boundary (a ``float`` cannot represent ``0.1`` exactly, so it
  would silently break exact-to-the-unit checks). ``Decimal``/``int``/clean numeric
  ``str`` are accepted and normalised to ``Decimal``; ``float`` is refused.
* **Fail closed on blanks / emptiness:** blank labels/keys/period names and empty
  required collections are refused at construction — a check can never be handed a
  fact bundle that silently means "nothing to verify".
* **Frozen & by-value:** every model is frozen with ``extra="forbid"``; checks share
  immutable data and cannot mutate each other's view (independence — plan §B.3).
* **No PII:** facts are synthetic, opaque, string-keyed scalars and flags — never
  raw artifact bytes or real client content (hashes-not-PII, T1).
"""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from autofirm.output_review.output_review_errors import OutputReviewError

__all__ = [
    "BalanceSheetFigures",
    "BalanceSheetPeriod",
    "DeckElementFacts",
    "DeckStructuralFacts",
    "ModelLintFacts",
    "ModelRowFormulaFacts",
    "NumericClaim",
    "NumericClaimSet",
    "SpecRoundTrip",
]


def _reject_float(value: object) -> object:
    """Refuse ``float`` before pydantic coerces it (the exactness guard).

    A ``float`` cannot represent most decimals exactly (e.g. ``0.1``), so accepting
    one would silently inject drift into an exact-to-the-unit check. Decimal / int /
    str are passed through for normal :class:`~decimal.Decimal` validation; a
    ``float`` (and ``bool``, which is an ``int`` subclass that has no place in a money
    field) is refused fail-closed (CLAUDE.md §3.11, §5.6).
    """
    if isinstance(value, bool | float):
        raise OutputReviewError(
            "monetary/numeric fields forbid float/bool input (exactness, §3.11); "
            "pass Decimal, int, or a numeric string"
        )
    return value


def _non_blank(value: str, *, field: str) -> str:
    """Refuse a blank label/key/name (fail-closed — an unnameable fact is useless)."""
    if not value or not value.strip():
        raise OutputReviewError(f"{field} must be non-blank")
    return value


class BalanceSheetPeriod(BaseModel):
    """One period's balance-sheet figures — the ACCOUNTING_IDENTITY check's unit.

    Inputs
    ------
    * ``period`` — opaque period label (e.g. ``"FY24"``); non-blank.
    * ``assets`` / ``liabilities`` / ``equity`` — :class:`~decimal.Decimal` figures
      the check compares as ``assets == liabilities + equity`` exact to the unit.

    Failure modes
    -------------
    Raises :class:`OutputReviewError` on a blank ``period`` or any ``float`` figure.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    period: str
    assets: Decimal
    liabilities: Decimal
    equity: Decimal

    @field_validator("assets", "liabilities", "equity", mode="before")
    @classmethod
    def _no_float_figures(cls, value: object) -> object:
        return _reject_float(value)

    @field_validator("period")
    @classmethod
    def _period_non_blank(cls, value: str) -> str:
        return _non_blank(value, field="BalanceSheetPeriod.period")


class BalanceSheetFigures(BaseModel):
    """The full set of periods the ACCOUNTING_IDENTITY check verifies.

    Inputs
    ------
    * ``periods`` — one :class:`BalanceSheetPeriod` per reporting period; at least one
      (an empty balance sheet has nothing to verify — refused fail-closed).

    Failure modes
    -------------
    Raises :class:`OutputReviewError` on an empty ``periods`` or duplicate period
    labels (an ambiguous period set could hide a defect in a shadowed period).
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    periods: tuple[BalanceSheetPeriod, ...]

    @model_validator(mode="after")
    def _non_empty_unique_periods(self) -> BalanceSheetFigures:
        if not self.periods:
            # fail-closed: an empty balance sheet means the check would vacuously
            # "pass" — refuse rather than wave through a model with nothing to verify.
            raise OutputReviewError("BalanceSheetFigures.periods must be non-empty")
        labels = [p.period for p in self.periods]
        if len(set(labels)) != len(labels):
            raise OutputReviewError("BalanceSheetFigures period labels must be unique")
        return self


class NumericClaim(BaseModel):
    """One declared-vs-recomputed numeric pair — the NUMERIC_RECOMPUTE check's unit.

    Inputs
    ------
    * ``label`` — opaque claim label (e.g. ``"gross_margin_fy24"``); non-blank.
    * ``declared_value`` — the value the artifact states (cached/written), ``Decimal``.
    * ``recomputed_value`` — the value the caller computed INDEPENDENTLY, ``Decimal``;
      the check asserts ``declared_value == recomputed_value`` exact to the unit.

    Failure modes
    -------------
    Raises :class:`OutputReviewError` on a blank ``label`` or any ``float`` value.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    label: str
    declared_value: Decimal
    recomputed_value: Decimal

    @field_validator("declared_value", "recomputed_value", mode="before")
    @classmethod
    def _no_float_values(cls, value: object) -> object:
        return _reject_float(value)

    @field_validator("label")
    @classmethod
    def _label_non_blank(cls, value: str) -> str:
        return _non_blank(value, field="NumericClaim.label")


class NumericClaimSet(BaseModel):
    """The collection of numeric claims the NUMERIC_RECOMPUTE check verifies.

    Inputs
    ------
    * ``claims`` — one :class:`NumericClaim` per recomputed figure; at least one
      (an empty set has nothing to recompute — refused fail-closed).

    Failure modes
    -------------
    Raises :class:`OutputReviewError` on an empty ``claims`` or duplicate labels.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    claims: tuple[NumericClaim, ...]

    @model_validator(mode="after")
    def _non_empty_unique_labels(self) -> NumericClaimSet:
        if not self.claims:
            raise OutputReviewError("NumericClaimSet.claims must be non-empty")
        labels = [c.label for c in self.claims]
        if len(set(labels)) != len(labels):
            raise OutputReviewError("NumericClaimSet claim labels must be unique")
        return self


class SpecRoundTrip(BaseModel):
    """Declared-vs-extracted value maps — the SPEC_ROUND_TRIP check's input.

    Inputs
    ------
    * ``declared_values`` — what the originating spec declared, by opaque key
      (string scalars, normalised by the caller — never floats, never raw bytes).
    * ``extracted_values`` — what was re-read from the rendered artifact, same keying;
      the check asserts the two maps match (every declared key present & equal).

    Failure modes
    -------------
    Raises :class:`OutputReviewError` if either map is empty (an empty spec round-trip
    is a vacuous pass — refuse it) or carries a blank key.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    declared_values: Mapping[str, str]
    extracted_values: Mapping[str, str]

    @field_validator("declared_values", "extracted_values")
    @classmethod
    def _non_empty_keys_non_blank(cls, value: Mapping[str, str]) -> Mapping[str, str]:
        if not value:
            # fail-closed: an empty map means "nothing to round-trip" — a check over
            # it would vacuously pass and let a dropped artifact slip through.
            raise OutputReviewError("SpecRoundTrip value maps must be non-empty")
        for key in value:
            _non_blank(key, field="SpecRoundTrip map key")
        return value


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
    @classmethod
    def _row_label_non_blank(cls, value: str) -> str:
        return _non_blank(value, field="ModelRowFormulaFacts.row_label")


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
    @classmethod
    def _cells_non_blank(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        for cell in value:
            _non_blank(cell, field="ModelLintFacts.orphan_constant_cells entry")
        return value

    @field_validator("present_line_items", "expected_line_items")
    @classmethod
    def _items_non_blank(cls, value: frozenset[str]) -> frozenset[str]:
        for item in value:
            _non_blank(item, field="ModelLintFacts line-item name")
        return value


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
    @classmethod
    def _ids_non_blank(cls, value: str) -> str:
        return _non_blank(value, field="DeckElementFacts id/kind")


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
