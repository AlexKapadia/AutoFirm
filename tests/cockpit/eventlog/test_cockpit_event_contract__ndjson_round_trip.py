"""CockpitEvent NDJSON round-trip: exact, deterministic, every-field equality."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta, timezone

import pytest

from autofirm.cockpit.eventlog.cockpit_event_contract import CockpitEvent, CockpitEventKind

_TS = datetime(2026, 6, 19, 9, 30, 15, 123456, tzinfo=UTC)


def _event(seq: int = 0, **overrides: object) -> CockpitEvent:
    base: dict[str, object] = {
        "seq": seq,
        "recorded_at": _TS,
        "kind": CockpitEventKind.FRONT_DOOR_REQUEST,
        "source": "frontdoor://dispatcher",
        "payload": {"correlation_id": "c-1", "handler": "FP&A Lead"},
    }
    base.update(overrides)
    return CockpitEvent(**base)  # type: ignore[arg-type]


@pytest.mark.parametrize("kind", list(CockpitEventKind))
def test_round_trip_is_exact_for_every_kind(kind: CockpitEventKind) -> None:
    event = _event(kind=kind)
    restored = CockpitEvent.from_ndjson_line(event.to_ndjson_line())
    assert restored == event
    assert restored.seq == event.seq
    assert restored.recorded_at == event.recorded_at
    assert restored.kind is kind
    assert restored.source == event.source
    assert dict(restored.payload) == dict(event.payload)


def test_round_trip_preserves_microseconds_and_offset() -> None:
    ts = datetime(2026, 1, 2, 3, 4, 5, 678901, tzinfo=timezone(timedelta(hours=5, minutes=30)))
    event = _event(recorded_at=ts)
    restored = CockpitEvent.from_ndjson_line(event.to_ndjson_line())
    assert restored.recorded_at == ts
    assert restored.recorded_at.utcoffset() == timedelta(hours=5, minutes=30)


def test_empty_payload_round_trips() -> None:
    event = _event(payload={})
    restored = CockpitEvent.from_ndjson_line(event.to_ndjson_line())
    assert dict(restored.payload) == {}


def test_encoding_is_a_single_line_with_no_newline() -> None:
    line = _event().to_ndjson_line()
    assert "\n" not in line


def test_encoding_is_deterministic_with_sorted_keys() -> None:
    # Same event -> byte-identical line, regardless of payload insertion order.
    a = _event(payload={"b": "2", "a": "1"})
    b = _event(payload={"a": "1", "b": "2"})
    assert a.to_ndjson_line() == b.to_ndjson_line()
    decoded = json.loads(a.to_ndjson_line())
    assert list(decoded.keys()) == sorted(decoded.keys())


def test_line_serialises_enum_by_value_not_name() -> None:
    decoded = json.loads(_event(kind=CockpitEventKind.SPEND_RECORDED).to_ndjson_line())
    assert decoded["kind"] == "spend_recorded"


def test_seq_and_payload_values_are_preserved_exactly() -> None:
    event = _event(seq=4321, payload={"k": "value-with-unicode-é"})
    restored = CockpitEvent.from_ndjson_line(event.to_ndjson_line())
    assert restored.seq == 4321
    assert restored.payload["k"] == "value-with-unicode-é"
