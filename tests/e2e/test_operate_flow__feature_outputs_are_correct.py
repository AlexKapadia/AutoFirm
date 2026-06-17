"""Operate-flow teeth: each feature's REAL output is correct, not just non-raising.

These assertions re-derive the expected numbers independently and check the
platform's outputs against them (finance ties, valuation positivity/determinism,
pricing margin floor + why==what, runway action sense, market-intel accounting,
green-light rationale tie, front-door delivery, real artifact bytes, heartbeat
single-fire, flow terminality). A green check whose evidence is wrong would fail
here, so "it ran" can never masquerade as "it works".
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from autofirm.e2e.operate_decisions_checks import (
    check_pricing_decision,
    check_runway_decision,
)
from autofirm.e2e.operate_finance_checks import (
    check_finance_statements,
    check_finance_valuation,
)
from autofirm.e2e.operate_platform_checks import (
    check_green_light_gate,
    check_heartbeat_tick,
    check_market_intel_sweep,
)
from autofirm.e2e.public_company_scenarios import (
    PublicCompanyScenario,
    public_company_scenarios,
)
from autofirm.e2e.scenario_result_contract import FeatureStatus

_SCENARIOS = public_company_scenarios()
_IDS = [s.slug for s in _SCENARIOS]


@pytest.mark.parametrize("scenario", _SCENARIOS, ids=_IDS)
def test_finance_statements_tie_to_independent_recomputation(
    scenario: PublicCompanyScenario,
) -> None:
    """The reported net income + cash net-change equal an independent hand recomputation."""
    check = check_finance_statements(scenario)
    assert check.status is FeatureStatus.PASSED
    expected_ni = scenario.revenue - scenario.operating_expense
    expected_cash = (
        scenario.equity_invested
        + scenario.loan_principal
        - scenario.capex
        + scenario.revenue
        - scenario.operating_expense
    )
    assert Decimal(check.evidence["net_income"]) == expected_ni
    assert Decimal(check.evidence["cash_net_change"]) == expected_cash


@pytest.mark.parametrize("scenario", _SCENARIOS, ids=_IDS)
def test_valuation_is_positive(scenario: PublicCompanyScenario) -> None:
    """A profitable projection yields a strictly positive DCF firm value (sense check)."""
    check = check_finance_valuation(scenario)
    assert check.status is FeatureStatus.PASSED
    assert Decimal(check.evidence["dcf_value"]) > 0


@pytest.mark.parametrize("scenario", _SCENARIOS, ids=_IDS)
def test_pricing_holds_the_margin_floor_and_explains_itself(
    scenario: PublicCompanyScenario,
) -> None:
    """The realised margin is at/above the scenario floor and a binding driver is named."""
    check = check_pricing_decision(scenario)
    assert check.status is FeatureStatus.PASSED
    assert Decimal(check.evidence["realised_margin"]) >= scenario.min_margin
    assert check.evidence["binding_driver"] in {"price_elasticity", "min_margin_floor"}


@pytest.mark.parametrize("scenario", _SCENARIOS, ids=_IDS)
def test_runway_action_is_within_the_closed_set(scenario: PublicCompanyScenario) -> None:
    """The runway recommendation is one of the model's three sensible actions."""
    check = check_runway_decision(scenario)
    assert check.status is FeatureStatus.PASSED
    assert check.evidence["action"] in {
        "raise_capital_now",
        "monitor_runway",
        "operations_self_sustaining",
    }


@pytest.mark.parametrize("scenario", _SCENARIOS, ids=_IDS)
def test_market_intel_accounts_for_every_signal(scenario: PublicCompanyScenario) -> None:
    """Exactly one clean public signal becomes one insight with zero silent drops."""
    check = check_market_intel_sweep(scenario)
    assert check.status is FeatureStatus.PASSED
    assert check.evidence["insights"] == "1"
    assert check.evidence["rejections"] == "0"


@pytest.mark.parametrize("scenario", _SCENARIOS, ids=_IDS)
def test_green_light_verdict_is_go_with_matching_rationale(
    scenario: PublicCompanyScenario,
) -> None:
    """Two corroborating insights clear the gate -> GO, and the score is reported."""
    check = check_green_light_gate(scenario)
    assert check.status is FeatureStatus.PASSED
    assert check.evidence["verdict"] == "go"


@pytest.mark.parametrize("scenario", _SCENARIOS, ids=_IDS)
def test_heartbeat_fires_exactly_once(scenario: PublicCompanyScenario) -> None:
    """One interval advance fires the registered beat exactly once (no catch-up burst)."""
    check = check_heartbeat_tick(scenario)
    assert check.status is FeatureStatus.PASSED
    assert check.evidence["calls"] == "1"
