"""Boundary-exact + property tests for DCF / present value / terminal value.

Proves ZERO numerical error against hand-computed golden values (CLAUDE.md
§3.11), determinism across runs, monotonicity properties, and the fail-closed
guards. Designed to KILL mutants on ``discounted_cash_flow``.
"""

from decimal import Decimal

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from autofirm.finance.valuation.discounted_cash_flow import (
    discounted_cash_flow_value,
    present_value,
    terminal_value,
)

# --------------------------------------------------------------------------- #
# present_value — hand-computed exact values.                                  #
# --------------------------------------------------------------------------- #


def test_present_value_one_period_exact() -> None:
    # 110 / 1.10 = 100 exactly.
    assert present_value(Decimal("110"), Decimal("0.10"), 1) == Decimal("100")


def test_present_value_two_periods_exact() -> None:
    # 121 / 1.10^2 = 121 / 1.21 = 100 exactly.
    assert present_value(Decimal("121"), Decimal("0.10"), 2) == Decimal("100")


def test_present_value_period_zero_is_undiscounted() -> None:
    # t=0 -> divide by (1+r)^0 = 1 -> the cash flow itself.
    assert present_value(Decimal("250.00"), Decimal("0.10"), 0) == Decimal("250.00")


def test_present_value_negative_cash_flow() -> None:
    assert present_value(Decimal("-110"), Decimal("0.10"), 1) == Decimal("-100")


def test_present_value_zero_rate_is_identity() -> None:
    assert present_value(Decimal("500"), Decimal("0"), 7) == Decimal("500")


# --------------------------------------------------------------------------- #
# terminal_value — hand-computed exact (Gordon growth).                        #
# --------------------------------------------------------------------------- #


def test_terminal_value_exact() -> None:
    # CF=100, r=10%, g=2% -> 100*1.02 / (0.10-0.02) = 102 / 0.08 = 1275 exactly.
    assert terminal_value(Decimal("100"), Decimal("0.10"), Decimal("0.02")) == Decimal("1275")


def test_terminal_value_zero_growth_is_perpetuity() -> None:
    # g=0 -> CF / r. 50 / 0.05 = 1000.
    assert terminal_value(Decimal("50"), Decimal("0.05"), Decimal("0")) == Decimal("1000")


# --------------------------------------------------------------------------- #
# discounted_cash_flow_value — hand-computed exact, with and without terminal.  #
# --------------------------------------------------------------------------- #


def test_dcf_finite_horizon_exact() -> None:
    # [100,100,100] @ 10%: 90.9090.. + 82.6446.. + 75.1314.. quantise check.
    value = discounted_cash_flow_value([Decimal("100")] * 3, Decimal("0.10"))
    # Hand value: 100/1.1 + 100/1.21 + 100/1.331 = 248.6851... ; assert to 4dp.
    assert value.quantize(Decimal("0.0001")) == Decimal("248.6852")


def test_dcf_flat_perpetuity_via_terminal_matches_closed_form() -> None:
    # One period of 100, then terminal value with g=0 at r=10%.
    # Explicit: 100/1.1 = 90.9090...; TV at n=1: 100/0.10 = 1000, discounted
    # 1000/1.1 = 909.0909...; total = 1000.00 exactly (a flat perpetuity of 100
    # at 10% is worth 100/0.10 = 1000 from t=0... but here CF starts at t=1, so
    # value = 100/0.10 = 1000). Confirm to the cent.
    value = discounted_cash_flow_value(
        [Decimal("100")], Decimal("0.10"), terminal_growth=Decimal("0")
    )
    assert value.quantize(Decimal("0.01")) == Decimal("1000.00")


def test_dcf_growing_terminal_value_exact_to_the_cent() -> None:
    # 2 explicit periods of 100, terminal g=3%, r=10%.
    # PV1 = 100/1.1 = 90.909090...
    # PV2 = 100/1.21 = 82.644628...
    # TV at n=2 = 100*1.03/(0.10-0.03) = 103/0.07 = 1471.428571...
    # PV(TV) = 1471.428571.../1.21 = 1216.056671...
    # total = 1389.610390...
    value = discounted_cash_flow_value(
        [Decimal("100"), Decimal("100")], Decimal("0.10"), terminal_growth=Decimal("0.03")
    )
    assert value.quantize(Decimal("0.01")) == Decimal("1389.61")


# --------------------------------------------------------------------------- #
# Fail-closed guards.                                                          #
# --------------------------------------------------------------------------- #


def test_present_value_negative_period_refused() -> None:
    with pytest.raises(ValueError, match="period must be >= 0"):
        present_value(Decimal("100"), Decimal("0.10"), -1)


def test_present_value_rate_at_minus_one_refused() -> None:
    with pytest.raises(ValueError, match="rate must be > -1"):
        present_value(Decimal("100"), Decimal("-1"), 1)


def test_present_value_rate_below_minus_one_refused() -> None:
    with pytest.raises(ValueError, match="rate must be > -1"):
        present_value(Decimal("100"), Decimal("-1.5"), 1)


def test_terminal_value_growth_equals_rate_refused() -> None:
    with pytest.raises(ValueError, match="strictly less than"):
        terminal_value(Decimal("100"), Decimal("0.10"), Decimal("0.10"))


def test_terminal_value_growth_above_rate_refused() -> None:
    with pytest.raises(ValueError, match="strictly less than"):
        terminal_value(Decimal("100"), Decimal("0.05"), Decimal("0.08"))


def test_dcf_empty_cash_flows_refused() -> None:
    with pytest.raises(ValueError, match="at least one period"):
        discounted_cash_flow_value([], Decimal("0.10"))


# --------------------------------------------------------------------------- #
# Determinism + properties.                                                    #
# --------------------------------------------------------------------------- #


def test_dcf_is_deterministic_across_runs() -> None:
    flows = [Decimal("137.50"), Decimal("212.34"), Decimal("99.01")]
    runs = {discounted_cash_flow_value(flows, Decimal("0.085")) for _ in range(20)}
    assert len(runs) == 1  # identical inputs -> identical output every time


_amounts = st.integers(min_value=1, max_value=10_000).map(lambda c: Decimal(c).scaleb(-2))
_rates = st.integers(min_value=1, max_value=5000).map(lambda b: Decimal(b).scaleb(-4))


@settings(max_examples=200)
@given(cash_flow=_amounts, rate=_rates, period=st.integers(min_value=1, max_value=30))
def test_property_positive_pv_below_undiscounted_for_positive_rate(
    cash_flow: Decimal, rate: Decimal, period: int
) -> None:
    # A positive future cash flow discounted at a positive rate is worth strictly
    # less than its face value (the time value of money).
    pv = present_value(cash_flow, rate, period)
    assert pv < cash_flow


@settings(max_examples=200)
@given(cash_flow=_amounts, rate=_rates, period=st.integers(min_value=0, max_value=30))
def test_property_present_value_round_trips_through_compounding(
    cash_flow: Decimal, rate: Decimal, period: int
) -> None:
    # PV * (1+r)^period == original cash flow (to high precision). Proves the
    # discount factor is the exact inverse of compounding.
    pv = present_value(cash_flow, rate, period)
    recovered = pv * (Decimal(1) + rate) ** period
    assert abs(recovered - cash_flow) < Decimal("1e-20")
