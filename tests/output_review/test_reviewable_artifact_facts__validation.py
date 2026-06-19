"""Teeth-tests for the by-value fact sub-models the seven P1 checks read from.

Prove (CLAUDE.md §5.6, §3.11): every monetary/numeric field REJECTS ``float`` (no
drift), blanks/empties are refused fail-closed, ``Decimal`` exactness round-trips
with no precision loss, models are frozen, and construction is deterministic. Each
test asserts a failure the contract must prevent — none is tautological.
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from pydantic import ValidationError

from autofirm.output_review.output_review_errors import OutputReviewError
from autofirm.output_review.reviewable_artifact_facts import (
    BalanceSheetFigures,
    BalanceSheetPeriod,
    DeckElementFacts,
    DeckStructuralFacts,
    ModelLintFacts,
    ModelRowFormulaFacts,
    NumericClaim,
    NumericClaimSet,
    SpecRoundTrip,
)

# ---- balance-sheet figures (ACCOUNTING_IDENTITY) -------------------------------


def _period(**over: object) -> BalanceSheetPeriod:
    base: dict[str, object] = {
        "period": "FY24",
        "assets": Decimal("100"),
        "liabilities": Decimal("60"),
        "equity": Decimal("40"),
    }
    base.update(over)
    return BalanceSheetPeriod(**base)  # type: ignore[arg-type]


def test_period_constructs_and_preserves_decimals_exactly() -> None:
    p = _period(assets=Decimal("100.01"), liabilities=Decimal("60.00"), equity="40.01")
    assert p.assets == Decimal("100.01")
    assert p.equity == Decimal("40.01")  # str -> Decimal, no drift


@pytest.mark.parametrize("field", ["assets", "liabilities", "equity"])
def test_period_rejects_float_figures(field: str) -> None:
    # float would silently break exact-to-the-unit — must be refused (§3.11).
    with pytest.raises(OutputReviewError):
        _period(**{field: 100.0})


@pytest.mark.parametrize("field", ["assets", "liabilities", "equity"])
def test_period_rejects_bool_figures(field: str) -> None:
    with pytest.raises(OutputReviewError):
        _period(**{field: True})


@pytest.mark.parametrize("blank", ["", "   ", "\t"])
def test_period_rejects_blank_label(blank: str) -> None:
    with pytest.raises(OutputReviewError):
        _period(period=blank)


def test_period_accepts_negative_equity_legitimately() -> None:
    # Negative equity (accumulated losses) is a REAL balance sheet — must NOT be
    # refused; the identity check still verifies A = L + E exactly. (No overfit.)
    p = _period(assets=Decimal("10"), liabilities=Decimal("30"), equity=Decimal("-20"))
    assert p.equity == Decimal("-20")


def test_period_is_frozen() -> None:
    with pytest.raises(ValidationError):
        _period().assets = Decimal("1")


def test_balance_sheet_requires_at_least_one_period() -> None:
    with pytest.raises(OutputReviewError):
        BalanceSheetFigures(periods=())


def test_balance_sheet_rejects_duplicate_period_labels() -> None:
    with pytest.raises(OutputReviewError):
        BalanceSheetFigures(periods=(_period(), _period()))


def test_balance_sheet_constructs_multi_period() -> None:
    bs = BalanceSheetFigures(periods=(_period(period="FY23"), _period(period="FY24")))
    assert len(bs.periods) == 2


# ---- numeric claims (NUMERIC_RECOMPUTE) ----------------------------------------


def _claim(**over: object) -> NumericClaim:
    base: dict[str, object] = {
        "label": "gross_margin",
        "declared_value": Decimal("0.42"),
        "recomputed_value": Decimal("0.42"),
    }
    base.update(over)
    return NumericClaim(**base)  # type: ignore[arg-type]


def test_claim_preserves_decimal_exactly_no_float_drift() -> None:
    c = _claim(declared_value="0.1", recomputed_value=Decimal("0.1"))
    # 0.1 has NO exact float repr; the str path must give an exact Decimal.
    assert c.declared_value == Decimal("0.1")
    assert c.declared_value == c.recomputed_value


@pytest.mark.parametrize("field", ["declared_value", "recomputed_value"])
def test_claim_rejects_float(field: str) -> None:
    with pytest.raises(OutputReviewError):
        _claim(**{field: 0.1})


@pytest.mark.parametrize("blank", ["", " ", "\n"])
def test_claim_rejects_blank_label(blank: str) -> None:
    with pytest.raises(OutputReviewError):
        _claim(label=blank)


def test_claim_set_requires_at_least_one() -> None:
    with pytest.raises(OutputReviewError):
        NumericClaimSet(claims=())


def test_claim_set_rejects_duplicate_labels() -> None:
    with pytest.raises(OutputReviewError):
        NumericClaimSet(claims=(_claim(), _claim()))


# ---- spec round-trip (SPEC_ROUND_TRIP) -----------------------------------------


def test_spec_round_trip_constructs() -> None:
    rt = SpecRoundTrip(
        declared_values={"title": "Q4 Review"}, extracted_values={"title": "Q4 Review"}
    )
    assert rt.declared_values["title"] == "Q4 Review"


def test_spec_round_trip_rejects_empty_declared() -> None:
    with pytest.raises(OutputReviewError):
        SpecRoundTrip(declared_values={}, extracted_values={"a": "b"})


def test_spec_round_trip_rejects_empty_extracted() -> None:
    with pytest.raises(OutputReviewError):
        SpecRoundTrip(declared_values={"a": "b"}, extracted_values={})


def test_spec_round_trip_rejects_blank_key() -> None:
    with pytest.raises(OutputReviewError):
        SpecRoundTrip(declared_values={"  ": "b"}, extracted_values={"a": "b"})


# ---- model lint facts (FAST_LINT) ----------------------------------------------


def test_model_lint_defaults_are_clean_empty() -> None:
    m = ModelLintFacts()
    assert m.orphan_constant_cells == ()
    assert m.rows == ()
    assert m.present_line_items == frozenset()


def test_model_lint_carries_facts() -> None:
    m = ModelLintFacts(
        orphan_constant_cells=("Sheet1!C9",),
        rows=(ModelRowFormulaFacts(row_label="Revenue", formula_consistent=False),),
        present_line_items=frozenset({"Revenue"}),
        expected_line_items=frozenset({"Revenue", "COGS"}),
    )
    assert m.rows[0].formula_consistent is False
    assert "COGS" in m.expected_line_items


def test_model_lint_rejects_blank_orphan_cell() -> None:
    with pytest.raises(OutputReviewError):
        ModelLintFacts(orphan_constant_cells=("",))


def test_model_lint_rejects_blank_line_item() -> None:
    with pytest.raises(OutputReviewError):
        ModelLintFacts(present_line_items=frozenset({"  "}))


def test_row_formula_facts_rejects_blank_label() -> None:
    with pytest.raises(OutputReviewError):
        ModelRowFormulaFacts(row_label="", formula_consistent=True)


# ---- deck structural facts (IBCS_SUCCESS + VISUAL_INTEGRITY) --------------------


def _element(**over: object) -> DeckElementFacts:
    base: dict[str, object] = {"element_id": "slide#1/chart#1", "element_kind": "BAR"}
    base.update(over)
    return DeckElementFacts(**base)  # type: ignore[arg-type]


def test_deck_element_defaults_all_flags_false() -> None:
    e = _element()
    assert not any(
        (e.has_notation, e.has_units, e.has_overlap, e.has_clipping, e.axis_truncated)
    )


def test_deck_element_carries_integrity_flags() -> None:
    e = _element(axis_truncated=True, has_overlap=True)
    assert e.axis_truncated is True and e.has_overlap is True


@pytest.mark.parametrize("field", ["element_id", "element_kind"])
def test_deck_element_rejects_blank(field: str) -> None:
    with pytest.raises(OutputReviewError):
        _element(**{field: "  "})


def test_deck_requires_at_least_one_element() -> None:
    with pytest.raises(OutputReviewError):
        DeckStructuralFacts(elements=())


def test_deck_rejects_duplicate_element_ids() -> None:
    with pytest.raises(OutputReviewError):
        DeckStructuralFacts(elements=(_element(), _element()))


def test_deck_constructs_with_distinct_elements() -> None:
    deck = DeckStructuralFacts(
        elements=(
            _element(element_id="slide#1/chart#1"),
            _element(element_id="slide#2/title#1", axis_truncated=True),
        )
    )
    assert len(deck.elements) == 2
    assert deck.elements[1].axis_truncated is True


# ---- determinism ---------------------------------------------------------------


def test_construction_is_deterministic() -> None:
    a = BalanceSheetFigures(periods=(_period(),))
    b = BalanceSheetFigures(periods=(_period(),))
    assert a == b
    assert a.model_dump() == b.model_dump()


# ---- PROPERTY: Decimal exactness preserved for ANY decimal-shaped string -------


@settings(max_examples=400)
@given(
    whole=st.integers(min_value=-(10**9), max_value=10**9),
    frac=st.integers(min_value=0, max_value=999_999),
)
def test_property_decimal_string_round_trips_exactly(whole: int, frac: int) -> None:
    """Any ``<whole>.<6-digit frac>`` string becomes the EXACT same Decimal."""
    s = f"{whole}.{frac:06d}"
    expected = Decimal(s)
    # Build via the STRING path on purpose: pydantic coerces str -> Decimal, and we
    # prove that path introduces no drift. The str args are deliberate runtime input
    # (the declared field type is Decimal), hence the targeted ignores.
    c = NumericClaim(
        label="x",
        declared_value=s,  # type: ignore[arg-type]
        recomputed_value=s,  # type: ignore[arg-type]
    )
    assert c.declared_value == expected
    assert c.recomputed_value == expected
    # No drift: the value re-stringifies to the same scale a float never could.
    assert c.declared_value == c.recomputed_value


@settings(max_examples=300)
@given(bad=st.floats(allow_nan=False, allow_infinity=False))
def test_property_any_float_is_refused(bad: float) -> None:
    """No ``float`` may ever populate a money field — fail-closed for ALL floats."""
    with pytest.raises(OutputReviewError):
        NumericClaim(
            label="x",
            declared_value=bad,  # type: ignore[arg-type]
            recomputed_value=Decimal("1"),
        )
