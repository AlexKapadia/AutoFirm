"""Adversarial + property tests for the DecisionModel contract layer.

Targets the explainability binding (why == what) and the fail-closed boundaries
of the typed contracts. The defining invariant: a recommendation can NEVER exist
without at least one driver, and its primary driver is always the head of the
ordered driver tuple. Designed to KILL mutants on ``decision_model_contract``.
"""

from decimal import Decimal

import pytest
from hypothesis import given
from hypothesis import strategies as st
from pydantic import ValidationError

from autofirm.decisions.decision_model_contract import (
    DecisionDriver,
    DecisionInputs,
    DecisionMetrics,
    DecisionModel,
    DecisionOutput,
    DecisionRecommendation,
    DriverDirection,
)

# Hypothesis strategy: finite, bounded exact Decimals (no NaN/Inf, no overflow).
_finite_decimals = st.decimals(
    min_value=Decimal("-1e6"), max_value=Decimal("1e6"), allow_nan=False, allow_infinity=False
)


def _driver(label: str = "x", contribution: str = "1") -> DecisionDriver:
    return DecisionDriver(
        label=label, direction=DriverDirection.RAISES, contribution=Decimal(contribution)
    )


# -- fail-closed: a recommendation must carry at least one driver (why == what) --


def test_recommendation_with_no_drivers_is_refused() -> None:
    # The binding that makes the "why" provably match the "what": no driverless action.
    with pytest.raises(ValidationError):
        DecisionRecommendation(action="do_x", rationale="because", drivers=())


def test_recommendation_with_drivers_is_accepted_and_primary_is_head() -> None:
    d0, d1 = _driver("first"), _driver("second")
    rec = DecisionRecommendation(action="do_x", rationale="why", drivers=(d0, d1))
    assert rec.primary_driver() is d0  # primary is always the ordered head


@given(st.lists(st.text(min_size=1, max_size=8), min_size=1, max_size=6))
def test_primary_driver_is_always_first_for_any_nonempty_ordering(labels: list[str]) -> None:
    drivers = tuple(_driver(label=lbl) for lbl in labels)
    rec = DecisionRecommendation(action="a", rationale="r", drivers=drivers)
    # Invariant: primary driver == drivers[0] for ANY non-empty driver tuple.
    assert rec.primary_driver() == drivers[0]


# -- fail-closed: non-finite contributions/metrics are refused --


@pytest.mark.parametrize("bad", ["NaN", "Infinity", "-Infinity"])
def test_non_finite_driver_contribution_is_refused(bad: str) -> None:
    with pytest.raises(ValidationError):
        DecisionDriver(label="x", direction=DriverDirection.NEUTRAL, contribution=Decimal(bad))


@pytest.mark.parametrize("bad", ["NaN", "Infinity"])
def test_non_finite_metric_value_is_refused(bad: str) -> None:
    with pytest.raises(ValidationError):
        DecisionMetrics(values={"m": Decimal(bad)})


def test_blank_action_or_rationale_is_refused() -> None:
    d = _driver()
    with pytest.raises(ValidationError):
        DecisionRecommendation(action="   ", rationale="r", drivers=(d,))
    with pytest.raises(ValidationError):
        DecisionRecommendation(action="a", rationale="", drivers=(d,))


def test_blank_driver_label_is_refused() -> None:
    with pytest.raises(ValidationError):
        DecisionDriver(label="", direction=DriverDirection.RAISES, contribution=Decimal(1))


# -- metrics accessor is exact and fail-closed on unknown keys --


@given(_finite_decimals)
def test_metrics_get_returns_exact_stored_value(value: Decimal) -> None:
    metrics = DecisionMetrics(values={"k": value})
    assert metrics.get("k") == value  # exact: no float coercion in the round-trip


def test_metrics_get_unknown_key_raises_keyerror() -> None:
    with pytest.raises(KeyError):
        DecisionMetrics(values={"a": Decimal(1)}).get("absent")


# -- frozen contracts: outputs/recommendations cannot be mutated after build --


def test_decision_output_is_frozen() -> None:
    out = DecisionOutput(
        metrics=DecisionMetrics(values={"a": Decimal(1)}),
        recommendation=DecisionRecommendation(action="a", rationale="r", drivers=(_driver(),)),
    )
    with pytest.raises(ValidationError):
        out.recommendation = out.recommendation  # type: ignore[misc]  # frozen model


# -- DecisionModel base: fail-closed on blank ids, exposes ids/kind --


class _NullInputs(DecisionInputs):
    pass


class _ConstModel(DecisionModel[_NullInputs]):
    """Minimal concrete model used only to exercise the abstract base."""

    @property
    def kind(self) -> str:
        return "const"

    def compute(self, inputs: _NullInputs) -> DecisionOutput:
        return DecisionOutput(
            metrics=DecisionMetrics(values={"c": Decimal(0)}),
            recommendation=DecisionRecommendation(action="a", rationale="r", drivers=(_driver(),)),
        )


@pytest.mark.parametrize("blank", ["", "   ", "\t"])
def test_blank_model_id_is_refused(blank: str) -> None:
    with pytest.raises(ValueError, match="model_id"):
        _ConstModel(model_id=blank, role_id="role")


@pytest.mark.parametrize("blank", ["", "   ", "\t"])
def test_blank_role_id_is_refused(blank: str) -> None:
    with pytest.raises(ValueError, match="role_id"):
        _ConstModel(model_id="m", role_id=blank)


def test_model_ids_are_stripped_and_exposed() -> None:
    model = _ConstModel(model_id="  m1  ", role_id="  r1  ")
    assert model.model_id == "m1"
    assert model.role_id == "r1"
    assert model.kind == "const"
