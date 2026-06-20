"""The front-door activity adapter: project the provenance trail into a cockpit read-model.

What this does
--------------
Defines :func:`build_front_door_activity_view`, which reads a :class:`ProvenanceReadable`
(the cockpit-owned read seam over the on-main front-door provenance trail) and maps each
:class:`~autofirm.frontdoor.front_door_provenance_trail.FrontDoorProvenanceEntry` into a
flattened, string-only flattened ``FrontDoorActivityEntryView`` (see
:mod:`~autofirm.cockpit.readmodels.front_door_activity_view`), preserving the trail's append
order. Read-only: it never records into or mutates the trail.

Why it exists / where it sits
-----------------------------
This is the seam that turns the on-main audit trail into the cockpit's "front-door activity"
panel data. Sits in the adapters layer (the only cockpit layer allowed to touch on-main
domain types) and produces a pure read-model the UI binds.

Security / compliance invariants upheld
---------------------------------------
* **Read-only projection (CLAUDE.md §3.2):** the adapter only calls ``entries()`` and copies
  fields into immutable views — it holds no handle that could mutate the live trail.
* **Faithful provenance:** the recorded routing outcome, handler title, and delivery status
  are surfaced verbatim, so a triaged/failed request stays visible as such.
"""

from __future__ import annotations

from autofirm.cockpit.adapters.provenance_read_port import ProvenanceReadable
from autofirm.cockpit.readmodels.front_door_activity_view import (
    FrontDoorActivityEntryView,
    FrontDoorActivityView,
)

__all__ = ["build_front_door_activity_view"]


def build_front_door_activity_view(trail: ProvenanceReadable) -> FrontDoorActivityView:
    """Project a provenance trail into an immutable :class:`FrontDoorActivityView` (read-only).

    Maps every recorded entry, in append order, into a flattened view row.

    Args:
        trail: Any object satisfying :class:`ProvenanceReadable` (e.g. the on-main
            ``InMemoryFrontDoorProvenanceTrail``).

    Returns:
        A :class:`FrontDoorActivityView` whose ``entries`` mirror the trail in order.
    """
    rows = tuple(
        FrontDoorActivityEntryView(
            correlation_id=entry.correlation_id,
            requester_display=entry.requester_display_name,
            routing_outcome=entry.routing_outcome.value,
            handler_role=entry.handler_role_title,
            delivery_status=entry.delivery_status.value,
            timestamp=entry.recorded_at,
        )
        for entry in trail.entries()
    )
    return FrontDoorActivityView(entries=rows)
