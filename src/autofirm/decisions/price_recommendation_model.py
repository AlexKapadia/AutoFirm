"""Pricing model: a profit-maximising price recommendation from elasticity + cost.

What this does
--------------
Turns unit cost, the price elasticity of demand, and a minimum-margin floor into
an explainable recommended price:

* **Optimal markup price** under constant-elasticity demand. For a profit-
  maximising monopolistic seller facing constant own-price elasticity
  ``epsilon > 1``, the optimal price is the cost marked up by the Lerner
  optimal-markup factor: ``price = unit_cost * epsilon / (epsilon - 1)``. As
  demand becomes more elastic (``epsilon`` grows) the factor shrinks toward 1
  (price approaches cost); as it approaches 1 the factor diverges (pricing power
  rises). This is the standard optimal-markup / Lerner-index result.
* **Margin floor.** The recommended price is never allowed below
  ``unit_cost / (1 - min_margin)`` -- the price that yields exactly the required
  gross margin -- so a thin-elasticity recommendation can never breach the firm's
  margin policy. The binding constraint becomes the dominant driver in the
  explanation.

Formula (Lerner index / constant-elasticity optimal markup; B5 pricing canon)
-----------------------------------------------------------------------------
* ``markup_price = unit_cost * epsilon / (epsilon - 1)``  (requires ``epsilon > 1``)
* ``floor_price  = unit_cost / (1 - min_margin)``         (requires ``0 <= min_margin < 1``)
* ``recommended  = max(markup_price, floor_price)``

Reproduced exactly; all monetary values are exact :class:`~decimal.Decimal`
(CLAUDE.md §3.11), never floats. ``docs/research/B5-pricing-and-monetization``.

Why it exists / where it sits
-----------------------------
The pricing concrete model of ``autofirm.decisions``. Specialises
:class:`DecisionModel`; argued correct from invariants (price monotone up in
cost; markup monotone down in elasticity; floor never breached -- §3.9), not
fitted to a fixture. Runs on real cost/elasticity estimates; tests synthetic
only (§3.12).

Security / compliance invariants upheld
---------------------------------------
Fail closed (§5.6): a non-positive cost, an elasticity ``<= 1`` (no finite
profit-maximising price -- demand is inelastic/unit-elastic), or a margin outside
``[0, 1)`` are REFUSED with ``ValueError`` rather than returning a divergent,
negative, or policy-breaching price.
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

__all__ = ["PriceRecommendationInputs", "PriceRecommendationModel"]

# Wide fixed precision so the deterministic markup/floor divisions never silently
# round (determinism -- CLAUDE.md §3.6/§3.11).
_PRICING_PRECISION = 50


class PriceRecommendationInputs(DecisionInputs):
    """Validated pricing inputs (exact ``Decimal``; fail-closed bounds).

    Args (fields):
        unit_cost: Marginal/unit cost to produce one unit (> 0).
        price_elasticity: Magnitude of own-price elasticity of demand. Must be
            ``> 1`` for a finite profit-maximising price (elastic demand). Supplied
            as a positive magnitude (e.g. ``2.5`` for an elasticity of -2.5).
        min_margin: Required minimum gross margin as a fraction in ``[0, 1)``
            (e.g. ``0.6`` for a 60% floor). The recommended price never yields a
            margin below this.
    """

    unit_cost: Decimal
    price_elasticity: Decimal
    min_margin: Decimal = Decimal("0")


def _validate(inputs: PriceRecommendationInputs) -> None:
    """Fail-closed domain validation for the optimal-markup identity (§5.6)."""
    if not inputs.unit_cost.is_finite() or inputs.unit_cost <= 0:
        # fail-closed: a non-positive cost has no meaningful markup price.
        raise ValueError(f"unit_cost must be a finite Decimal > 0, got {inputs.unit_cost}")
    if not inputs.price_elasticity.is_finite() or inputs.price_elasticity <= Decimal(1):
        # fail-closed: at epsilon <= 1 demand is unit-/inelastic and the markup
        # factor diverges or goes negative -- there is no finite optimum.
        raise ValueError(
            f"price_elasticity must be a finite Decimal > 1 (elastic demand), "
            f"got {inputs.price_elasticity}"
        )
    if not (Decimal(0) <= inputs.min_margin < Decimal(1)):
        # fail-closed: a margin floor outside [0, 1) makes the floor price
        # undefined (>=1 divides by zero or flips sign).
        raise ValueError(f"min_margin must be in [0, 1), got {inputs.min_margin}")


class PriceRecommendationModel(DecisionModel[PriceRecommendationInputs]):
    """Deterministic constant-elasticity optimal-markup price with a margin floor."""

    @property
    def kind(self) -> str:
        """Stable model-family label used by the persistence seam."""
        return "price_recommendation"

    def compute(self, inputs: PriceRecommendationInputs) -> DecisionOutput:
        """Compute the markup price, the margin-floor price, and recommend the max.

        The dominant driver names whichever constraint set the price -- the
        elasticity-driven optimal markup, or the margin floor when it binds -- so
        the explanation states exactly why this price and not another (§3.11).
        """
        _validate(inputs)
        with localcontext() as ctx:
            ctx.prec = _PRICING_PRECISION
            # Lerner optimal markup: cost * epsilon / (epsilon - 1).
            markup_factor = inputs.price_elasticity / (inputs.price_elasticity - Decimal(1))
            markup_price = inputs.unit_cost * markup_factor
            # Margin floor price: cost / (1 - min_margin).
            floor_price = inputs.unit_cost / (Decimal(1) - inputs.min_margin)
            floor_binds = floor_price > markup_price
            recommended_price = floor_price if floor_binds else markup_price
            # Realised gross margin at the recommended price: (p - c) / p.
            realised_margin = (recommended_price - inputs.unit_cost) / recommended_price

        metrics = DecisionMetrics(
            values={
                "markup_factor": markup_factor,
                "markup_price": markup_price,
                "floor_price": floor_price,
                "recommended_price": recommended_price,
                "realised_margin": realised_margin,
            }
        )
        recommendation = self._derive_recommendation(
            inputs=inputs,
            recommended_price=recommended_price,
            floor_binds=floor_binds,
        )
        return DecisionOutput(metrics=metrics, recommendation=recommendation)

    def _derive_recommendation(
        self,
        *,
        inputs: PriceRecommendationInputs,
        recommended_price: Decimal,
        floor_binds: bool,
    ) -> DecisionRecommendation:
        """Attach the drivers behind the chosen price (which constraint bound it).

        Drivers are ordered most-influential first: the binding constraint
        (margin floor vs. elasticity markup) heads the list, then cost (which
        scales the whole price). The action restates the exact recommended price,
        so the "what" is literally the recommended number and the "why" is the
        constraint that produced it (§3.11).
        """
        if floor_binds:
            binding_driver = DecisionDriver(
                label="min_margin_floor",
                direction=DriverDirection.RAISES,  # the floor lifted price above the markup
                contribution=inputs.min_margin,
            )
            rationale = "margin floor binds — priced to hold the minimum gross margin"
        else:
            # More-elastic demand LOWERS the markup price; the elasticity is the
            # reason the price sits where it does relative to cost.
            binding_driver = DecisionDriver(
                label="price_elasticity",
                direction=DriverDirection.LOWERS,
                contribution=-inputs.price_elasticity,
            )
            rationale = "elastic demand sets the profit-maximising markup over cost"

        cost_driver = DecisionDriver(
            label="unit_cost",
            direction=DriverDirection.RAISES,  # higher cost always raises the price
            contribution=inputs.unit_cost,
        )
        return DecisionRecommendation(
            action=f"set_price={recommended_price}",
            rationale=rationale,
            drivers=(binding_driver, cost_driver),
        )
