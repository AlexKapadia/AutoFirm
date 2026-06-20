"""FrontDoorActivityView/-EntryView: immutability + faithful field carriage."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from autofirm.cockpit.readmodels.front_door_activity_view import (
    FrontDoorActivityEntryView,
    FrontDoorActivityView,
)

_TS = datetime(2026, 6, 19, 9, 30, tzinfo=UTC)


def _entry(correlation_id: str = "c-1") -> FrontDoorActivityEntryView:
    return FrontDoorActivityEntryView(
        correlation_id=correlation_id,
        requester_display="Ada Lovelace",
        routing_outcome="routed_to_capable_role",
        handler_role="FP&A Lead",
        delivery_status="delivered",
        timestamp=_TS,
    )


def test_entry_view_carries_every_field_exactly() -> None:
    entry = _entry()
    assert entry.correlation_id == "c-1"
    assert entry.requester_display == "Ada Lovelace"
    assert entry.routing_outcome == "routed_to_capable_role"
    assert entry.handler_role == "FP&A Lead"
    assert entry.delivery_status == "delivered"
    assert entry.timestamp == _TS


def test_entry_view_is_frozen() -> None:
    entry = _entry()
    with pytest.raises(AttributeError):
        entry.correlation_id = "mutated"  # type: ignore[misc]


def test_activity_view_preserves_entry_order() -> None:
    rows = (_entry("c-0"), _entry("c-1"), _entry("c-2"))
    view = FrontDoorActivityView(entries=rows)
    assert [e.correlation_id for e in view.entries] == ["c-0", "c-1", "c-2"]


def test_empty_activity_view_is_empty_tuple() -> None:
    assert FrontDoorActivityView(entries=()).entries == ()


def test_entry_view_equality_is_by_value() -> None:
    assert _entry("c-9") == _entry("c-9")
    assert _entry("c-9") != _entry("c-8")
