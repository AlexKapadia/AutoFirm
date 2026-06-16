"""Persistence seam: file a model's DecisionOutput under its owning role's memory.

What this does
--------------
Bridges ``autofirm.decisions`` to ``autofirm.memory`` so a model's deterministic
result is durably remembered by the agent/role that owns the model, and can be
recalled and reconstructed later with zero numerical loss:

* :func:`serialise_output` / :func:`deserialise_output` -- a LOSSLESS JSON
  round-trip for a :class:`DecisionOutput`. Every exact :class:`~decimal.Decimal`
  is written as its canonical STRING (never a float), so a recalled metric or
  driver contribution is bit-for-bit the value that was computed (CLAUDE.md
  §3.11). The round-trip is the identity on every valid output.
* :func:`persist_decision` -- serialise a model's output and write it through the
  injected :class:`AgentMemoryLayer`, OWNED BY the model's ``role_id`` and tagged
  with the model kind + id, so an agent can later recall "my pricing decisions".
* :func:`load_decision` -- recall a persisted decision by memory id and rebuild
  the exact :class:`DecisionOutput`.

Why it exists / where it sits
-----------------------------
A thin, dependency-light seam (the decisions package depends on the memory
facade, never the reverse) so the model layer stays a pure deterministic core and
the memory layer stays the single persistence surface. It mirrors the memory
layer's owner-scoped writes: the model's owning role is the access key, exactly
as ``remember(owner=...)`` expects.

Security / compliance invariants upheld
---------------------------------------
* **Fail closed (§5.6):** deserialisation REFUSES content that is not a
  well-formed serialised output (missing/extra top-level keys, wrong shape) with
  a ``ValueError`` rather than silently constructing a partial/wrong output. The
  memory layer re-validates every stored field at its own boundary.
* **Determinism / exactness (§3.11):** Decimals serialise as strings, so no float
  rounding is ever introduced by the round-trip.
* **Owner scoping (§5.6):** the decision is written under the model's owning
  ``role_id``; the memory store enforces that the writer owns the target scope.
"""

from __future__ import annotations

import json
from decimal import Decimal
from typing import Any

from autofirm.decisions.decision_model_contract import (
    DecisionDriver,
    DecisionMetrics,
    DecisionModel,
    DecisionOutput,
    DecisionRecommendation,
    DriverDirection,
)
from autofirm.memory.agent_memory_layer import AgentMemoryLayer
from autofirm.memory.memory_record_contract import MaturityTier, MemoryKind

__all__ = [
    "deserialise_output",
    "load_decision",
    "persist_decision",
    "serialise_output",
]

# The single schema version stamped into every serialised payload, so a future
# format change can be detected and refused rather than mis-parsed (fail-closed).
_SCHEMA_VERSION = 1


def _driver_to_dict(driver: DecisionDriver) -> dict[str, str]:
    """Serialise one driver, contribution as an exact string (never a float)."""
    return {
        "label": driver.label,
        "direction": driver.direction.value,
        "contribution": str(driver.contribution),  # exact: Decimal -> canonical string
    }


def serialise_output(output: DecisionOutput) -> str:
    """Serialise a :class:`DecisionOutput` to a lossless JSON string.

    Every monetary/metric value is written as its exact Decimal STRING, so
    :func:`deserialise_output` reconstructs the identical output (§3.11).
    """
    payload: dict[str, Any] = {
        "schema_version": _SCHEMA_VERSION,
        "metrics": {name: str(value) for name, value in output.metrics.values.items()},
        "recommendation": {
            "action": output.recommendation.action,
            "rationale": output.recommendation.rationale,
            "drivers": [_driver_to_dict(d) for d in output.recommendation.drivers],
        },
    }
    # sort_keys keeps the serialisation canonical/deterministic for identical
    # outputs (so a re-serialise is byte-stable -- aids audit/diffing).
    return json.dumps(payload, sort_keys=True)


def deserialise_output(content: str) -> DecisionOutput:
    """Reconstruct a :class:`DecisionOutput` from :func:`serialise_output` output.

    Fail-closed: malformed JSON, a wrong schema version, or a missing/extra
    top-level key is REFUSED with ``ValueError`` rather than yielding a partial
    output (§5.6). Decimal strings are parsed back to exact ``Decimal``.
    """
    try:
        payload = json.loads(content)
    except json.JSONDecodeError as exc:  # fail-closed: not valid JSON
        raise ValueError(f"decision content is not valid JSON: {exc}") from exc
    if not isinstance(payload, dict):  # fail-closed: top level must be an object
        raise ValueError("decision content must be a JSON object")
    if payload.get("schema_version") != _SCHEMA_VERSION:
        # fail-closed: refuse an unknown format rather than guess its meaning.
        raise ValueError(
            f"unsupported decision schema_version {payload.get('schema_version')!r}"
        )
    expected_keys = {"schema_version", "metrics", "recommendation"}
    if set(payload) != expected_keys:  # fail-closed: unexpected/missing keys
        raise ValueError(f"decision payload keys {set(payload)} != {expected_keys}")

    raw_metrics = payload["metrics"]
    raw_rec = payload["recommendation"]
    if not isinstance(raw_metrics, dict) or not isinstance(raw_rec, dict):
        raise ValueError("metrics and recommendation must be JSON objects")  # fail-closed

    metrics = DecisionMetrics(
        values={name: Decimal(str(value)) for name, value in raw_metrics.items()}
    )
    drivers = tuple(
        DecisionDriver(
            label=d["label"],
            direction=DriverDirection(d["direction"]),
            contribution=Decimal(str(d["contribution"])),
        )
        for d in raw_rec["drivers"]
    )
    recommendation = DecisionRecommendation(
        action=raw_rec["action"],
        rationale=raw_rec["rationale"],
        drivers=drivers,
    )
    return DecisionOutput(metrics=metrics, recommendation=recommendation)


def persist_decision(
    *,
    memory: AgentMemoryLayer,
    model: DecisionModel[Any],
    output: DecisionOutput,
) -> str:
    """Remember ``output`` under ``model``'s owning role; return the new memory id.

    The decision is written as SEMANTIC memory owned by the model's ``role_id``
    (the access key), tagged with the model kind + id so the owner can later
    recall its decisions of a given family. The store enforces that the writer
    owns the scope (fail-closed, §5.6).
    """
    record = memory.remember(
        written_by=model.role_id,
        owner=model.role_id,  # owner-scoped: the model's role owns its decisions
        content=serialise_output(output),  # untrusted at the memory boundary; re-validated there
        kind=MemoryKind.SEMANTIC,  # a durable, recalled fact about the business
        tier=MaturityTier.STORAGE,
        tags=(f"decision_model:{model.kind}", f"model_id:{model.model_id}"),
    )
    return record.memory_id


def load_decision(
    *,
    memory: AgentMemoryLayer,
    model: DecisionModel[Any],
    memory_id: str,
) -> DecisionOutput:
    """Recall and reconstruct a persisted :class:`DecisionOutput` for ``model``.

    PS-scoped read: the model's owning ``role_id`` is both reader and owner, so a
    role can only load its own decisions (cross-owner private reads are refused in
    the data layer, §5.6). The reconstruction is exact (§3.11).
    """
    record = memory.get(reader=model.role_id, owner=model.role_id, memory_id=memory_id)
    return deserialise_output(record.content)
