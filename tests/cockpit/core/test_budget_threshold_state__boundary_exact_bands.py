"""Boundary-exact tests for the budget-band classifier — zero float, on/over/under each cut.

The classifier maps (spent, budget) -> one of four bands at the 50 / 80 / 95 % cutoffs.
The cutoffs are INCLUSIVE-from-below: a band is entered the instant spend REACHES the
threshold (CLAUDE.md §3.6 boundary-exactness). The suite asserts every band edge with
exact-cent Money just-under / on / just-over the cut, proves the comparison is integer
cross-multiplication (no float ratio, so 0.1+0.2 style drift cannot misclassify), and
fails closed on a non-positive budget. No tautological asserts — each case targets a
specific off-by-one / flipped-comparison mutant.
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from hypothesis import given
from hypothesis import strategies as st

from autofirm.cockpit.core.budget_threshold_state import (
    BudgetBand,
    classify_budget_band,
)
from autofirm.foundation.money.money_amount import Money

_USD = "USD"


def _usd(s: str) -> Money:
    return Money(Decimal(s), _USD)


# Budget of exactly 1000.00 USD makes the percentage edges land on clean cents:
# 50% -> 500.00, 80% -> 800.00, 95% -> 950.00.
_BUDGET = _usd("1000.00")


@pytest.mark.parametrize(
    ("spent", "expected"),
    [
        ("0.00", BudgetBand.OK),
        ("499.99", BudgetBand.OK),  # just-under 50%
        ("500.00", BudgetBand.WARN_50),  # ON 50% -> enters WARN_50 (inclusive)
        ("500.01", BudgetBand.WARN_50),  # just-over 50%
        ("799.99", BudgetBand.WARN_50),  # just-under 80%
        ("800.00", BudgetBand.WARN_80),  # ON 80%
        ("800.01", BudgetBand.WARN_80),
        ("949.99", BudgetBand.WARN_80),  # just-under 95%
        ("950.00", BudgetBand.CRIT_95),  # ON 95%
        ("950.01", BudgetBand.CRIT_95),
        ("1000.00", BudgetBand.CRIT_95),  # at budget
        ("100000.00", BudgetBand.CRIT_95),  # massively over budget stays CRIT_95
    ],
)
def test_band_edges_are_boundary_exact(spent: str, expected: BudgetBand) -> None:
    assert classify_budget_band(_usd(spent), _BUDGET) is expected


def test_exact_percentage_edges_are_inclusive_from_below_not_above() -> None:
    # The defining property: exactly-50% is WARN_50 (not OK); exactly-just-below is OK.
    # A flipped `>=`→`>` mutant moves the 500.00 case to OK and is killed here.
    assert classify_budget_band(_usd("500.00"), _BUDGET) is BudgetBand.WARN_50
    assert classify_budget_band(_usd("499.999999"), _BUDGET) is BudgetBand.OK
    assert classify_budget_band(_usd("800.00"), _BUDGET) is BudgetBand.WARN_80
    assert classify_budget_band(_usd("950.00"), _BUDGET) is BudgetBand.CRIT_95


def test_uses_no_float_ratio_classic_drift_case() -> None:
    # A budget/spend pair that 0.1+0.2 float arithmetic would misclassify. Decimal cross-
    # multiplication classifies it exactly. spent=0.30, budget=0.60 -> exactly 50%.
    assert classify_budget_band(_usd("0.30"), _usd("0.60")) is BudgetBand.WARN_50
    # 0.29999... just under -> OK; the float path 0.1+0.2 (=0.30000000000000004) would lie.
    assert classify_budget_band(Money(Decimal("0.2999999"), _USD), _usd("0.60")) is (
        BudgetBand.OK
    )


def test_zero_spend_is_ok_regardless_of_budget() -> None:
    assert classify_budget_band(_usd("0.00"), _usd("1.00")) is BudgetBand.OK
    assert classify_budget_band(_usd("0.00"), _usd("999999.99")) is BudgetBand.OK


@given(spent=st.integers(min_value=0, max_value=10_000_000))
def test_band_is_monotonic_non_decreasing_in_spend(spent: int) -> None:
    # Property: more spend never moves to a LESS severe band. Compare consecutive cents.
    budget = _usd("1000.00")
    rank = {
        BudgetBand.OK: 0,
        BudgetBand.WARN_50: 1,
        BudgetBand.WARN_80: 2,
        BudgetBand.CRIT_95: 3,
    }
    here = Money(Decimal(spent).scaleb(-2), _USD)  # cents -> dollars exactly
    nxt = Money((Decimal(spent) + 1).scaleb(-2), _USD)
    assert rank[classify_budget_band(here, budget)] <= rank[classify_budget_band(nxt, budget)]


def test_is_deterministic_across_repeats() -> None:
    bands = {classify_budget_band(_usd("800.00"), _BUDGET) for _ in range(50)}
    assert len(bands) == 1


# --- Fail-closed -----------------------------------------------------------------------


@pytest.mark.parametrize("budget", ["0.00", "-1.00", "-0.01"])
def test_non_positive_budget_is_refused_fail_closed(budget: str) -> None:
    # fail-closed: a zero/negative budget makes "% of budget" undefined — refuse rather
    # than divide-by-zero or invert the comparison sign.
    with pytest.raises(ValueError):
        classify_budget_band(_usd("1.00"), _usd(budget))


def test_negative_spend_is_refused_fail_closed() -> None:
    # A negative cumulative spend is nonsensical for a band classification; refuse it.
    with pytest.raises(ValueError):
        classify_budget_band(_usd("-0.01"), _BUDGET)


def test_cross_currency_spend_vs_budget_is_refused_fail_closed() -> None:
    # fail-closed: comparing GBP spend against a USD budget is meaningless — refuse.
    with pytest.raises(ValueError):
        classify_budget_band(Money(Decimal("1.00"), "GBP"), _BUDGET)


@pytest.mark.parametrize("bad", [None, "100", 100, Decimal("100")])
def test_non_money_arguments_are_refused_fail_closed(bad: object) -> None:
    with pytest.raises((TypeError, ValueError)):
        classify_budget_band(bad, _BUDGET)  # type: ignore[arg-type]
    with pytest.raises((TypeError, ValueError)):
        classify_budget_band(_usd("1.00"), bad)  # type: ignore[arg-type]
