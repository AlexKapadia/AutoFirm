"""provenance_read_port: the on-main in-memory trail satisfies the cockpit read port."""

from __future__ import annotations

from datetime import UTC, datetime

from autofirm.cockpit.adapters.provenance_read_port import ProvenanceReadable
from autofirm.comms.delivery_outcome_types import DeliveryStatus
from autofirm.frontdoor.front_door_provenance_trail import (
    FrontDoorProvenanceEntry,
    InMemoryFrontDoorProvenanceTrail,
)
from autofirm.frontdoor.routing_decision_contract import RoutingOutcome


def _entry() -> FrontDoorProvenanceEntry:
    return FrontDoorProvenanceEntry(
        correlation_id="c-1",
        requester_id="r-1",
        requester_display_name="Ada",
        routing_outcome=RoutingOutcome.ROUTED_TO_CAPABLE_ROLE,
        handler_role_id="role-1",
        handler_role_title="Lead",
        routing_reason="matched",
        delivery_status=DeliveryStatus.DELIVERED,
        recorded_at=datetime(2026, 6, 19, tzinfo=UTC),
    )


def test_in_memory_trail_satisfies_read_port_structurally() -> None:
    # The on-main InMemoryFrontDoorProvenanceTrail has entries(); it fits the port with
    # no on-main change (the cockpit owns the read seam the write-only Protocol lacks).
    trail: ProvenanceReadable = InMemoryFrontDoorProvenanceTrail()
    assert trail.entries() == ()


def test_port_exposes_recorded_entries() -> None:
    trail = InMemoryFrontDoorProvenanceTrail()
    trail.record(_entry())
    port: ProvenanceReadable = trail
    entries = port.entries()
    assert len(entries) == 1
    assert entries[0].correlation_id == "c-1"
