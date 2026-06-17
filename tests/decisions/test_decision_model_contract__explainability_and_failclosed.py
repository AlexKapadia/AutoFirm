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


# A label the contract ACCEPTS: non-empty AFTER its strip-whitespace normalisation
# (the _Label constraint strips then enforces min_length=1). Bare ``st.text`` is
# wrong here -- it yields whitespace-only strings (e.g. '\x85') that the contract
# legitimately REFUSES, so the model could never have built such a driver. We test
# the ordering invariant over labels the contract can actually hold.
_contract_label = st.text(
    alphabet=st.characters(min_codepoint=33, max_codepoint=126),  # printable, non-whitespace
    min_size=1,
    max_size=8,
)
# Bounded, exact, finite, and explicitly INCLUDING distinct magnitudes so a head
# driver can be made to carry a SMALLER contribution than a later one -- which is
# exactly the case that catches a contract that silently re-ranks the explanation.
_contract_contribution = st.decimals(
    min_value=Decimal("-1e6"), max_value=Decimal("1e6"), allow_nan=False, allow_infinity=False
)


@given(
    st.lists(
        st.tuples(_contract_label, _contract_contribution),
        min_size=1,
        max_size=6,
    )
)
def test_primary_driver_is_the_head_in_the_models_declared_order(
    spec: list[tuple[str, Decimal]],
) -> None:
    # The contract is ORDER-PRESERVING: the model declares its drivers
    # most-influential-first, and the contract MUST NOT silently re-rank them
    # (that would let the "why" drift from the "what" the model decided -- §3.11).
    drivers = tuple(
        DecisionDriver(label=lbl, direction=DriverDirection.RAISES, contribution=c)
        for lbl, c in spec
    )
    rec = DecisionRecommendation(action="a", rationale="r", drivers=drivers)
    primary = rec.primary_driver()
    # 1) primary() returns the SAME object the model put first -- not a copy, not a
    #    re-sorted pick. Kills mutants that return drivers[-1], max()/min(), or
    #    that reorder the tuple on construction.
    assert primary is drivers[0]
    # 2) Order is preserved end-to-end: the stored tuple is exactly as supplied,
    #    even when a LATER driver has a strictly larger |contribution| than the
    #    head. A contract that re-sorted by magnitude would fail this.
    assert rec.drivers == drivers


def test_primary_driver_stays_head_even_when_a_later_driver_is_larger() -> None:
    # Deterministic, hand-built witness of the order-preserving invariant: the
    # head's contribution (1) is strictly smaller in magnitude than a later
    # driver's (99), yet the primary is still the head the model declared.
    head = _driver(label="declared_primary", contribution="1")
    bigger_later = _driver(label="bigger_but_secondary", contribution="99")
    rec = DecisionRecommendation(action="a", rationale="r", drivers=(head, bigger_later))
    assert rec.primary_driver() is head
    assert rec.drivers == (head, bigger_later)  # never re-ranked by magnitude


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
