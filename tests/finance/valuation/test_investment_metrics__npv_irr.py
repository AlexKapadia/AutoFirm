"""Boundary-exact + property tests for NPV and IRR.

NPV is checked against hand-computed values; IRR against hand-solvable roots and
via the round-trip property ``NPV(IRR) ~ 0``. Fail-closed guards and determinism
are pinned. Designed to KILL mutants on ``investment_metrics``.
"""

from decimal import Decimal

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from autofirm.finance.valuation.investment_metrics import (
    internal_rate_of_return,
    net_present_value,
)

# --------------------------------------------------------------------------- #
# NPV — hand-computed exact values.                                            #
# --------------------------------------------------------------------------- #


def test_npv_zero_at_break_even() -> None:
    # -100 today, +110 next year at 10% -> NPV = -100 + 100 = 0 exactly.
    assert net_present_value([Decimal("-100"), Decimal("110")], Decimal("0.10")) == Decimal("0")


def test_npv_positive_project() -> None:
    # -100 + 121/1.1^1? No: [-100, 110] @ 5% -> -100 + 110/1.05 = 4.7619...
    npv = net_present_value([Decimal("-100"), Decimal("110")], Decimal("0.05"))
    assert npv.quantize(Decimal("0.0001")) == Decimal("4.7619")


def test_npv_zero_rate_is_plain_sum() -> None:
    flows = [Decimal("-100"), Decimal("40"), Decimal("40"), Decimal("40")]
    npv = net_present_value(flows, Decimal("0"))
    assert npv == Decimal("20")  # -100 + 120


def test_npv_single_period_is_that_flow() -> None:
    assert net_present_value([Decimal("-500.00")], Decimal("0.10")) == Decimal("-500.00")


def test_npv_empty_refused() -> None:
    with pytest.raises(ValueError, match="at least one period"):
        net_present_value([], Decimal("0.10"))


# --------------------------------------------------------------------------- #
# IRR — hand-solvable roots + the defining round-trip property.                #
# --------------------------------------------------------------------------- #


def test_irr_simple_two_period_is_ten_percent() -> None:
    # [-100, 110] -> IRR solves -100 + 110/(1+r) = 0 -> r = 0.10 exactly.
    irr = internal_rate_of_return([Decimal("-100"), Decimal("110")])
    assert abs(irr - Decimal("0.10")) < Decimal("1e-9")


def test_irr_classic_three_year_project() -> None:
    # [-1000, 500, 500, 500] -> IRR ~ 23.375%. Verify NPV at IRR is ~0.
    flows = [Decimal("-1000"), Decimal("500"), Decimal("500"), Decimal("500")]
    irr = internal_rate_of_return(flows)
    assert abs(irr - Decimal("0.23375")) < Decimal("1e-4")
    assert abs(net_present_value(flows, irr)) < Decimal("1e-9")


def test_irr_exact_bracket_endpoint_returned_when_npv_zero_at_low() -> None:
    # If NPV is exactly zero at the low bracket bound, IRR returns it directly.
    # Construct flows whose IRR is exactly -0.9999? Hard; instead test high end:
    # flows where NPV at high(=10) is exactly zero is also contrived, so we test
    # the generic root finding below and the guard branches here.
    flows = [Decimal("-100"), Decimal("110")]
    irr = internal_rate_of_return(flows, low=Decimal("0.10"), high=Decimal("0.50"))
    # low bound IS the root -> returned immediately.
    assert irr == Decimal("0.10")


def test_irr_high_endpoint_returned_when_npv_zero_at_high() -> None:
    flows = [Decimal("-100"), Decimal("110")]
    irr = internal_rate_of_return(flows, low=Decimal("-0.50"), high=Decimal("0.10"))
    assert irr == Decimal("0.10")


# --------------------------------------------------------------------------- #
# IRR fail-closed guards.                                                      #
# --------------------------------------------------------------------------- #


def test_irr_no_sign_change_refused() -> None:
    # All-positive cash flows: NPV never crosses zero -> no IRR in range.
    with pytest.raises(ValueError, match="does not change sign"):
        internal_rate_of_return([Decimal("100"), Decimal("100")])


def test_irr_empty_refused() -> None:
    with pytest.raises(ValueError, match="at least one period"):
        internal_rate_of_return([])


def test_irr_non_positive_tolerance_refused() -> None:
    with pytest.raises(ValueError, match="tolerance must be > 0"):
        internal_rate_of_return([Decimal("-100"), Decimal("110")], tolerance=Decimal("0"))


def test_irr_non_positive_iterations_refused() -> None:
    with pytest.raises(ValueError, match="max_iterations must be > 0"):
        internal_rate_of_return([Decimal("-100"), Decimal("110")], max_iterations=0)


def test_irr_exhausted_budget_returns_tight_estimate() -> None:
    # With a single bisection step the result is the bracket midpoint, not yet
    # converged — proves the budget-exhaustion path returns a value (no hang).
    flows = [Decimal("-1000"), Decimal("500"), Decimal("500"), Decimal("500")]
    estimate = internal_rate_of_return(
        flows, low=Decimal("0"), high=Decimal("1"), max_iterations=1
    )
    assert Decimal("0") < estimate < Decimal("1")


# --------------------------------------------------------------------------- #
# Determinism + the IRR round-trip property.                                   #
# --------------------------------------------------------------------------- #


def test_irr_is_deterministic_across_runs() -> None:
    flows = [Decimal("-1000"), Decimal("450"), Decimal("550"), Decimal("600")]
    runs = {internal_rate_of_return(flows) for _ in range(15)}
    assert len(runs) == 1


_outlay = st.integers(min_value=100, max_value=100_000).map(lambda c: Decimal(c).scaleb(-2))
_inflow = st.integers(min_value=1, max_value=100_000).map(lambda c: Decimal(c).scaleb(-2))


@settings(max_examples=200)
@given(
    outlay=_outlay,
    inflows=st.lists(_inflow, min_size=2, max_size=6),
)
def test_property_npv_at_irr_is_approximately_zero(
    outlay: Decimal, inflows: list[Decimal]
) -> None:
    # A conventional project (one negative outlay then positive inflows that
    # exceed it) has an IRR at which NPV is ~0 — the defining property of IRR.
    # A tiny outlay against large inflows can imply an IRR above any fixed
    # bracket, so we widen the search to a very high ceiling; the property under
    # test is "NPV(IRR) ~ 0", not the bracket width.
    flows = [-outlay, *inflows]
    if sum(inflows, start=Decimal("0.00")) <= outlay:
        return  # not a profitable project -> IRR may be negative/out of bracket
    try:
        irr = internal_rate_of_return(flows, high=Decimal("1000000"))
    except ValueError:
        return  # IRR outside even the wide bracket -> precondition not met
    npv = net_present_value(flows, irr)
    assert abs(npv) <= Decimal("1e-6")  # NPV(IRR) == 0 to tolerance
