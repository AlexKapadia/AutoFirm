"""Mutation-killing assertions for the cockpit event contract (CLAUDE.md §3.6).

Why this file exists
--------------------
The sibling ``test_cockpit_event_contract__fail_closed_validation.py`` asserts diagnostics
with ``pytest.raises(match=...)`` -- but ``match`` is a regex SUBSTRING search, so mutmut's
string-wrap mutant (``"msg"`` -> ``"XXmsgXX"``) still matches and SURVIVES. It also never
pins the enum ``.value`` strings, the ``frozen``/``slots`` dataclass flags, or the
``ensure_ascii=False`` serialisation flag. These tests close every one of those gaps with
EXACT assertions, so the corresponding mutants are killed rather than surviving.
"""

from __future__ import annotations

import dataclasses
import json
from datetime import UTC, datetime

import pytest

from autofirm.cockpit.eventlog.cockpit_event_contract import (
    CockpitEvent,
    CockpitEventDecodeError,
    CockpitEventKind,
)

_TS = datetime(2026, 6, 19, 9, 30, tzinfo=UTC)


def _valid_kwargs(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "seq": 0,
        "recorded_at": _TS,
        "kind": CockpitEventKind.ORG_CHANGED,
        "source": "org://engine",
        "payload": {"k": "v"},
    }
    base.update(overrides)
    return base


# --------------------------- enum .value strings (string-wrap) --------------------------- #


def test_event_kind_values_are_exact() -> None:
    # Each .value is the verbatim on-the-wire/audit token; a wrap mutant changes it.
    assert CockpitEventKind.FRONT_DOOR_REQUEST.value == "front_door_request"
    assert CockpitEventKind.ORG_CHANGED.value == "org_changed"
    assert CockpitEventKind.SPEND_RECORDED.value == "spend_recorded"
    assert CockpitEventKind.KILL_SWITCH_OBSERVED.value == "kill_switch_observed"


def test_event_kind_membership_and_order_are_exact() -> None:
    assert [m.value for m in CockpitEventKind] == [
        "front_door_request",
        "org_changed",
        "spend_recorded",
        "kill_switch_observed",
    ]


# --------------------------- frozen + slots flags --------------------------- #


def test_event_is_frozen_and_slotted() -> None:
    event = CockpitEvent(**_valid_kwargs())  # type: ignore[arg-type]
    with pytest.raises(dataclasses.FrozenInstanceError):
        event.seq = 99  # type: ignore[misc]  # frozen=True -> assignment refused
    assert not hasattr(event, "__dict__")  # slots=True -> no instance __dict__


# --------------------------- construction messages (EXACT equality) --------------------------- #


def test_construct_bool_seq_message_is_exact() -> None:
    with pytest.raises(TypeError) as ei:
        CockpitEvent(**_valid_kwargs(seq=True))  # type: ignore[arg-type]
    assert str(ei.value) == "seq must be an int"


def test_construct_negative_seq_message_is_exact() -> None:
    with pytest.raises(ValueError) as ei:
        CockpitEvent(**_valid_kwargs(seq=-1))  # type: ignore[arg-type]
    assert str(ei.value) == "seq must be >= 0"


def test_construct_non_kind_message_is_exact() -> None:
    with pytest.raises(TypeError) as ei:
        CockpitEvent(**_valid_kwargs(kind="org_changed"))  # type: ignore[arg-type]
    assert str(ei.value) == "kind must be a CockpitEventKind"


def test_construct_naive_timestamp_message_is_exact() -> None:
    with pytest.raises(ValueError) as ei:
        CockpitEvent(**_valid_kwargs(recorded_at=datetime(2026, 1, 1)))  # type: ignore[arg-type]
    assert str(ei.value) == "recorded_at must be timezone-aware"


def test_construct_blank_source_message_is_exact() -> None:
    with pytest.raises(ValueError) as ei:
        CockpitEvent(**_valid_kwargs(source="   "))  # type: ignore[arg-type]
    assert str(ei.value) == "source must be a non-empty provenance string"


def test_construct_non_string_payload_message_is_exact() -> None:
    with pytest.raises(TypeError) as ei:
        CockpitEvent(**_valid_kwargs(payload={"k": 1}))  # type: ignore[arg-type]
    assert str(ei.value) == "payload keys and values must both be str"


# --------------------- deterministic serialisation (ensure_ascii=False) --------------------- #


def test_to_ndjson_keeps_non_ascii_raw_not_escaped() -> None:
    # ensure_ascii=False keeps the literal character; the mutant (=True) emits \uXXXX.
    event = CockpitEvent(**_valid_kwargs(source="café://wösch", payload={"naïve": "résumé"}))  # type: ignore[arg-type]
    line = event.to_ndjson_line()
    assert "café://wösch" in line
    assert "résumé" in line
    assert "naïve" in line
    assert "\\u" not in line  # no JSON unicode escapes -> ensure_ascii was False


def test_to_ndjson_is_sorted_compact_and_byte_stable() -> None:
    event = CockpitEvent(**_valid_kwargs(seq=7, kind=CockpitEventKind.SPEND_RECORDED))  # type: ignore[arg-type]
    line = event.to_ndjson_line()
    # exact byte string: sorted keys, (",", ":") separators, kind serialised by .value.
    assert line == (
        '{"kind":"spend_recorded",'
        '"payload":{"k":"v"},'
        f'"recorded_at":"{_TS.isoformat()}",'
        '"seq":7,'
        '"source":"org://engine"}'
    )


# --------------------------- decode messages (EXACT equality) --------------------------- #


def _decode(obj: object) -> CockpitEvent:
    return CockpitEvent.from_ndjson_line(json.dumps(obj))


def _valid_obj() -> dict[str, object]:
    return {
        "seq": 7,
        "recorded_at": _TS.isoformat(),
        "kind": "spend_recorded",
        "source": "ledger://append",
        "payload": {"k": "v"},
    }


def test_decode_non_json_message_prefix_is_exact() -> None:
    with pytest.raises(CockpitEventDecodeError) as ei:
        CockpitEvent.from_ndjson_line("{not json")
    # The {exc} tail varies by Python build, but the literal prefix is pinned -> a
    # wrap mutant ("XXnot valid JSON: ...XX") starts with "XX" and fails this.
    assert str(ei.value).startswith("not valid JSON: ")
    assert not str(ei.value).startswith("XX")


def test_decode_non_object_message_is_exact() -> None:
    with pytest.raises(CockpitEventDecodeError) as ei:
        CockpitEvent.from_ndjson_line("[1, 2, 3]")
    assert str(ei.value) == "expected a JSON object, got list"


@pytest.mark.parametrize("field", ["seq", "recorded_at", "kind", "source", "payload"])
def test_decode_missing_field_message_is_exact(field: str) -> None:
    obj = _valid_obj()
    del obj[field]
    with pytest.raises(CockpitEventDecodeError) as ei:
        _decode(obj)
    assert str(ei.value) == f"missing required field {field!r}"


def test_decode_non_int_seq_message_is_exact() -> None:
    with pytest.raises(CockpitEventDecodeError) as ei:
        _decode({**_valid_obj(), "seq": "7"})
    assert str(ei.value) == "seq must be an int, got str"


def test_decode_non_string_timestamp_message_is_exact() -> None:
    with pytest.raises(CockpitEventDecodeError) as ei:
        _decode({**_valid_obj(), "recorded_at": 123})
    assert str(ei.value) == "recorded_at must be a str, got int"


def test_decode_non_iso_timestamp_message_is_exact() -> None:
    with pytest.raises(CockpitEventDecodeError) as ei:
        _decode({**_valid_obj(), "recorded_at": "not-a-date"})
    assert str(ei.value) == "recorded_at is not ISO-8601: 'not-a-date'"


def test_decode_non_string_kind_message_is_exact() -> None:
    with pytest.raises(CockpitEventDecodeError) as ei:
        _decode({**_valid_obj(), "kind": 5})
    assert str(ei.value) == "kind must be a str, got int"


def test_decode_unknown_kind_message_is_exact() -> None:
    with pytest.raises(CockpitEventDecodeError) as ei:
        _decode({**_valid_obj(), "kind": "no_such_kind"})
    assert str(ei.value) == "unknown event kind 'no_such_kind'"


def test_decode_non_string_source_message_is_exact() -> None:
    with pytest.raises(CockpitEventDecodeError) as ei:
        _decode({**_valid_obj(), "source": 9})
    assert str(ei.value) == "source must be a str, got int"


def test_decode_non_object_payload_message_is_exact() -> None:
    with pytest.raises(CockpitEventDecodeError) as ei:
        _decode({**_valid_obj(), "payload": [1, 2]})
    assert str(ei.value) == "payload must be an object, got list"


def test_decode_non_string_payload_value_message_is_exact() -> None:
    with pytest.raises(CockpitEventDecodeError) as ei:
        _decode({**_valid_obj(), "payload": {"k": 1}})
    assert str(ei.value) == "payload keys and values must both be strings"
