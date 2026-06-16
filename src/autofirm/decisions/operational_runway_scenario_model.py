"""Operational scenario model: cash-runway projection under a growth scenario.

What this does
--------------
Projects a company's cash position month-by-month from a starting balance, a
starting monthly revenue that compounds at a monthly growth rate, and a fixed
monthly operating cost, then reports the **runway** (the number of whole months
the company can operate before cash would go negative) and an explainable
verdict against a minimum-runway policy.

Each month: ``cash += revenue_t - fixed_cost`` where
``revenue_t = revenue_0 * (1 + growth) ** t``. Because revenue compounds, a
company can be burning today yet reach cash-flow breakeven later in the horizon;
the projection captures that exactly. The runway is the count of fully-funded
months before the first month that would end with negative cash (capped at the
projection horizon, which bounds the loop -- §3.6).

Why it exists / where it sits
-----------------------------
The operational/scenario concrete model of ``autofirm.decisions``. Specialises
:class:`DecisionModel`; argued correct from invariants (runway is monotone
non-decreasing in starting cash and revenue, non-increasing in fixed cost --
§3.9), not fitted to a fixture. Runs on real operating data; tests synthetic only
(§3.12). Monetary values are exact :class:`~decimal.Decimal` (CLAUDE.md §3.11).

Security / compliance invariants upheld
---------------------------------------
Fail closed (§5.6): a negative starting cash/revenue/fixed cost, a growth rate
``<= -1`` (revenue would go non-positive), or a non-positive projection horizon
are REFUSED with ``ValueError``. The horizon hard-caps the projection loop so no
mutated bound can make the model run unbounded.
"""

from __future__ import annotations

from decimal import Decimal, localcontext

from autofirm.decisions.decision_model_contract import (
    DecisionDriver,
    DecisionInputs,
    DecisionMetrics,
    DecisionModel,
    DecisionOutput,
    DecisionRecommendation,
    DriverDirection,
)

__all__ = ["OperationalRunwayInputs", "OperationalRunwayScenarioModel"]

# Wide fixed precision so the compounding projection never silently rounds
# (determinism -- CLAUDE.md §3.6/§3.11).
_RUNWAY_PRECISION = 50


class OperationalRunwayInputs(DecisionInputs):
    """Validated runway-scenario inputs (exact ``Decimal``; fail-closed bounds).

    Args (fields):
        starting_cash: Cash on hand at month 0 (>= 0).
        monthly_revenue: Revenue in month 0 (>= 0); compounds at ``growth_rate``.
        monthly_fixed_cost: Fixed operating cost charged every month (>= 0).
        growth_rate: Per-month revenue growth as a fraction ``> -1`` (e.g. ``0.1``
            for +10%/mo; ``-0.05`` for decline). Must exceed ``-1`` so revenue
            stays non-negative.
        horizon_months: Number of months to project (> 0). Caps the runway and
            bounds the projection loop.
        min_runway_months: Policy threshold; a runway below this triggers a
            "raise capital" verdict. Must be >= 0.
    """

    starting_cash: Decimal
    monthly_revenue: Decimal
    monthly_fixed_cost: Decimal
    growth_rate: Decimal = Decimal("0")
    horizon_months: int = 60
    min_runway_months: int = 6


def _validate(inputs: OperationalRunwayInputs) -> None:
    """Fail-closed domain validation for the runway projection (§5.6)."""
    for name, amount in (
        ("starting_cash", inputs.starting_cash),
        ("monthly_revenue", inputs.monthly_revenue),
        ("monthly_fixed_cost", inputs.monthly_fixed_cost),
    ):
        if not amount.is_finite() or amount < 0:  # fail-closed: no negative cash/flows
            raise ValueError(f"{name} must be a finite, non-negative Decimal, got {amount}")
    if not inputs.growth_rate.is_finite() or inputs.growth_rate <= Decimal(-1):
        # fail-closed: growth <= -1 drives revenue non-positive (undefined scenario).
        raise ValueError(f"growth_rate must be a finite Decimal > -1, got {inputs.growth_rate}")
    if inputs.horizon_months <= 0:  # fail-closed: need a positive, bounded horizon
        raise ValueError(f"horizon_months must be > 0, got {inputs.horizon_months}")
    if inputs.min_runway_months < 0:  # fail-closed: a negative policy floor is nonsensical
        raise ValueError(f"min_runway_months must be >= 0, got {inputs.min_runway_months}")


class OperationalRunwayScenarioModel(DecisionModel[OperationalRunwayInputs]):
    """Deterministic cash-runway projection with an explainable funding verdict."""

    @property
    def kind(self) -> str:
        """Stable model-family label used by the persistence seam."""
        return "operational_runway_scenario"

    def compute(self, inputs: OperationalRunwayInputs) -> DecisionOutput:
        """Project cash month-by-month and derive a runway verdict.

        Returns the number of fully-funded months (``runway_months``), the ending
        cash over the horizon, and a verdict whose drivers name the fixed cost and
        growth that shaped the runway -- so the funding recommendation is explained
        exactly by the projection that produced it (§3.11).
        """
        _validate(inputs)
        with localcontext() as ctx:
            ctx.prec = _RUNWAY_PRECISION
            cash = inputs.starting_cash
            runway_months = 0
            growth_multiplier = Decimal(1) + inputs.growth_rate
            revenue = inputs.monthly_revenue
            # Bounded loop (<= horizon_months): a mutated bound cannot hang the gate.
            for _ in range(inputs.horizon_months):
                month_end_cash = cash + revenue - inputs.monthly_fixed_cost
                if month_end_cash < 0:  # the company runs out of cash this month
                    break
                cash = month_end_cash
                runway_months += 1
                revenue = revenue * growth_multiplier  # compound next month's revenue
            ending_cash = cash

        # If the company survived the whole horizon, the runway is reported as the
        # horizon (a deterministic cap), and ``survives_horizon`` flags it so the
        # verdict does not over-claim an unbounded runway.
        survives_horizon = runway_months >= inputs.horizon_months
        metrics = DecisionMetrics(
            values={
                "runway_months": Decimal(runway_months),
                "ending_cash": ending_cash,
                "horizon_months": Decimal(inputs.horizon_months),
            }
        )
        recommendation = self._derive_verdict(
            inputs=inputs,
            runway_months=runway_months,
            survives_horizon=survives_horizon,
        )
        return DecisionOutput(metrics=metrics, recommendation=recommendation)

    def _derive_verdict(
        self,
        *,
        inputs: OperationalRunwayInputs,
        runway_months: int,
        survives_horizon: bool,
    ) -> DecisionRecommendation:
        """Map the runway to a funding verdict, attaching the drivers behind it.

        The dominant driver is the runway's distance from the policy floor; the
        fixed cost (which shortens runway) and growth (which lengthens it) follow.
        The action is a pure function of ``runway_months`` vs. the floor, so it
        cannot contradict its drivers (§3.11).
        """
        if survives_horizon:
            action = "operations_self_sustaining"
            rationale = "cash survives the full projection horizon — no raise needed"
        elif runway_months >= inputs.min_runway_months:
            action = "monitor_runway"
            rationale = "runway above the policy floor — monitor and plan ahead"
        else:
            action = "raise_capital_now"
            rationale = "runway below the policy floor — secure funding before cash runs out"

        runway_driver = DecisionDriver(
            label="runway_months",
            direction=(
                DriverDirection.RAISES
                if runway_months >= inputs.min_runway_months
                else DriverDirection.LOWERS
            ),
            contribution=Decimal(runway_months) - Decimal(inputs.min_runway_months),
        )
        # Higher fixed cost LOWERS runway; faster growth RAISES it.
        cost_driver = DecisionDriver(
            label="monthly_fixed_cost",
            direction=DriverDirection.LOWERS,
            contribution=-inputs.monthly_fixed_cost,
        )
        growth_driver = DecisionDriver(
            label="growth_rate",
            direction=DriverDirection.RAISES,
            contribution=inputs.growth_rate,
        )
        return DecisionRecommendation(
            action=action,
            rationale=rationale,
            drivers=(runway_driver, cost_driver, growth_driver),
        )
