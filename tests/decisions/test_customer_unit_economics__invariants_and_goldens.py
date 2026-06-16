"""Adversarial + property tests for the customer unit-economics model.

Key invariants proven (argued from properties, never fitted to one example):
* LTV is MONOTONE: higher churn never raises LTV; higher gross margin never
  lowers it; higher ARPA never lowers it.
* Worked golden examples are EXACT to the unit (zero numerical error, §3.11).
* The verdict's drivers always match the chosen action (why == what).
* Insufficient/contradictory inputs fail closed (§5.6).
Designed to KILL mutants on ``customer_unit_economics_model``.
"""

from decimal import Decimal

import pytest
from hypothesis import given
from hypothesis import strategies as st

from autofirm.decisions.customer_unit_economics_model import (
    CustomerUnitEconomicsInputs,
    CustomerUnitEconomicsModel,
)

_MODEL = CustomerUnitEconomicsModel(model_id="ue", role_id="analyst")

# Strategies over the valid domain (synthetic only -- no PII, §3.12).
_positive_money = st.decimals(
    min_value=Decimal("0.01"), max_value=Decimal("100000"), allow_nan=False, allow_infinity=False
)
_fraction = st.decimals(
    min_value=Decimal("0.0001"), max_value=Decimal("1"), allow_nan=False, allow_infinity=False
)


def _inputs(arpa: str, margin: str, churn: str, cac: str) -> CustomerUnitEconomicsInputs:
    return CustomerUnitEconomicsInputs(
        arpa=Decimal(arpa),
        gross_margin=Decimal(margin),
        monthly_churn_rate=Decimal(churn),
        cac=Decimal(cac),
    )


# -- worked golden examples: EXACT, zero numerical error --


def test_golden_healthy_example_is_exact() -> None:
    # ARPA=100, margin=0.8 -> arpa_margin=80; churn=0.05 -> lifetime=20 -> LTV=1600;
    # CAC=400 -> payback=5, ltv_cac=4 (>= 3 healthy).
    out = _MODEL.compute(_inputs("100", "0.8", "0.05", "400"))
    assert out.metrics.get("ltv") == Decimal("1600")
    assert out.metrics.get("payback_periods") == Decimal("5")
    assert out.metrics.get("ltv_cac") == Decimal("4")
    assert out.recommendation.action == "scale_acquisition"


def test_golden_breakeven_band_example_is_exact() -> None:
    # LTV:CAC exactly between 1 and 3 -> improve_efficiency.
    # ARPA=50 margin=1 churn=0.5 -> arpa_margin=50 lifetime=2 LTV=100; CAC=50 -> ltv_cac=2.
    out = _MODEL.compute(_inputs("50", "1", "0.5", "50"))
    assert out.metrics.get("ltv_cac") == Decimal("2")
    assert out.recommendation.action == "improve_efficiency"


def test_golden_unprofitable_example_is_exact() -> None:
    # ltv_cac < 1 -> halt. ARPA=10 margin=0.5 churn=0.5 -> arpa_margin=5 lifetime=2 LTV=10;
    # CAC=100 -> ltv_cac=0.1.
    out = _MODEL.compute(_inputs("10", "0.5", "0.5", "100"))
    assert out.metrics.get("ltv_cac") == Decimal("0.1")
    assert out.recommendation.action == "halt_and_fix_economics"


# -- boundary-exact verdict thresholds (on / just-over / just-under) --


def test_verdict_exactly_on_healthy_threshold_is_healthy() -> None:
    # ltv_cac == 3 exactly: arpa_margin=30 lifetime=1/0.1=10 LTV=300, CAC=100 -> 3.
    out = _MODEL.compute(_inputs("30", "1", "0.1", "100"))
    assert out.metrics.get("ltv_cac") == Decimal("3")
    assert out.recommendation.action == "scale_acquisition"  # >= threshold => healthy


def test_verdict_exactly_on_breakeven_floor_is_improve() -> None:
    # ltv_cac == 1 exactly: LTV == CAC.
    out = _MODEL.compute(_inputs("10", "1", "0.1", "100"))  # arpa_margin=10 lifetime=10 LTV=100
    assert out.metrics.get("ltv_cac") == Decimal("1")
    assert out.recommendation.action == "improve_efficiency"  # >= breakeven, < healthy


# -- MONOTONICITY invariants (the load-bearing properties) --


@given(arpa=_positive_money, margin=_fraction, cac=_positive_money, c1=_fraction, c2=_fraction)
def test_higher_churn_never_raises_ltv(
    arpa: Decimal, margin: Decimal, cac: Decimal, c1: Decimal, c2: Decimal
) -> None:
    lo, hi = sorted((c1, c2))
    ltv_lo = CustomerUnitEconomicsModel(model_id="m", role_id="r").compute(
        CustomerUnitEconomicsInputs(
            arpa=arpa, gross_margin=margin, monthly_churn_rate=lo, cac=cac
        )
    ).metrics.get("ltv")
    ltv_hi = CustomerUnitEconomicsModel(model_id="m", role_id="r").compute(
        CustomerUnitEconomicsInputs(
            arpa=arpa, gross_margin=margin, monthly_churn_rate=hi, cac=cac
        )
    ).metrics.get("ltv")
    # Invariant: more churn => shorter lifetime => LTV never increases.
    assert ltv_hi <= ltv_lo


@given(arpa=_positive_money, churn=_fraction, cac=_positive_money, m1=_fraction, m2=_fraction)
def test_higher_margin_never_lowers_ltv(
    arpa: Decimal, churn: Decimal, cac: Decimal, m1: Decimal, m2: Decimal
) -> None:
    lo, hi = sorted((m1, m2))
    ltv_lo = _MODEL.compute(
        CustomerUnitEconomicsInputs(
            arpa=arpa, gross_margin=lo, monthly_churn_rate=churn, cac=cac
        )
    ).metrics.get("ltv")
    ltv_hi = _MODEL.compute(
        CustomerUnitEconomicsInputs(
            arpa=arpa, gross_margin=hi, monthly_churn_rate=churn, cac=cac
        )
    ).metrics.get("ltv")
    assert ltv_hi >= ltv_lo  # higher margin never lowers LTV


@given(margin=_fraction, churn=_fraction, cac=_positive_money, a1=_positive_money, a2=_positive_money)
def test_higher_arpa_never_lowers_ltv(
    margin: Decimal, churn: Decimal, cac: Decimal, a1: Decimal, a2: Decimal
) -> None:
    lo, hi = sorted((a1, a2))
    ltv_lo = _MODEL.compute(
        CustomerUnitEconomicsInputs(
            arpa=lo, gross_margin=margin, monthly_churn_rate=churn, cac=cac
        )
    ).metrics.get("ltv")
    ltv_hi = _MODEL.compute(
        CustomerUnitEconomicsInputs(
            arpa=hi, gross_margin=margin, monthly_churn_rate=churn, cac=cac
        )
    ).metrics.get("ltv")
    assert ltv_hi >= ltv_lo


# -- determinism: identical inputs => identical output across runs --


@given(arpa=_positive_money, margin=_fraction, churn=_fraction, cac=_positive_money)
def test_compute_is_deterministic(
    arpa: Decimal, margin: Decimal, churn: Decimal, cac: Decimal
) -> None:
    ins = CustomerUnitEconomicsInputs(
        arpa=arpa, gross_margin=margin, monthly_churn_rate=churn, cac=cac
    )
    assert _MODEL.compute(ins) == _MODEL.compute(ins)  # pure: no clock/randomness


# -- why == what: the verdict's drivers are consistent with the chosen action --


@given(arpa=_positive_money, margin=_fraction, churn=_fraction, cac=_positive_money)
def test_explanation_matches_decision(
    arpa: Decimal, margin: Decimal, churn: Decimal, cac: Decimal
) -> None:
    out = _MODEL.compute(
        CustomerUnitEconomicsInputs(
            arpa=arpa, gross_margin=margin, monthly_churn_rate=churn, cac=cac
        )
    )
    ltv_cac = out.metrics.get("ltv_cac")
    primary = out.recommendation.primary_driver()
    assert primary.label == "ltv_cac_ratio"
    # The primary driver's exact contribution is the signed distance from the
    # healthy threshold -- it cannot drift from the computed ratio.
    assert primary.contribution == ltv_cac - Decimal("3")
    # Direction agrees with the action: a healthy verdict <=> ratio raises.
    if out.recommendation.action == "scale_acquisition":
        assert primary.direction.value == "raises"
    else:
        assert primary.direction.value == "lowers"


# -- fail-closed cases (insufficient / contradictory inputs) --


@pytest.mark.parametrize(
    "arpa,margin,churn,cac,match",
    [
        ("100", "0.8", "0", "400", "churn"),  # zero churn => infinite lifetime
        ("100", "0", "0.05", "400", "margin"),  # zero margin out of (0,1]
        ("100", "1.5", "0.05", "400", "margin"),  # margin > 1
        ("100", "0.8", "1.5", "400", "churn"),  # churn > 1
        ("-1", "0.8", "0.05", "400", "arpa"),  # negative revenue
        ("100", "0.8", "0.05", "0", "cac"),  # zero CAC => undefined ratio
        ("0", "0.8", "0.05", "400", "payback"),  # zero ARPA => undefined payback
    ],
)
def test_invalid_inputs_fail_closed(
    arpa: str, margin: str, churn: str, cac: str, match: str
) -> None:
    with pytest.raises(ValueError, match=match):
        _MODEL.compute(_inputs(arpa, margin, churn, cac))


def test_inverted_threshold_band_is_refused() -> None:
    # breakeven >= healthy is contradictory and refused fail-closed.
    with pytest.raises(ValueError, match="breakeven"):
        _MODEL.compute(
            CustomerUnitEconomicsInputs(
                arpa=Decimal("100"),
                gross_margin=Decimal("0.8"),
                monthly_churn_rate=Decimal("0.05"),
                cac=Decimal("400"),
                healthy_ltv_cac=Decimal("2"),
                breakeven_ltv_cac=Decimal("3"),
            )
        )
