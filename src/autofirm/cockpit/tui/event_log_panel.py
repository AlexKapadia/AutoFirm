"""The event-log panel: renders the recorded cockpit events (seq, kind, source, when).

What this does
--------------
Defines :class:`EventLogPanel`, which maps the recorded cockpit events (each an
:class:`~autofirm.cockpit.tui.cockpit_read_model_protocol.EventLike`) into table rows — one per
event, showing its sequence number, kind, source, and timestamp. An empty log renders the
empty-state message.

Why it exists / where it sits
-----------------------------
The operator's audit-trail view. It renders events via the read-only ``EventLike`` attributes
(``seq`` / ``kind`` / ``source`` / ``recorded_at``) so the tui never imports the event-log
module itself — keeping the import-linter fence intact (CLAUDE.md §3.10). Sits in the tui layer.
"""

from __future__ import annotations

from autofirm.cockpit.tui.cockpit_read_model_protocol import EventLike
from autofirm.cockpit.tui.cockpit_table_panel import CockpitTablePanel

__all__ = ["EventLogPanel"]


class EventLogPanel(CockpitTablePanel):
    """A panel that renders the recorded cockpit events, newest-last (append order)."""

    def __init__(self) -> None:
        """Build the event-log panel with its columns and empty-state message."""
        super().__init__(
            title="Event log — recorded",
            columns=("Seq", "Kind", "Source", "When"),
            empty_message="No events recorded yet.",
            panel_id="event-log-panel",
        )

    def show(self, events: tuple[EventLike, ...]) -> None:
        """Render every recorded event in order (or the empty message when there are none)."""
        rows = tuple(
            (
                str(event.seq),
                str(event.kind),
                event.source,
                event.recorded_at.isoformat(timespec="seconds"),
            )
            for event in events
        )
        self.set_subtitle(f"{len(events)} event(s)")
        self.display_rows(rows)
