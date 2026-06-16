"""Customer-base unit-economics model: CAC, LTV, churn, payback, LTV:CAC verdict.

What this does
--------------
Turns a company's real subscription/customer metrics into the canonical
unit-economics quantities and an explainable health verdict:

* **LTV** (lifetime value) = ``ARPA_margin / churn`` -- the standard SaaS
  contribution-margin lifetime-value identity, where the expected customer
  lifetime in periods is ``1 / churn`` and ``ARPA_margin`` is per-period revenue
  per account times the gross margin.
* **Payback period** (in periods) = ``CAC / ARPA_margin`` -- how long the
  per-period margin takes to repay the acquisition cost.
* **LTV:CAC ratio** = ``LTV / CAC`` -- the headline efficiency ratio. The verdict
  uses the widely-cited 3.0 healthy threshold and a 1.0 break-even floor.

Formulae (SaaS unit-economics canon; see docs/research/B5-pricing-and-monetization)
-----------------------------------------------------------------------------------
* ``LTV = (ARPA * gross_margin) / monthly_churn_rate``
* ``payback_periods = CAC / (ARPA * gross_margin)``
* ``ltv_cac = LTV / CAC``

These are reproduced exactly; every monetary value stays an exact
:class:`~decimal.Decimal` (CLAUDE.md §3.11), never a float.

Why it exists / where it sits
-----------------------------
The customer-base concrete model of ``autofirm.decisions``. It specialises the
:class:`DecisionModel` contract; correctness is argued from invariants
(monotonicity of LTV in churn/margin, exactness of the identities) rather than
fitted to any one company (§3.9). It runs on REAL customer data for live
decisions; platform tests use synthetic fixtures only (§3.12).

Security / compliance invariants upheld
---------------------------------------
Fail closed (§5.6): a non-positive churn (infinite/undefined lifetime), a
non-positive or >100% margin, a negative ARPA/CAC, or a zero CAC (undefined
ratio/payback) are REFUSED with ``ValueError`` rather than producing a
silently-wrong, infinite, or negative recommendation.
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

__all__ = ["CustomerUnitEconomicsInputs", "CustomerUnitEconomicsModel"]

# Wide fixed precision for the deterministic division identities so the exact
# arithmetic below never silently rounds (determinism -- CLAUDE.md §3.6/§3.11).
_UNIT_ECON_PRECISION = 50

# Decision thresholds for the LTV:CAC verdict. These are the widely-cited SaaS
# benchmarks (healthy >= 3x; below break-even < 1x), passed as injectable inputs
# below so they are tunable per company and NEVER magic constants fitted to a
# fixture (§3.9). The names here are the documented defaults only.
_DEFAULT_HEALTHY_LTV_CAC = Decimal("3")
_DEFAULT_BREAKEVEN_LTV_CAC = Decimal("1")


class CustomerUnitEconomicsInputs(DecisionInputs):
    """Validated unit-economics inputs (all exact ``Decimal``; fail-closed bounds).

    Args (fields):
        arpa: Average revenue per account per period (>= 0).
        gross_margin: Gross margin as a fraction in ``(0, 1]`` (e.g. ``0.8``).
        monthly_churn_rate: Per-period churn as a fraction in ``(0, 1]``; the
            expected lifetime is ``1 / churn`` periods. Must be > 0 (a zero churn
            implies an infinite, undefined lifetime -- refused).
        cac: Customer acquisition cost (> 0; a zero CAC makes the ratio/payback
            undefined).
        healthy_ltv_cac: The LTV:CAC at/above which the verdict is "healthy".
        breakeven_ltv_cac: The LTV:CAC below which the verdict is "unprofitable".
    """

    arpa: Decimal
    gross_margin: Decimal
    monthly_churn_rate: Decimal
    cac: Decimal
    healthy_ltv_cac: Decimal = _DEFAULT_HEALTHY_LTV_CAC
    breakeven_ltv_cac: Decimal = _DEFAULT_BREAKEVEN_LTV_CAC


def _validate(inputs: CustomerUnitEconomicsInputs) -> None:
    """Fail-closed domain validation for the unit-economics identities (§5.6)."""
    if not inputs.arpa.is_finite() or inputs.arpa < 0:  # fail-closed: revenue cannot be negative
        raise ValueError(f"arpa must be a finite, non-negative Decimal, got {inputs.arpa}")
    if not inputs.cac.is_finite() or inputs.cac <= 0:  # fail-closed: zero CAC -> undefined ratio
        raise ValueError(f"cac must be a finite Decimal > 0, got {inputs.cac}")
    if not (Decimal(0) < inputs.gross_margin <= Decimal(1)):  # fail-closed: margin in (0, 1]
        raise ValueError(f"gross_margin must be in (0, 1], got {inputs.gross_margin}")
    if not (Decimal(0) < inputs.monthly_churn_rate <= Decimal(1)):  # fail-closed: churn in (0, 1]
        raise ValueError(
            f"monthly_churn_rate must be in (0, 1] (zero implies infinite lifetime), "
            f"got {inputs.monthly_churn_rate}"
        )
    # fail-closed: an inverted threshold band would make the verdict nonsensical.
    if inputs.breakeven_ltv_cac >= inputs.healthy_ltv_cac:
        raise ValueError(
            "breakeven_ltv_cac must be strictly below healthy_ltv_cac, got "
            f"{inputs.breakeven_ltv_cac} >= {inputs.healthy_ltv_cac}"
        )


class CustomerUnitEconomicsModel(DecisionModel[CustomerUnitEconomicsInputs]):
    """Deterministic CAC/LTV/churn/payback model with an explainable health verdict."""

    @property
    def kind(self) -> str:
        """Stable model-family label used by the persistence seam."""
        return "customer_unit_economics"

    def compute(self, inputs: CustomerUnitEconomicsInputs) -> DecisionOutput:
        """Compute LTV, payback, and LTV:CAC, and derive an explainable verdict.

        The recommendation's drivers name the exact inputs that moved the verdict
        (margin and churn drive LTV up/down; CAC drives the ratio down), so the
        "why" matches the "what" exactly (§3.11).
        """
        _validate(inputs)
        with localcontext() as ctx:
            ctx.prec = _UNIT_ECON_PRECISION
            arpa_margin = inputs.arpa * inputs.gross_margin  # per-period margin per account
            lifetime_periods = Decimal(1) / inputs.monthly_churn_rate  # 1 / churn
            ltv = arpa_margin * lifetime_periods  # LTV = ARPA_margin / churn
            # arpa_margin can be 0 only if arpa is 0 (margin > 0 enforced); then
            # payback is undefined -> fail closed rather than divide by zero.
            if arpa_margin == 0:  # fail-closed: zero per-period margin -> no payback
                raise ValueError("arpa must be > 0 to define a payback period (zero margin)")
            payback_periods = inputs.cac / arpa_margin  # CAC / ARPA_margin
            ltv_cac = ltv / inputs.cac  # LTV : CAC

        metrics = DecisionMetrics(
            values={
                "arpa_margin": arpa_margin,
                "lifetime_periods": lifetime_periods,
                "ltv": ltv,
                "payback_periods": payback_periods,
                "ltv_cac": ltv_cac,
            }
        )
        recommendation = self._derive_verdict(inputs=inputs, ltv_cac=ltv_cac, ltv=ltv)
        return DecisionOutput(metrics=metrics, recommendation=recommendation)

    def _derive_verdict(
        self,
        *,
        inputs: CustomerUnitEconomicsInputs,
        ltv_cac: Decimal,
        ltv: Decimal,
    ) -> DecisionRecommendation:
        """Map the LTV:CAC ratio to a verdict, attaching the drivers that produced it.

        The drivers are ordered most-influential first: the LTV:CAC ratio itself
        (vs. the healthy threshold) is the dominant driver, followed by the churn
        and margin that built LTV. The action is a pure function of ``ltv_cac`` and
        the thresholds, so it can never disagree with its stated drivers (§3.11).
        """
        if ltv_cac >= inputs.healthy_ltv_cac:
            action = "scale_acquisition"
            rationale = "LTV:CAC at or above the healthy threshold — economics support scaling"
        elif ltv_cac >= inputs.breakeven_ltv_cac:
            action = "improve_efficiency"
            rationale = "LTV:CAC above break-even but below healthy — tighten CAC or churn"
        else:
            action = "halt_and_fix_economics"
            rationale = "LTV:CAC below break-even — acquisition loses money per customer"

        # The ratio vs. the healthy threshold is the dominant, decision-making
        # driver; its signed distance from the threshold is the exact contribution.
        ratio_driver = DecisionDriver(
            label="ltv_cac_ratio",
            direction=(
                DriverDirection.RAISES
                if ltv_cac >= inputs.healthy_ltv_cac
                else DriverDirection.LOWERS
            ),
            contribution=ltv_cac - inputs.healthy_ltv_cac,
        )
        # Higher churn LOWERS the verdict (it shrank LTV); lower churn RAISES it.
        churn_driver = DecisionDriver(
            label="monthly_churn_rate",
            direction=DriverDirection.LOWERS,
            contribution=-inputs.monthly_churn_rate,
        )
        # Higher margin RAISES the verdict (it grew LTV).
        margin_driver = DecisionDriver(
            label="gross_margin",
            direction=DriverDirection.RAISES,
            contribution=inputs.gross_margin,
        )
        return DecisionRecommendation(
            action=action,
            rationale=rationale,
            drivers=(ratio_driver, churn_driver, margin_driver),
        )
