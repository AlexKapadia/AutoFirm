"""CockpitEvent fail-closed construction + every decode-rejection branch."""

from __future__ import annotations

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


# --------------------------- construction (fail-closed) --------------------------- #


def test_negative_seq_is_refused() -> None:
    with pytest.raises(ValueError, match="seq must be >= 0"):
        CockpitEvent(**_valid_kwargs(seq=-1))  # type: ignore[arg-type]


def test_zero_seq_is_accepted_boundary() -> None:
    assert CockpitEvent(**_valid_kwargs(seq=0)).seq == 0  # type: ignore[arg-type]


def test_bool_seq_is_refused_even_though_bool_is_an_int() -> None:
    with pytest.raises(TypeError, match="seq must be an int"):
        CockpitEvent(**_valid_kwargs(seq=True))  # type: ignore[arg-type]


def test_non_int_seq_is_refused() -> None:
    with pytest.raises(TypeError, match="seq must be an int"):
        CockpitEvent(**_valid_kwargs(seq="0"))  # type: ignore[arg-type]


def test_non_kind_is_refused() -> None:
    with pytest.raises(TypeError, match="kind must be a CockpitEventKind"):
        CockpitEvent(**_valid_kwargs(kind="front_door_request"))  # type: ignore[arg-type]


def test_naive_timestamp_is_refused() -> None:
    with pytest.raises(ValueError, match="recorded_at must be timezone-aware"):
        CockpitEvent(**_valid_kwargs(recorded_at=datetime(2026, 1, 1, 0, 0)))  # type: ignore[arg-type]


@pytest.mark.parametrize("blank", ["", "   ", "\t"])
def test_blank_source_is_refused(blank: str) -> None:
    with pytest.raises(ValueError, match="source must be a non-empty"):
        CockpitEvent(**_valid_kwargs(source=blank))  # type: ignore[arg-type]


def test_non_string_payload_key_is_refused() -> None:
    with pytest.raises(TypeError, match="payload keys and values must both be str"):
        CockpitEvent(**_valid_kwargs(payload={1: "v"}))  # type: ignore[arg-type]


def test_non_string_payload_value_is_refused() -> None:
    with pytest.raises(TypeError, match="payload keys and values must both be str"):
        CockpitEvent(**_valid_kwargs(payload={"k": 2}))  # type: ignore[arg-type]


def test_payload_is_frozen_after_construction() -> None:
    event = CockpitEvent(**_valid_kwargs())  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        event.payload["x"] = "y"  # type: ignore[index]


# --------------------------- decode (fail-closed) --------------------------- #


def _valid_obj() -> dict[str, object]:
    return {
        "seq": 7,
        "recorded_at": _TS.isoformat(),
        "kind": "spend_recorded",
        "source": "ledger://append",
        "payload": {"k": "v"},
    }


def _decode(obj: object) -> CockpitEvent:
    return CockpitEvent.from_ndjson_line(json.dumps(obj))


def test_decode_rejects_non_json() -> None:
    with pytest.raises(CockpitEventDecodeError, match="not valid JSON"):
        CockpitEvent.from_ndjson_line("{not json")


def test_decode_rejects_blank_line() -> None:
    with pytest.raises(CockpitEventDecodeError, match="not valid JSON"):
        CockpitEvent.from_ndjson_line("")


def test_decode_rejects_non_object_json() -> None:
    with pytest.raises(CockpitEventDecodeError, match="expected a JSON object"):
        CockpitEvent.from_ndjson_line("[1, 2, 3]")


@pytest.mark.parametrize("field", ["seq", "recorded_at", "kind", "source", "payload"])
def test_decode_rejects_missing_required_field(field: str) -> None:
    obj = _valid_obj()
    del obj[field]
    with pytest.raises(CockpitEventDecodeError, match=f"missing required field '{field}'"):
        _decode(obj)


def test_decode_rejects_non_int_seq() -> None:
    with pytest.raises(CockpitEventDecodeError, match="seq must be an int"):
        _decode({**_valid_obj(), "seq": "7"})


def test_decode_rejects_bool_seq() -> None:
    with pytest.raises(CockpitEventDecodeError, match="seq must be an int"):
        _decode({**_valid_obj(), "seq": True})


def test_decode_rejects_non_string_timestamp() -> None:
    with pytest.raises(CockpitEventDecodeError, match="recorded_at must be a str"):
        _decode({**_valid_obj(), "recorded_at": 123})


def test_decode_rejects_non_iso_timestamp() -> None:
    with pytest.raises(CockpitEventDecodeError, match="not ISO-8601"):
        _decode({**_valid_obj(), "recorded_at": "not-a-date"})


def test_decode_rejects_non_string_kind() -> None:
    with pytest.raises(CockpitEventDecodeError, match="kind must be a str"):
        _decode({**_valid_obj(), "kind": 5})


def test_decode_rejects_unknown_kind() -> None:
    with pytest.raises(CockpitEventDecodeError, match="unknown event kind"):
        _decode({**_valid_obj(), "kind": "no_such_kind"})


def test_decode_rejects_non_string_source() -> None:
    with pytest.raises(CockpitEventDecodeError, match="source must be a str"):
        _decode({**_valid_obj(), "source": 9})


def test_decode_rejects_non_object_payload() -> None:
    with pytest.raises(CockpitEventDecodeError, match="payload must be an object"):
        _decode({**_valid_obj(), "payload": [1, 2]})


def test_decode_rejects_non_string_payload_value() -> None:
    with pytest.raises(CockpitEventDecodeError, match="payload keys and values must both be"):
        _decode({**_valid_obj(), "payload": {"k": 1}})
