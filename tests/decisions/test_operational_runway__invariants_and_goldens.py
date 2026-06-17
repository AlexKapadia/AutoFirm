"""Adversarial + property tests for the operational cash-runway scenario model.

Key invariants proven (argued from properties, never fitted to one example):
* The compounding cash projection is EXACT and deterministic (§3.11); worked
  golden examples (including a compounding-revenue case) are exact to the cent.
* The runway (whole months to cash-negative) is correct on worked examples and
  is capped at, never exceeds, the horizon.
* MONOTONICITY: higher fixed cost never increases runway; higher starting cash /
  revenue never decreases it; faster growth never decreases it.
* Impossible inputs (negative balances, non-positive horizon, growth <= -1) fail
  closed (§5.6); the horizon hard-bounds the loop.
* why == what: the funding verdict is a pure function of runway vs. the policy
  floor and its drivers cannot contradict it.
Designed to KILL mutants on ``operational_runway_scenario_model``.
"""

from decimal import Decimal
from typing import TypedDict

import pytest
from hypothesis import given
from hypothesis import strategies as st

from autofirm.decisions.operational_runway_scenario_model import (
    OperationalRunwayInputs,
    OperationalRunwayScenarioModel,
)

_MODEL = OperationalRunwayScenarioModel(model_id="rw", role_id="ops-analyst")

# Strategies over the valid domain (synthetic only -- no PII, §3.12). Bounded so
# the projection stays fast and the arithmetic stays exact.
_nonneg_money = st.decimals(
    min_value=Decimal("0"), max_value=Decimal("1000000"), allow_nan=False, allow_infinity=False
)
_growth = st.decimals(
    min_value=Decimal("-0.9"), max_value=Decimal("1"), allow_nan=False, allow_infinity=False
)
_horizon = st.integers(min_value=1, max_value=36)


def _inputs(
    cash: str,
    revenue: str,
    fixed: str,
    *,
    growth: str = "0",
    horizon: int = 60,
) -> OperationalRunwayInputs:
    # min_runway_months is left at the model default (6) for the worked goldens.
    return OperationalRunwayInputs(
        starting_cash=Decimal(cash),
        monthly_revenue=Decimal(revenue),
        monthly_fixed_cost=Decimal(fixed),
        growth_rate=Decimal(growth),
        horizon_months=horizon,
    )


# -- worked golden examples: EXACT, zero numerical error --


def test_golden_flat_burn_runway_is_exact() -> None:
    # cash=1000, revenue=0, fixed=100, no growth. Each month cash -= 100.
    # Month-end cash: 900, 800, ... 0 (month 10 ends at 0, still >= 0 so counted),
    # month 11 ends at -100 -> break. Runway = 10 months; ending cash = 0.
    out = _MODEL.compute(_inputs("1000", "0", "100", growth="0", horizon=60))
    assert out.metrics.get("runway_months") == Decimal("10")
    assert out.metrics.get("ending_cash") == Decimal("0")
    assert out.recommendation.action == "monitor_runway"  # 10 >= floor 6


def test_golden_exact_zero_month_end_is_counted() -> None:
    # cash=100, revenue=0, fixed=100: month 1 ends at exactly 0 -> counted (>= 0),
    # month 2 ends at -100 -> break. Runway = 1. Proves the boundary uses < 0 (not <= 0).
    out = _MODEL.compute(_inputs("100", "0", "100", horizon=60))
    assert out.metrics.get("runway_months") == Decimal("1")
    assert out.metrics.get("ending_cash") == Decimal("0")
    assert out.recommendation.action == "raise_capital_now"  # 1 < floor 6


def test_golden_compounding_revenue_reaches_breakeven_is_exact() -> None:
    # cash=0, revenue=100, fixed=110, growth=0.1/mo.
    # m1: 0 + 100 - 110 = -10 < 0 -> break immediately. Runway = 0, ending cash = 0.
    out = _MODEL.compute(_inputs("0", "100", "110", growth="0.1", horizon=24))
    assert out.metrics.get("runway_months") == Decimal("0")
    assert out.metrics.get("ending_cash") == Decimal("0")


def test_golden_compounding_revenue_accumulates_exactly() -> None:
    # cash=50, revenue=100, fixed=120, growth=0.5/mo. Hand-computed compounding:
    # m1: cash=50 + 100 - 120 = 30 (>=0, counted). revenue -> 150
    # m2: 30 + 150 - 120 = 60. revenue -> 225
    # m3: 60 + 225 - 120 = 165. revenue -> 337.5
    # horizon=3 -> survives all 3 months. Runway = 3 (capped at horizon),
    # ending cash = 165 exactly, survives_horizon True.
    out = _MODEL.compute(_inputs("50", "100", "120", growth="0.5", horizon=3))
    assert out.metrics.get("runway_months") == Decimal("3")
    assert out.metrics.get("ending_cash") == Decimal("165")
    assert out.metrics.get("horizon_months") == Decimal("3")
    assert out.recommendation.action == "operations_self_sustaining"


def test_revenue_compounds_not_linear() -> None:
    # Distinguish geometric compounding from a linear ramp. cash big enough to
    # survive; growth 1.0 (doubling). revenue sequence 10,20,40 -> month-3 inflow 40.
    # cash=1000, fixed=0: ending = 1000 + 10 + 20 + 40 = 1070 after 3 months.
    out = _MODEL.compute(_inputs("1000", "10", "0", growth="1", horizon=3))
    assert out.metrics.get("ending_cash") == Decimal("1070")  # 10+20+40, not 10+20+30


# -- horizon cap & survival flag --


def test_runway_capped_at_horizon() -> None:
    # Hugely cash-positive: survives every month. Runway == horizon (the cap).
    out = _MODEL.compute(_inputs("1000000", "1000", "0", horizon=12))
    assert out.metrics.get("runway_months") == Decimal("12")
    assert out.recommendation.action == "operations_self_sustaining"


def test_survives_horizon_boundary_off_by_one() -> None:
    # Exactly funds 5 months then would go negative on month 6; horizon=5 -> the
    # model reports survival (runway >= horizon). Kills a >/>= off-by-one on the cap.
    # cash=500, revenue=0, fixed=100: months end 400,300,200,100,0 (5 counted),
    # horizon=5 -> runway 5 == horizon -> survives_horizon.
    out = _MODEL.compute(_inputs("500", "0", "100", horizon=5))
    assert out.metrics.get("runway_months") == Decimal("5")
    assert out.recommendation.action == "operations_self_sustaining"


# -- verdict thresholds: on / just-over / just-under the policy floor --


def test_runway_exactly_on_policy_floor_is_monitor() -> None:
    # runway == min_runway (6): does NOT survive horizon but is at the floor.
    # cash=600 fixed=100 revenue=0 horizon=60: 6 months funded, month 7 negative.
    out = _MODEL.compute(_inputs("600", "0", "100", horizon=60))
    assert out.metrics.get("runway_months") == Decimal("6")
    assert out.recommendation.action == "monitor_runway"  # >= floor, not surviving


def test_runway_just_under_floor_raises_capital() -> None:
    # runway == 5 < floor 6.
    out = _MODEL.compute(_inputs("500", "0", "100", horizon=60))
    assert out.metrics.get("runway_months") == Decimal("5")
    assert out.recommendation.action == "raise_capital_now"


# -- MONOTONICITY invariants (load-bearing) --
#
# A single ``_scenario`` strategy draws a full valid input bundle; ``_runway_with``
# recomputes the runway with one field overridden. Each property then varies just
# that one field via a sorted pair, keeping signatures small and the invariant
# crisp (one cause, one effect).


class _Scenario(TypedDict):
    """A full, valid runway-input bundle (typed so the ``**`` unpack is precise)."""

    starting_cash: Decimal
    monthly_revenue: Decimal
    monthly_fixed_cost: Decimal
    growth_rate: Decimal
    horizon_months: int
    min_runway_months: int


@st.composite
def _scenario(draw: st.DrawFn) -> _Scenario:
    """A full, valid runway-input bundle (min_runway pinned to 0 for monotonicity)."""
    return _Scenario(
        starting_cash=draw(_nonneg_money),
        monthly_revenue=draw(_nonneg_money),
        monthly_fixed_cost=draw(_nonneg_money),
        growth_rate=draw(_growth),
        horizon_months=draw(_horizon),
        min_runway_months=0,
    )


def _runway_with(base: _Scenario, **override: Decimal | int) -> Decimal:
    """Runway months for ``base`` with the given field(s) overridden."""
    spec: _Scenario = {**base, **override}  # type: ignore[typeddict-item]
    return _MODEL.compute(OperationalRunwayInputs(**spec)).metrics.get("runway_months")


_pair_money = st.tuples(_nonneg_money, _nonneg_money)
_pair_growth = st.tuples(_growth, _growth)


@given(base=_scenario(), pair=_pair_money)
def test_higher_fixed_cost_never_increases_runway(
    base: _Scenario, pair: tuple[Decimal, Decimal]
) -> None:
    lo, hi = sorted(pair)
    # More burn each month can only shorten (never lengthen) the runway.
    assert _runway_with(base, monthly_fixed_cost=hi) <= _runway_with(base, monthly_fixed_cost=lo)


@given(base=_scenario(), pair=_pair_money)
def test_higher_starting_cash_never_decreases_runway(
    base: _Scenario, pair: tuple[Decimal, Decimal]
) -> None:
    lo, hi = sorted(pair)
    assert _runway_with(base, starting_cash=hi) >= _runway_with(base, starting_cash=lo)


@given(base=_scenario(), pair=_pair_money)
def test_higher_revenue_never_decreases_runway(
    base: _Scenario, pair: tuple[Decimal, Decimal]
) -> None:
    lo, hi = sorted(pair)
    # growth >= -0.9 keeps the multiplier (1+g) non-negative, so a larger starting
    # revenue is never smaller at any month -> never less inflow -> never less runway.
    assert _runway_with(base, monthly_revenue=hi) >= _runway_with(base, monthly_revenue=lo)


@given(base=_scenario(), pair=_pair_growth)
def test_faster_growth_never_decreases_runway(
    base: _Scenario, pair: tuple[Decimal, Decimal]
) -> None:
    lo, hi = sorted(pair)
    # Higher growth means revenue is never lower at any month, so cash is never
    # lower -> runway never shorter.
    assert _runway_with(base, growth_rate=hi) >= _runway_with(base, growth_rate=lo)


@given(base=_scenario())
def test_runway_is_bounded_by_horizon(base: _Scenario) -> None:
    runway = _runway_with(base)
    # Bounded loop: the runway never exceeds the horizon and is never negative.
    assert Decimal(0) <= runway <= Decimal(base["horizon_months"])


# -- determinism --


@given(base=_scenario())
def test_compute_is_deterministic(base: _Scenario) -> None:
    ins = OperationalRunwayInputs(**base)
    assert _MODEL.compute(ins) == _MODEL.compute(ins)  # pure, no clock/randomness


# -- why == what: verdict drivers cannot contradict the action --


@given(base=_scenario(), min_runway=st.integers(min_value=0, max_value=24))
def test_verdict_drivers_match_action(base: _Scenario, min_runway: int) -> None:
    spec: _Scenario = {**base, "min_runway_months": min_runway}
    out = _MODEL.compute(OperationalRunwayInputs(**spec))
    runway = int(out.metrics.get("runway_months"))
    horizon = int(base["horizon_months"])
    action = out.recommendation.action
    primary = out.recommendation.primary_driver()
    assert primary.label == "runway_months"
    # The primary driver's signed contribution is the exact distance from the floor.
    assert primary.contribution == Decimal(runway) - Decimal(min_runway)
    if runway >= horizon:
        assert action == "operations_self_sustaining"
    elif runway >= min_runway:
        assert action == "monitor_runway"
    else:
        assert action == "raise_capital_now"
    # Direction agrees: above-floor raises, below-floor lowers.
    if runway >= min_runway:
        assert primary.direction.value == "raises"
    else:
        assert primary.direction.value == "lowers"
    # The cost and growth drivers always carry exact, signed contributions.
    cost_driver = out.recommendation.drivers[1]
    growth_driver = out.recommendation.drivers[2]
    assert cost_driver.label == "monthly_fixed_cost"
    assert cost_driver.contribution == -base["monthly_fixed_cost"]
    assert growth_driver.label == "growth_rate"
    assert growth_driver.contribution == base["growth_rate"]


# -- fail-closed cases (impossible inputs) --


def _valid_baseline_dict() -> dict[str, Decimal | int]:
    """A fully-valid runway-input kwarg dict to corrupt one field at a time."""
    return {
        "starting_cash": Decimal("100"),
        "monthly_revenue": Decimal("0"),
        "monthly_fixed_cost": Decimal("100"),
        "growth_rate": Decimal("0"),
        "horizon_months": 60,
        "min_runway_months": 6,
    }


@pytest.mark.parametrize(
    "field,value,match",
    [
        ("starting_cash", Decimal("-1"), "starting_cash"),  # negative cash
        ("monthly_revenue", Decimal("-1"), "monthly_revenue"),  # negative revenue
        ("monthly_fixed_cost", Decimal("-1"), "monthly_fixed_cost"),  # negative fixed cost
        ("growth_rate", Decimal("-1"), "growth_rate"),  # growth == -1
        ("growth_rate", Decimal("-2"), "growth_rate"),  # growth < -1
        ("horizon_months", 0, "horizon_months"),  # zero horizon
        ("horizon_months", -5, "horizon_months"),  # negative horizon
        ("min_runway_months", -1, "min_runway_months"),  # negative floor
    ],
)
def test_invalid_inputs_fail_closed(field: str, value: Decimal | int, match: str) -> None:
    # A valid baseline with exactly one field corrupted -> must be refused.
    spec = _valid_baseline_dict()
    spec[field] = value
    with pytest.raises(ValueError, match=match):
        _MODEL.compute(OperationalRunwayInputs(**spec))  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "field,bad",
    [
        ("starting_cash", "NaN"),
        ("monthly_revenue", "Infinity"),
        ("monthly_fixed_cost", "NaN"),
        ("growth_rate", "Infinity"),
    ],
)
def test_non_finite_money_is_refused(field: str, bad: str) -> None:
    kwargs = {
        "starting_cash": Decimal("100"),
        "monthly_revenue": Decimal("0"),
        "monthly_fixed_cost": Decimal("10"),
        "growth_rate": Decimal("0"),
        "horizon_months": 12,
        "min_runway_months": 6,
    }
    kwargs[field] = Decimal(bad)
    with pytest.raises(ValueError, match=field):
        _MODEL.compute(OperationalRunwayInputs(**kwargs))  # type: ignore[arg-type]


def test_kind_label_is_stable() -> None:
    assert _MODEL.kind == "operational_runway_scenario"
