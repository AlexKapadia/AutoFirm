"""front_door_activity_adapter: maps every provenance entry, in order, read-only."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from autofirm.cockpit.adapters.front_door_activity_adapter import (
    build_front_door_activity_view,
)
from autofirm.comms.delivery_outcome_types import DeliveryStatus
from autofirm.frontdoor.front_door_provenance_trail import (
    FrontDoorProvenanceEntry,
    InMemoryFrontDoorProvenanceTrail,
)
from autofirm.frontdoor.routing_decision_contract import RoutingOutcome

_START = datetime(2026, 6, 19, 8, 0, 0, tzinfo=UTC)


def _entry(
    n: int,
    *,
    outcome: RoutingOutcome = RoutingOutcome.ROUTED_TO_CAPABLE_ROLE,
    delivery: DeliveryStatus = DeliveryStatus.DELIVERED,
) -> FrontDoorProvenanceEntry:
    return FrontDoorProvenanceEntry(
        correlation_id=f"corr-{n}",
        requester_id=f"req-{n}",
        requester_display_name=f"Requester {n}",
        routing_outcome=outcome,
        handler_role_id=f"role-{n}",
        handler_role_title=f"Title {n}",
        routing_reason="matched terms: finance",
        delivery_status=delivery,
        recorded_at=_START + timedelta(minutes=n),
    )


def test_empty_trail_yields_empty_view() -> None:
    trail = InMemoryFrontDoorProvenanceTrail()
    assert build_front_door_activity_view(trail).entries == ()


def test_maps_every_entry_in_recorded_order() -> None:
    trail = InMemoryFrontDoorProvenanceTrail()
    for n in range(3):
        trail.record(_entry(n))
    view = build_front_door_activity_view(trail)
    assert [row.correlation_id for row in view.entries] == ["corr-0", "corr-1", "corr-2"]


def test_each_field_is_flattened_faithfully() -> None:
    trail = InMemoryFrontDoorProvenanceTrail()
    trail.record(
        _entry(
            7,
            outcome=RoutingOutcome.TRIAGED_NO_CAPABLE_ROLE,
            delivery=DeliveryStatus.DEAD_LETTERED,
        )
    )
    row = build_front_door_activity_view(trail).entries[0]
    assert row.correlation_id == "corr-7"
    assert row.requester_display == "Requester 7"
    assert row.routing_outcome == "triaged_no_capable_role"  # enum .value, not name
    assert row.handler_role == "Title 7"  # the human-readable TITLE, not the id
    assert row.delivery_status == "dead_lettered"
    assert row.timestamp == _START + timedelta(minutes=7)


def test_failed_delivery_stays_visible_not_papered_over() -> None:
    trail = InMemoryFrontDoorProvenanceTrail()
    trail.record(_entry(0, delivery=DeliveryStatus.DEAD_LETTERED))
    trail.record(_entry(1, delivery=DeliveryStatus.DELIVERED))
    statuses = [row.delivery_status for row in build_front_door_activity_view(trail).entries]
    assert statuses == ["dead_lettered", "delivered"]


def test_adapter_does_not_mutate_the_trail() -> None:
    trail = InMemoryFrontDoorProvenanceTrail()
    trail.record(_entry(0))
    build_front_door_activity_view(trail)
    assert len(trail) == 1  # read-only: no entry added/removed
