"""The front-door activity panel: renders recent human-request provenance rows.

What this does
--------------
Defines :class:`FrontDoorActivityPanel`, which maps a
:class:`~autofirm.cockpit.readmodels.front_door_activity_view.FrontDoorActivityView` into table
rows — one per recorded request, showing its correlation id, requester, routing outcome,
handling role, delivery status, and timestamp. No activity renders the empty-state message.

Why it exists / where it sits
-----------------------------
The operator's "what is the front door doing?" view. Sits in the tui layer; depends only on the
base panel and the front-door read-model DTO (no on-main import).
"""

from __future__ import annotations

from autofirm.cockpit.readmodels.front_door_activity_view import FrontDoorActivityView
from autofirm.cockpit.tui.cockpit_table_panel import CockpitTablePanel

__all__ = ["FrontDoorActivityPanel"]


class FrontDoorActivityPanel(CockpitTablePanel):
    """A panel that renders recent front-door provenance, one row per request."""

    def __init__(self) -> None:
        """Build the front-door panel with its columns and empty-state message."""
        super().__init__(
            title="Front door — recent activity",
            columns=("Correlation", "Requester", "Outcome", "Handler", "Delivery", "When"),
            empty_message="No front-door activity yet.",
            panel_id="front-door-activity-panel",
        )

    def show(self, view: FrontDoorActivityView) -> None:
        """Render every recorded activity row (or the empty message when there is none)."""
        rows = tuple(
            (
                entry.correlation_id,
                entry.requester_display,
                entry.routing_outcome,
                entry.handler_role,
                entry.delivery_status,
                entry.timestamp.isoformat(timespec="seconds"),
            )
            for entry in view.entries
        )
        self.set_subtitle(f"{len(view.entries)} request(s)")
        self.display_rows(rows)
