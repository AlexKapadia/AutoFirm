"""Adversarial + property tests for the price-recommendation model.

Key invariants proven (argued from properties, never fitted to one example):
* The recommended price is the EXACT ``max(markup_price, floor_price)`` and is
  deterministic (§3.11). Worked golden examples are exact to the cent.
* The margin floor is NEVER breached: the realised gross margin at the
  recommended price is always >= ``min_margin``.
* The explanation matches the recommendation EXACTLY (why == what): the action
  restates the recommended price, and the binding driver names whichever
  constraint (margin floor vs. elasticity markup) actually set the price.
* MONOTONICITY: higher cost never lowers the price; more-elastic demand never
  raises the markup price.
* Boundary-exact behaviour where the floor and markup cross.
* Malformed / insufficient / contradictory inputs fail closed (§5.6).
Designed to KILL mutants on ``price_recommendation_model``.
"""

from decimal import Decimal, localcontext

import pytest
from hypothesis import given
from hypothesis import strategies as st

from autofirm.decisions.price_recommendation_model import (
    PriceRecommendationInputs,
    PriceRecommendationModel,
)

_MODEL = PriceRecommendationModel(model_id="pr", role_id="pricing-analyst")

# Strategies over the valid domain (synthetic only -- no PII, §3.12).
_positive_cost = st.decimals(
    min_value=Decimal("0.01"), max_value=Decimal("100000"), allow_nan=False, allow_infinity=False
)
# Elasticity must be strictly > 1; keep it bounded away from 1 so the markup
# factor stays finite and comparisons are stable.
_elastic = st.decimals(
    min_value=Decimal("1.01"), max_value=Decimal("50"), allow_nan=False, allow_infinity=False
)
# Margin floor fraction in [0, 1).
_margin = st.decimals(
    min_value=Decimal("0"), max_value=Decimal("0.99"), allow_nan=False, allow_infinity=False
)


def _inputs(cost: str, elasticity: str, margin: str = "0") -> PriceRecommendationInputs:
    return PriceRecommendationInputs(
        unit_cost=Decimal(cost),
        price_elasticity=Decimal(elasticity),
        min_margin=Decimal(margin),
    )


def _recommended(out_price: str) -> str:
    return f"set_price={out_price}"


# -- worked golden examples: EXACT to the cent, zero numerical error --


def test_golden_markup_binds_is_exact() -> None:
    # cost=100, epsilon=2 -> markup factor = 2/1 = 2 -> markup_price=200.
    # No margin floor (0) -> floor_price = 100/1 = 100 < 200 -> markup binds.
    out = _MODEL.compute(_inputs("100", "2", "0"))
    assert out.metrics.get("markup_factor") == Decimal("2")
    assert out.metrics.get("markup_price") == Decimal("200")
    assert out.metrics.get("floor_price") == Decimal("100")
    assert out.metrics.get("recommended_price") == Decimal("200")
    # realised margin = (200-100)/200 = 0.5 exactly.
    assert out.metrics.get("realised_margin") == Decimal("0.5")
    assert out.recommendation.action == _recommended("200")


def test_golden_floor_binds_is_exact() -> None:
    # cost=100, epsilon=10 -> markup factor = 10/9 -> markup_price ~= 111.11...
    # margin floor 0.6 -> floor_price = 100/(1-0.6) = 100/0.4 = 250 > markup.
    out = _MODEL.compute(_inputs("100", "10", "0.6"))
    assert out.metrics.get("floor_price") == Decimal("250")
    assert out.metrics.get("recommended_price") == Decimal("250")
    # realised margin = (250-100)/250 = 0.6 exactly -- the floor is held to the cent.
    assert out.metrics.get("realised_margin") == Decimal("0.6")
    # The action restates str(recommended_price); 100/0.4 canonicalises to 2.5E+2.
    assert out.recommendation.action == _recommended(str(out.metrics.get("recommended_price")))
    assert out.metrics.get("recommended_price") == Decimal("2.5E+2") == Decimal("250")


def test_golden_markup_factor_for_elasticity_three_is_exact() -> None:
    # epsilon=3 -> factor = 3/2 = 1.5; cost=80 -> markup_price=120.
    out = _MODEL.compute(_inputs("80", "3", "0"))
    assert out.metrics.get("markup_factor") == Decimal("1.5")
    assert out.metrics.get("markup_price") == Decimal("120")
    assert out.metrics.get("recommended_price") == Decimal("120")


# -- boundary-exact: the floor/markup crossover (on / just-over / just-under) --


def test_floor_and_markup_exactly_equal_picks_markup() -> None:
    # Construct floor_price == markup_price exactly. cost=100, epsilon=2 ->
    # markup_price=200. Choose min_margin so floor_price=200: 100/(1-m)=200 ->
    # 1-m=0.5 -> m=0.5. floor_binds is ``floor_price > markup_price`` (STRICT), so
    # at exact equality the markup branch is taken -- kills a >=/> mutant.
    out = _MODEL.compute(_inputs("100", "2", "0.5"))
    assert out.metrics.get("markup_price") == Decimal("200")
    assert out.metrics.get("floor_price") == Decimal("200")
    assert out.metrics.get("recommended_price") == Decimal("200")
    # markup branch => elasticity is the binding driver, not the floor.
    assert out.recommendation.primary_driver().label == "price_elasticity"


def test_floor_just_over_markup_picks_floor() -> None:
    # Same as above but margin nudged up so floor_price > markup_price.
    out = _MODEL.compute(_inputs("100", "2", "0.51"))
    floor = out.metrics.get("floor_price")
    markup = out.metrics.get("markup_price")
    assert floor > markup
    assert out.metrics.get("recommended_price") == floor
    assert out.recommendation.primary_driver().label == "min_margin_floor"


def test_floor_just_under_markup_picks_markup() -> None:
    out = _MODEL.compute(_inputs("100", "2", "0.49"))
    floor = out.metrics.get("floor_price")
    markup = out.metrics.get("markup_price")
    assert floor < markup
    assert out.metrics.get("recommended_price") == markup
    assert out.recommendation.primary_driver().label == "price_elasticity"


# -- the recommended price is EXACTLY max(markup, floor) (property) --


@given(cost=_positive_cost, elasticity=_elastic, margin=_margin)
def test_recommended_is_exact_max_of_markup_and_floor(
    cost: Decimal, elasticity: Decimal, margin: Decimal
) -> None:
    out = _MODEL.compute(
        PriceRecommendationInputs(
            unit_cost=cost, price_elasticity=elasticity, min_margin=margin
        )
    )
    rec = out.metrics.get("recommended_price")
    markup = out.metrics.get("markup_price")
    floor = out.metrics.get("floor_price")
    assert rec == max(markup, floor)  # exact: kills min()/swap mutants


# -- the margin floor is NEVER breached (the load-bearing safety property) --


@given(cost=_positive_cost, elasticity=_elastic, margin=_margin)
def test_recommended_price_never_below_the_floor_price(
    cost: Decimal, elasticity: Decimal, margin: Decimal
) -> None:
    # The EXACT, load-bearing safety invariant: the recommended price is never
    # below the margin-floor price ``cost/(1-margin)``. This is the guarantee the
    # module makes exactly (recommended == max(markup, floor) >= floor), with no
    # second division to reintroduce rounding. The derived ``realised_margin``
    # display metric is checked separately with a precision tolerance below.
    out = _MODEL.compute(
        PriceRecommendationInputs(
            unit_cost=cost, price_elasticity=elasticity, min_margin=margin
        )
    )
    assert out.metrics.get("recommended_price") >= out.metrics.get("floor_price")


@given(cost=_positive_cost, elasticity=_elastic, margin=_margin)
def test_realised_margin_holds_the_floor_within_precision(
    cost: Decimal, elasticity: Decimal, margin: Decimal
) -> None:
    out = _MODEL.compute(
        PriceRecommendationInputs(
            unit_cost=cost, price_elasticity=elasticity, min_margin=margin
        )
    )
    realised = out.metrics.get("realised_margin")
    # The realised margin metric is ``(p-c)/p`` at 50-digit precision; when the
    # markup binds a hair above the floor, the extra division can round it a few
    # ulps below the exact floor. The floor is held to well within that precision:
    # the absolute shortfall is bounded by a tiny epsilon. Compute the gap at wide
    # precision so the default-context subtraction does not swallow the epsilon.
    with localcontext() as ctx:
        ctx.prec = 60
        shortfall = margin - realised  # > 0 only by a rounding-scale amount
    assert shortfall <= Decimal("1e-40")


@given(cost=_positive_cost, elasticity=_elastic, margin=_margin)
def test_recommended_price_at_least_cost(
    cost: Decimal, elasticity: Decimal, margin: Decimal
) -> None:
    out = _MODEL.compute(
        PriceRecommendationInputs(
            unit_cost=cost, price_elasticity=elasticity, min_margin=margin
        )
    )
    # A profit-maximising / floored price is always strictly above marginal cost.
    assert out.metrics.get("recommended_price") > cost


# -- MONOTONICITY invariants --


@given(elasticity=_elastic, margin=_margin, c1=_positive_cost, c2=_positive_cost)
def test_higher_cost_never_lowers_recommended_price(
    elasticity: Decimal, margin: Decimal, c1: Decimal, c2: Decimal
) -> None:
    lo, hi = sorted((c1, c2))
    price_lo = _MODEL.compute(
        PriceRecommendationInputs(
            unit_cost=lo, price_elasticity=elasticity, min_margin=margin
        )
    ).metrics.get("recommended_price")
    price_hi = _MODEL.compute(
        PriceRecommendationInputs(
            unit_cost=hi, price_elasticity=elasticity, min_margin=margin
        )
    ).metrics.get("recommended_price")
    # Both markup and floor scale linearly in cost, so the max does too.
    assert price_hi >= price_lo


@given(cost=_positive_cost, e1=_elastic, e2=_elastic)
def test_more_elastic_demand_never_raises_markup_price(
    cost: Decimal, e1: Decimal, e2: Decimal
) -> None:
    lo, hi = sorted((e1, e2))
    markup_lo = _MODEL.compute(
        PriceRecommendationInputs(unit_cost=cost, price_elasticity=lo)
    ).metrics.get("markup_price")
    markup_hi = _MODEL.compute(
        PriceRecommendationInputs(unit_cost=cost, price_elasticity=hi)
    ).metrics.get("markup_price")
    # factor = e/(e-1) is decreasing in e, so a more-elastic (larger) epsilon
    # yields a markup price that is never higher.
    assert markup_hi <= markup_lo


@given(cost=_positive_cost, elasticity=_elastic, m1=_margin, m2=_margin)
def test_higher_margin_floor_never_lowers_price(
    cost: Decimal, elasticity: Decimal, m1: Decimal, m2: Decimal
) -> None:
    lo, hi = sorted((m1, m2))
    price_lo = _MODEL.compute(
        PriceRecommendationInputs(
            unit_cost=cost, price_elasticity=elasticity, min_margin=lo
        )
    ).metrics.get("recommended_price")
    price_hi = _MODEL.compute(
        PriceRecommendationInputs(
            unit_cost=cost, price_elasticity=elasticity, min_margin=hi
        )
    ).metrics.get("recommended_price")
    assert price_hi >= price_lo  # a tighter floor only ever raises the price


# -- determinism: identical inputs => identical output across runs --


@given(cost=_positive_cost, elasticity=_elastic, margin=_margin)
def test_compute_is_deterministic(
    cost: Decimal, elasticity: Decimal, margin: Decimal
) -> None:
    ins = PriceRecommendationInputs(
        unit_cost=cost, price_elasticity=elasticity, min_margin=margin
    )
    assert _MODEL.compute(ins) == _MODEL.compute(ins)  # pure: no clock/randomness


# -- why == what: the explanation matches the recommendation EXACTLY --


@given(cost=_positive_cost, elasticity=_elastic, margin=_margin)
def test_action_restates_the_recommended_price(
    cost: Decimal, elasticity: Decimal, margin: Decimal
) -> None:
    out = _MODEL.compute(
        PriceRecommendationInputs(
            unit_cost=cost, price_elasticity=elasticity, min_margin=margin
        )
    )
    rec_price = out.metrics.get("recommended_price")
    # The "what" is literally the recommended number -- it cannot drift from the metric.
    assert out.recommendation.action == f"set_price={rec_price}"


@given(cost=_positive_cost, elasticity=_elastic, margin=_margin)
def test_primary_driver_names_the_binding_constraint(
    cost: Decimal, elasticity: Decimal, margin: Decimal
) -> None:
    out = _MODEL.compute(
        PriceRecommendationInputs(
            unit_cost=cost, price_elasticity=elasticity, min_margin=margin
        )
    )
    markup = out.metrics.get("markup_price")
    floor = out.metrics.get("floor_price")
    primary = out.recommendation.primary_driver()
    if floor > markup:
        # the floor set the price -> margin floor is the dominant driver, raising it.
        assert primary.label == "min_margin_floor"
        assert primary.direction.value == "raises"
        assert primary.contribution == margin  # exact contribution == the floor fraction
    else:
        # the elasticity markup set the price -> elasticity is the dominant driver.
        assert primary.label == "price_elasticity"
        assert primary.direction.value == "lowers"
        assert primary.contribution == -elasticity  # exact, signed
    # cost is always the second driver and always raises the price.
    cost_driver = out.recommendation.drivers[1]
    assert cost_driver.label == "unit_cost"
    assert cost_driver.direction.value == "raises"
    assert cost_driver.contribution == cost


# -- fail-closed cases (malformed / insufficient / contradictory inputs) --


@pytest.mark.parametrize(
    "cost,elasticity,margin,match",
    [
        ("0", "2", "0", "unit_cost"),  # zero cost: no meaningful markup
        ("-1", "2", "0", "unit_cost"),  # negative cost
        ("100", "1", "0", "price_elasticity"),  # epsilon == 1: factor diverges
        ("100", "0.5", "0", "price_elasticity"),  # epsilon < 1: inelastic, no optimum
        ("100", "-2", "0", "price_elasticity"),  # negative elasticity magnitude
        ("100", "2", "1", "min_margin"),  # margin == 1: floor divides by zero
        ("100", "2", "1.5", "min_margin"),  # margin > 1
        ("100", "2", "-0.1", "min_margin"),  # negative margin floor
    ],
)
def test_invalid_inputs_fail_closed(
    cost: str, elasticity: str, margin: str, match: str
) -> None:
    with pytest.raises(ValueError, match=match):
        _MODEL.compute(_inputs(cost, elasticity, margin))


@pytest.mark.parametrize("bad", ["NaN", "Infinity", "-Infinity"])
def test_non_finite_cost_is_refused(bad: str) -> None:
    with pytest.raises(ValueError, match="unit_cost"):
        _MODEL.compute(_inputs(bad, "2", "0"))


@pytest.mark.parametrize("bad", ["NaN", "Infinity"])
def test_non_finite_elasticity_is_refused(bad: str) -> None:
    with pytest.raises(ValueError, match="price_elasticity"):
        _MODEL.compute(_inputs("100", bad, "0"))


def test_kind_label_is_stable() -> None:
    assert _MODEL.kind == "price_recommendation"
