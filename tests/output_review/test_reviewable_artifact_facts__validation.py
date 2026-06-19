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


def test_balance_sheet_figures_is_frozen() -> None:
    # The OUTER aggregate must be immutable too: a check shares this bundle and must
    # not be able to swap the period set under another check (frozen=True; killing the
    # frozen->False and the whole model_config->None mutants on the aggregate config).
    bs = BalanceSheetFigures(periods=(_period(),))
    with pytest.raises(ValidationError):
        bs.periods = ()  # type: ignore[misc]


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


def test_claim_is_frozen() -> None:
    # The claim unit a check reads must be immutable (frozen=True): kills the
    # frozen->False and model_config->None mutants on NumericClaim's config.
    with pytest.raises(ValidationError):
        _claim().declared_value = Decimal("1")


def test_claim_set_is_frozen() -> None:
    # The outer claim set must be immutable too: kills the frozen->False and
    # model_config->None mutants on NumericClaimSet's config.
    cs = NumericClaimSet(claims=(_claim(),))
    with pytest.raises(ValidationError):
        cs.claims = ()  # type: ignore[misc]


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


def test_spec_round_trip_is_frozen() -> None:
    # The round-trip bundle a check reads must be immutable (frozen=True): kills the
    # frozen->False and model_config->None mutants on SpecRoundTrip's config.
    rt = SpecRoundTrip(declared_values={"k": "v"}, extracted_values={"k": "v"})
    with pytest.raises(ValidationError):
        rt.declared_values = {"k": "x"}  # type: ignore[misc]


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


# =================================================================================
# EXACT-MESSAGE PINS (mutmut wraps string literals in XX..XX, so a substring check
# would NOT kill the mutant — every message below is asserted with FULL ``==``).
# =================================================================================

# The single shared float/bool refusal message (fact_value_guards.reject_float_input).
_FLOAT_MSG = (
    "monetary/numeric fields forbid float/bool input (exactness, §3.11); "
    "pass Decimal, int, or a numeric string"
)


# ---- fact_value_guards.reject_float_input — exact message on EVERY money field ---


@pytest.mark.parametrize("field", ["assets", "liabilities", "equity"])
def test_period_float_message_is_exact(field: str) -> None:
    with pytest.raises(OutputReviewError) as excinfo:
        _period(**{field: 0.1})
    assert str(excinfo.value) == _FLOAT_MSG


@pytest.mark.parametrize("field", ["assets", "liabilities", "equity"])
def test_period_bool_message_is_exact(field: str) -> None:
    # bool is an int subclass — refused with the SAME exact message.
    with pytest.raises(OutputReviewError) as excinfo:
        _period(**{field: True})
    assert str(excinfo.value) == _FLOAT_MSG


@pytest.mark.parametrize("field", ["declared_value", "recomputed_value"])
def test_claim_float_message_is_exact(field: str) -> None:
    with pytest.raises(OutputReviewError) as excinfo:
        _claim(**{field: 0.1})
    assert str(excinfo.value) == _FLOAT_MSG


@pytest.mark.parametrize("field", ["declared_value", "recomputed_value"])
def test_claim_bool_message_is_exact(field: str) -> None:
    with pytest.raises(OutputReviewError) as excinfo:
        _claim(**{field: False})
    assert str(excinfo.value) == _FLOAT_MSG


# ---- require_non_blank — exact "{field} must be non-blank" per call site ---------


def test_period_blank_label_message_is_exact() -> None:
    with pytest.raises(OutputReviewError) as excinfo:
        _period(period="   ")
    assert str(excinfo.value) == "BalanceSheetPeriod.period must be non-blank"


def test_claim_blank_label_message_is_exact() -> None:
    with pytest.raises(OutputReviewError) as excinfo:
        _claim(label="\t")
    assert str(excinfo.value) == "NumericClaim.label must be non-blank"


def test_row_formula_blank_label_message_is_exact() -> None:
    with pytest.raises(OutputReviewError) as excinfo:
        ModelRowFormulaFacts(row_label="  ", formula_consistent=True)
    assert str(excinfo.value) == "ModelRowFormulaFacts.row_label must be non-blank"


def test_orphan_cell_blank_message_is_exact() -> None:
    with pytest.raises(OutputReviewError) as excinfo:
        ModelLintFacts(orphan_constant_cells=("",))
    assert (
        str(excinfo.value)
        == "ModelLintFacts.orphan_constant_cells entry must be non-blank"
    )


def test_present_line_item_blank_message_is_exact() -> None:
    with pytest.raises(OutputReviewError) as excinfo:
        ModelLintFacts(present_line_items=frozenset({"  "}))
    assert str(excinfo.value) == "ModelLintFacts line-item name must be non-blank"


def test_expected_line_item_blank_message_is_exact() -> None:
    # The SAME validator guards expected_line_items — pin it from that field too.
    with pytest.raises(OutputReviewError) as excinfo:
        ModelLintFacts(expected_line_items=frozenset({"\n"}))
    assert str(excinfo.value) == "ModelLintFacts line-item name must be non-blank"


@pytest.mark.parametrize("field", ["element_id", "element_kind"])
def test_deck_element_blank_message_is_exact(field: str) -> None:
    with pytest.raises(OutputReviewError) as excinfo:
        _element(**{field: "   "})
    assert str(excinfo.value) == "DeckElementFacts id/kind must be non-blank"


def test_spec_round_trip_blank_key_message_is_exact() -> None:
    with pytest.raises(OutputReviewError) as excinfo:
        SpecRoundTrip(declared_values={"  ": "b"}, extracted_values={"a": "b"})
    assert str(excinfo.value) == "SpecRoundTrip map key must be non-blank"


# ---- non-empty / uniqueness model-validator messages — exact ``==`` --------------


def test_balance_sheet_empty_message_is_exact() -> None:
    with pytest.raises(OutputReviewError) as excinfo:
        BalanceSheetFigures(periods=())
    assert str(excinfo.value) == "BalanceSheetFigures.periods must be non-empty"


def test_balance_sheet_duplicate_message_is_exact() -> None:
    with pytest.raises(OutputReviewError) as excinfo:
        BalanceSheetFigures(periods=(_period(period="FY24"), _period(period="FY24")))
    assert str(excinfo.value) == "BalanceSheetFigures period labels must be unique"


def test_claim_set_empty_message_is_exact() -> None:
    with pytest.raises(OutputReviewError) as excinfo:
        NumericClaimSet(claims=())
    assert str(excinfo.value) == "NumericClaimSet.claims must be non-empty"


def test_claim_set_duplicate_message_is_exact() -> None:
    with pytest.raises(OutputReviewError) as excinfo:
        NumericClaimSet(claims=(_claim(label="m"), _claim(label="m")))
    assert str(excinfo.value) == "NumericClaimSet claim labels must be unique"


def test_deck_empty_message_is_exact() -> None:
    with pytest.raises(OutputReviewError) as excinfo:
        DeckStructuralFacts(elements=())
    assert str(excinfo.value) == "DeckStructuralFacts.elements must be non-empty"


def test_deck_duplicate_message_is_exact() -> None:
    with pytest.raises(OutputReviewError) as excinfo:
        DeckStructuralFacts(
            elements=(_element(element_id="dup"), _element(element_id="dup"))
        )
    assert str(excinfo.value) == "DeckStructuralFacts element ids must be unique"


def test_spec_round_trip_empty_declared_message_is_exact() -> None:
    with pytest.raises(OutputReviewError) as excinfo:
        SpecRoundTrip(declared_values={}, extracted_values={"a": "b"})
    assert str(excinfo.value) == "SpecRoundTrip value maps must be non-empty"


def test_spec_round_trip_empty_extracted_message_is_exact() -> None:
    with pytest.raises(OutputReviewError) as excinfo:
        SpecRoundTrip(declared_values={"a": "b"}, extracted_values={})
    assert str(excinfo.value) == "SpecRoundTrip value maps must be non-empty"


# =================================================================================
# DEFAULT-VALUE MUTANTS — mutmut flips ``()``/``frozenset()`` defaults to ``None``.
# Omit each optional field and pin BOTH the value and its concrete empty type.
# =================================================================================


def test_model_lint_orphan_cells_default_is_empty_tuple() -> None:
    m = ModelLintFacts()
    assert m.orphan_constant_cells == ()
    assert isinstance(m.orphan_constant_cells, tuple)


def test_model_lint_rows_default_is_empty_tuple() -> None:
    m = ModelLintFacts()
    assert m.rows == ()
    assert isinstance(m.rows, tuple)


def test_model_lint_present_items_default_is_empty_frozenset() -> None:
    m = ModelLintFacts()
    assert m.present_line_items == frozenset()
    assert isinstance(m.present_line_items, frozenset)


def test_model_lint_expected_items_default_is_empty_frozenset() -> None:
    m = ModelLintFacts()
    assert m.expected_line_items == frozenset()
    assert isinstance(m.expected_line_items, frozenset)


# ---- per-element bool flag defaults (deck) — each pinned INDIVIDUALLY -------------


def test_deck_element_has_notation_defaults_false() -> None:
    assert _element().has_notation is False


def test_deck_element_has_units_defaults_false() -> None:
    assert _element().has_units is False


def test_deck_element_has_overlap_defaults_false() -> None:
    assert _element().has_overlap is False


def test_deck_element_has_clipping_defaults_false() -> None:
    assert _element().has_clipping is False


def test_deck_element_axis_truncated_defaults_false() -> None:
    assert _element().axis_truncated is False


# =================================================================================
# BOUNDARY — on / just-over / just-under for every non-empty + uniqueness gate.
# A 1-element collection is ACCEPTED (just-over empty); two DISTINCT accepted;
# two IDENTICAL refused. Proves the validator is not a no-op and not over-strict.
# =================================================================================


def test_balance_sheet_one_period_accepted_boundary() -> None:
    bs = BalanceSheetFigures(periods=(_period(period="FY24"),))
    assert len(bs.periods) == 1


def test_balance_sheet_two_distinct_accepted_boundary() -> None:
    bs = BalanceSheetFigures(periods=(_period(period="FY23"), _period(period="FY24")))
    assert len(bs.periods) == 2


def test_claim_set_one_claim_accepted_boundary() -> None:
    cs = NumericClaimSet(claims=(_claim(label="only"),))
    assert len(cs.claims) == 1


def test_claim_set_two_distinct_accepted_boundary() -> None:
    cs = NumericClaimSet(claims=(_claim(label="a"), _claim(label="b")))
    assert len(cs.claims) == 2


def test_deck_one_element_accepted_boundary() -> None:
    deck = DeckStructuralFacts(elements=(_element(element_id="only#1"),))
    assert len(deck.elements) == 1


def test_spec_round_trip_single_key_accepted_boundary() -> None:
    rt = SpecRoundTrip(declared_values={"k": "v"}, extracted_values={"k": "v"})
    assert rt.declared_values["k"] == "v"


# ---- int/Decimal/str ACCEPTED on money fields (just-under the float boundary) -----


def test_money_fields_accept_int_and_decimal_and_str() -> None:
    # reject_float_input must pass int/Decimal/str through untouched — proving it
    # rejects ONLY float/bool, not all numerics (no over-strict mutant survives).
    p = _period(assets=7, liabilities=Decimal("3"), equity="4")
    assert p.assets == Decimal("7")
    assert p.liabilities == Decimal("3")
    assert p.equity == Decimal("4")
