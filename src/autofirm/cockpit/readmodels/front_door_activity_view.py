"""The front-door activity read-model: a snapshot of recent human-request provenance.

What this does
--------------
Defines :class:`FrontDoorActivityEntryView` (one immutable, presentation-ready row of how a
single human request was handled) and :class:`FrontDoorActivityView` (the ordered tuple of
those rows). These are the cockpit-facing projection of the on-main
:class:`~autofirm.frontdoor.front_door_provenance_trail.FrontDoorProvenanceEntry`, built by
:mod:`~autofirm.cockpit.adapters.front_door_activity_adapter` — flattened to plain strings so
the UI binds a stable shape and never touches an on-main enum or domain object.

Why it exists / where it sits
-----------------------------
The operator's "what is the front door doing?" panel reads this view. Keeping it a pure,
string-only DTO (no on-main import) is what lets the front-door contract be re-wired without
touching the cockpit UI. Sits in the read-model layer; depends only on stdlib.

Security / compliance invariants upheld
---------------------------------------
* **Read-only projection (CLAUDE.md §3.2):** an entry view is an immutable copy of audit
  fields; it carries no handle back into the live trail.
* **Faithful provenance:** the view surfaces the *recorded* routing outcome, handler, and
  delivery status verbatim — a failed/triaged request stays visible as such, never papered
  over.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

__all__ = ["FrontDoorActivityEntryView", "FrontDoorActivityView"]


@dataclass(frozen=True, slots=True)
class FrontDoorActivityEntryView:
    """One presentation-ready row of front-door provenance (immutable, string-flattened).

    Attributes:
        correlation_id: The id threading this request to its decision and response.
        requester_display: The human-readable name of who asked.
        routing_outcome: The recorded routing outcome value (e.g. ``"routed_to_capable_role"``).
        handler_role: The human-readable title of the role that handled the request.
        delivery_status: The recorded internal-delivery outcome value (e.g. ``"delivered"``).
        timestamp: When the request's provenance was recorded (tz-aware, injected clock).

    Note:
        The on-main ``FrontDoorProvenanceEntry`` carries no "channel" field, so this view
        surfaces ``delivery_status`` (a real recorded field) rather than inventing one.
    """

    correlation_id: str
    requester_display: str
    routing_outcome: str
    handler_role: str
    delivery_status: str
    timestamp: datetime


@dataclass(frozen=True, slots=True)
class FrontDoorActivityView:
    """An ordered, immutable snapshot of recent front-door activity rows.

    Attributes:
        entries: The activity rows in the trail's recorded (append) order — newest-last,
            matching the append-only provenance trail so the audit order is preserved.
    """

    entries: tuple[FrontDoorActivityEntryView, ...]
