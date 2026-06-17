"""Adversarial + property tests for the decision-model persistence seam.

Key invariants proven (argued from properties, never fitted to one example):
* The serialise -> deserialise round-trip is the IDENTITY on every valid output
  (LOSSLESS): every exact Decimal survives bit-for-bit, and driver ORDER is
  preserved (§3.11, why == what cannot drift).
* Serialisation is deterministic / canonical (byte-stable for equal outputs).
* Decimals are stored as STRINGS (never floats) -- high-precision values that a
  float would corrupt round-trip exactly.
* The persist -> load round-trip through a real, deterministic AgentMemoryLayer
  reconstructs the identical output, owner-scoped (§5.6).
* Corrupt / partial / wrong-schema payloads fail closed (§5.6).
Designed to KILL mutants on ``decision_model_persistence``.
"""

from decimal import Decimal

import pytest
from hypothesis import given
from hypothesis import strategies as st

from autofirm.decisions.decision_model_contract import (
    DecisionDriver,
    DecisionMetrics,
    DecisionOutput,
    DecisionRecommendation,
    DriverDirection,
)
from autofirm.decisions.decision_model_persistence import (
    deserialise_output,
    load_decision,
    persist_decision,
    serialise_output,
)
from autofirm.decisions.operational_runway_scenario_model import (
    OperationalRunwayInputs,
    OperationalRunwayScenarioModel,
)
from autofirm.decisions.price_recommendation_model import (
    PriceRecommendationInputs,
    PriceRecommendationModel,
)
from autofirm.memory.memory_access_errors import MemoryAccessError
from tests.memory.synthetic_memory_fixtures import make_layer

# -- Hypothesis strategies over arbitrary VALID outputs (synthetic only, §3.12) --

# Exact, finite, high-precision Decimals -- including values a float cannot hold
# losslessly, so the round-trip must use the string path or the test fails.
_exact_decimals = st.decimals(
    min_value=Decimal("-1e9"), max_value=Decimal("1e9"), allow_nan=False, allow_infinity=False,
    places=None,
)
_labels = st.text(
    alphabet=st.characters(min_codepoint=33, max_codepoint=126), min_size=1, max_size=12
)
_directions = st.sampled_from(list(DriverDirection))


@st.composite
def _drivers(draw: st.DrawFn) -> DecisionDriver:
    return DecisionDriver(
        label=draw(_labels), direction=draw(_directions), contribution=draw(_exact_decimals)
    )


@st.composite
def _outputs(draw: st.DrawFn) -> DecisionOutput:
    # Distinct metric keys (a dict cannot hold duplicate keys); preserve insertion.
    n_metrics = draw(st.integers(min_value=0, max_value=5))
    keys = draw(
        st.lists(_labels, min_size=n_metrics, max_size=n_metrics, unique=True)
    )
    values = {k: draw(_exact_decimals) for k in keys}
    drivers = tuple(draw(st.lists(_drivers(), min_size=1, max_size=5)))
    return DecisionOutput(
        metrics=DecisionMetrics(values=values),
        recommendation=DecisionRecommendation(
            action=draw(_labels), rationale=draw(_labels), drivers=drivers
        ),
    )


# -- LOSSLESS round-trip is the identity (the load-bearing property) --


@given(_outputs())
def test_serialise_deserialise_is_identity(output: DecisionOutput) -> None:
    # The frozen pydantic models compare by value, so equality proves a bit-for-bit
    # reconstruction of metrics, action, rationale, and the full driver tuple.
    assert deserialise_output(serialise_output(output)) == output


@given(_outputs())
def test_driver_order_is_preserved(output: DecisionOutput) -> None:
    restored = deserialise_output(serialise_output(output))
    original = output.recommendation.drivers
    rebuilt = restored.recommendation.drivers
    # Order-preserving: same length, same drivers, same positions (why == what).
    assert rebuilt == original
    # And specifically the primary (head) survives as the head -- a re-sort mutant dies.
    assert rebuilt[0] == original[0]


@given(_outputs())
def test_metric_keys_and_values_survive_exactly(output: DecisionOutput) -> None:
    restored = deserialise_output(serialise_output(output))
    assert restored.metrics.values == output.metrics.values  # exact Decimals, exact keys


def test_high_precision_decimal_survives_a_float_would_not() -> None:
    # 0.1 + 0.2 != 0.3 in float; this 30-digit value cannot be held by a float.
    # If the seam ever stored a float, this round-trip would corrupt -- it must not.
    precise = Decimal("0.123456789012345678901234567890")
    output = DecisionOutput(
        metrics=DecisionMetrics(values={"m": precise}),
        recommendation=DecisionRecommendation(
            action="a", rationale="r",
            drivers=(DecisionDriver(label="d", direction=DriverDirection.RAISES,
                                    contribution=precise),),
        ),
    )
    restored = deserialise_output(serialise_output(output))
    assert restored.metrics.get("m") == precise
    assert restored.recommendation.drivers[0].contribution == precise


# -- serialisation is deterministic / canonical (byte-stable) --


@given(_outputs())
def test_serialisation_is_canonical_and_repeatable(output: DecisionOutput) -> None:
    # sort_keys makes the JSON byte-stable, so re-serialising yields the same bytes
    # (auditable/diffable). Determinism: §3.11.
    assert serialise_output(output) == serialise_output(output)


def test_serialised_payload_carries_schema_version() -> None:
    output = DecisionOutput(
        metrics=DecisionMetrics(values={"m": Decimal("1")}),
        recommendation=DecisionRecommendation(
            action="a", rationale="r",
            drivers=(DecisionDriver(label="d", direction=DriverDirection.NEUTRAL,
                                    contribution=Decimal("0")),),
        ),
    )
    assert '"schema_version":1' in serialise_output(output).replace(" ", "")


# -- round-trip through a real, deterministic AgentMemoryLayer (owner-scoped) --


def test_persist_then_load_reconstructs_identical_output() -> None:
    layer = make_layer()
    model = PriceRecommendationModel(model_id="pr", role_id="pricing")
    output = model.compute(
        PriceRecommendationInputs(
            unit_cost=Decimal("100"), price_elasticity=Decimal("3"), min_margin=Decimal("0.4")
        )
    )
    memory_id = persist_decision(memory=layer, model=model, output=output)
    loaded = load_decision(memory=layer, model=model, memory_id=memory_id)
    assert loaded == output  # lossless through the real persistence surface


def test_persist_load_is_owner_scoped_and_tagged() -> None:
    layer = make_layer()
    model = OperationalRunwayScenarioModel(model_id="rw", role_id="ops")
    output = model.compute(
        OperationalRunwayInputs(
            starting_cash=Decimal("1000"), monthly_revenue=Decimal("0"),
            monthly_fixed_cost=Decimal("100"),
        )
    )
    memory_id = persist_decision(memory=layer, model=model, output=output)
    # The record is owned by the model's role and carries the model-family tags.
    record = layer.get(reader="ops", owner="ops", memory_id=memory_id)
    assert record.owner == "ops"
    assert f"decision_model:{model.kind}" in record.tags
    assert f"model_id:{model.model_id}" in record.tags


def test_load_under_a_different_owner_is_refused() -> None:
    # Fail-closed (§5.6): a model owned by another role cannot load these decisions.
    layer = make_layer()
    owner_model = OperationalRunwayScenarioModel(model_id="rw", role_id="ops")
    output = owner_model.compute(
        OperationalRunwayInputs(
            starting_cash=Decimal("1000"), monthly_revenue=Decimal("0"),
            monthly_fixed_cost=Decimal("100"),
        )
    )
    memory_id = persist_decision(memory=layer, model=owner_model, output=output)
    intruder = OperationalRunwayScenarioModel(model_id="rw", role_id="rival")
    # The intruder's role scopes the read to its OWN owner partition, which holds
    # no such record -> the store refuses with a typed access error (fail-closed).
    with pytest.raises(MemoryAccessError):
        load_decision(memory=layer, model=intruder, memory_id=memory_id)


# -- fail-closed: corrupt / partial / wrong-schema payloads --


@pytest.mark.parametrize(
    "content,match",
    [
        ("not json at all {", "valid JSON"),
        ("[1, 2, 3]", "JSON object"),  # top level is a list, not an object
        ('"a string"', "JSON object"),  # top level is a bare string
        ("123", "JSON object"),  # top level is a number
    ],
)
def test_malformed_json_is_refused(content: str, match: str) -> None:
    with pytest.raises(ValueError, match=match):
        deserialise_output(content)


def test_wrong_schema_version_is_refused() -> None:
    import json

    payload = json.dumps(
        {"schema_version": 99, "metrics": {}, "recommendation": {
            "action": "a", "rationale": "r", "drivers": []}}
    )
    with pytest.raises(ValueError, match="schema_version"):
        deserialise_output(payload)


def test_missing_schema_version_is_refused() -> None:
    import json

    payload = json.dumps(
        {"metrics": {}, "recommendation": {"action": "a", "rationale": "r", "drivers": []}}
    )
    with pytest.raises(ValueError, match="schema_version"):
        deserialise_output(payload)


@pytest.mark.parametrize(
    "payload",
    [
        # missing 'recommendation'
        {"schema_version": 1, "metrics": {}},
        # missing 'metrics'
        {"schema_version": 1, "recommendation": {"action": "a", "rationale": "r", "drivers": []}},
        # extra top-level key
        {"schema_version": 1, "metrics": {}, "recommendation": {
            "action": "a", "rationale": "r", "drivers": []}, "extra": 1},
    ],
)
def test_partial_or_extra_keys_are_refused(payload: dict[str, object]) -> None:
    import json

    with pytest.raises(ValueError, match="keys"):
        deserialise_output(json.dumps(payload))


@pytest.mark.parametrize(
    "metrics,rec",
    [
        ("not-a-dict", {"action": "a", "rationale": "r", "drivers": []}),  # metrics not object
        ({}, "not-a-dict"),  # recommendation not object
    ],
)
def test_non_object_sections_are_refused(metrics: object, rec: object) -> None:
    import json

    payload = json.dumps({"schema_version": 1, "metrics": metrics, "recommendation": rec})
    with pytest.raises(ValueError, match="must be JSON objects"):
        deserialise_output(payload)


def test_empty_drivers_payload_is_refused_by_contract() -> None:
    # A payload with a well-formed shape but ZERO drivers is rejected by the
    # recommendation contract (why == what: no driverless action), fail-closed.
    import json

    from pydantic import ValidationError

    payload = json.dumps(
        {"schema_version": 1, "metrics": {"m": "1"},
         "recommendation": {"action": "a", "rationale": "r", "drivers": []}}
    )
    with pytest.raises(ValidationError):
        deserialise_output(payload)
