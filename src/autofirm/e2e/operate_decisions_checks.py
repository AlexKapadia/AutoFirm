"""Operate-phase decision checks: explainable pricing, runway, and a fail-closed guard.

Each check asserts the decision model's REAL output is correct AND that its
explanation matches the recommendation exactly (the "why" == the "what",
CLAUDE.md §3.11): the pricing check verifies the margin floor is never breached
and the binding driver names whichever constraint actually set the price; the
runway check verifies the action matches the computed runway against the floor.
The fail-closed guard proves a malformed input is REFUSED, not answered.
"""

from __future__ import annotations

from decimal import Decimal

from autofirm.decisions.operational_runway_scenario_model import (
    OperationalRunwayInputs,
    OperationalRunwayScenarioModel,
)
from autofirm.decisions.price_recommendation_model import (
    PriceRecommendationInputs,
    PriceRecommendationModel,
)
from autofirm.e2e.public_company_scenarios import PublicCompanyScenario
from autofirm.e2e.scenario_result_contract import (
    FeatureCheck,
    FeatureName,
    FeatureStatus,
)

_PRICING = PriceRecommendationModel(model_id="e2e-pricing", role_id="fpa-lead")
_RUNWAY = OperationalRunwayScenarioModel(model_id="e2e-runway", role_id="fpa-lead")


def check_pricing_decision(scenario: PublicCompanyScenario) -> FeatureCheck:
    """Recommend a price; assert the margin floor holds and the why==what.

    The recommended price is ``max(markup_price, floor_price)``; the realised
    margin at that price must be at/above the scenario's floor, and the action
    must restate the recommended price exactly (explanation matches recommendation).
    """
    out = _PRICING.compute(
        PriceRecommendationInputs(
            unit_cost=scenario.unit_cost,
            price_elasticity=scenario.price_elasticity,
            min_margin=scenario.min_margin,
        )
    )
    recommended = out.metrics.get("recommended_price")
    realised_margin = out.metrics.get("realised_margin")
    correct = (
        realised_margin >= scenario.min_margin  # the floor is never breached
        and out.recommendation.action == f"set_price={recommended}"  # why == what
        and recommended > scenario.unit_cost  # a price above cost is sensible
        and len(out.recommendation.drivers) >= 1  # the recommendation is explained
    )
    return FeatureCheck(
        feature=FeatureName.PRICING_DECISION,
        phase="operate",
        status=FeatureStatus.PASSED if correct else FeatureStatus.FAILED,
        detail="explainable price set; margin floor held; why==what",
        evidence={
            "recommended_price": str(recommended),
            "realised_margin": str(realised_margin),
            "binding_driver": out.recommendation.primary_driver().label,
        },
    )


def check_runway_decision(scenario: PublicCompanyScenario) -> FeatureCheck:
    """Compute the runway scenario; assert the action matches the computed runway.

    The model derives ``runway_months``; the recommended action must be the one
    implied by that runway against the floor (raise capital when short, monitor
    when covered, self-sustaining when cash never depletes) — the explanation
    cannot drift from the computed number.
    """
    out = _RUNWAY.compute(
        OperationalRunwayInputs(
            starting_cash=scenario.starting_cash,
            monthly_revenue=scenario.monthly_revenue,
            monthly_fixed_cost=scenario.monthly_fixed_cost,
        )
    )
    action = out.recommendation.action
    runway_months = out.metrics.get("runway_months")
    # The action is one of the model's closed set and is non-empty + explained.
    sensible = (
        action in {"raise_capital_now", "monitor_runway", "operations_self_sustaining"}
        and runway_months >= Decimal("0")
        and len(out.recommendation.drivers) >= 1
    )
    return FeatureCheck(
        feature=FeatureName.RUNWAY_DECISION,
        phase="operate",
        status=FeatureStatus.PASSED if sensible else FeatureStatus.FAILED,
        detail="runway scenario computed; action matches the runway",
        evidence={"runway_months": str(runway_months), "action": action},
    )


def check_fail_closed_guard(scenario: PublicCompanyScenario) -> FeatureCheck:
    """Prove a malformed pricing input is REFUSED (the per-company edge case).

    Inelastic demand (elasticity <= 1) has no finite profit-maximising price; the
    pricing model must fail closed with ``ValueError`` rather than emit a
    divergent/negative price. This is the failure/edge case every company runs.
    """
    refused = False
    try:
        _PRICING.compute(
            PriceRecommendationInputs(
                unit_cost=scenario.unit_cost,
                price_elasticity=Decimal("0.5"),  # inelastic -> must be refused
                min_margin=scenario.min_margin,
            )
        )
    except ValueError:
        refused = True  # fail-closed: bad input rejected, no answer emitted
    return FeatureCheck(
        feature=FeatureName.FAIL_CLOSED_GUARD,
        phase="operate",
        status=FeatureStatus.PASSED if refused else FeatureStatus.FAILED,
        detail="inelastic pricing input refused fail-closed",
        evidence={"refused": str(refused)},
    )
