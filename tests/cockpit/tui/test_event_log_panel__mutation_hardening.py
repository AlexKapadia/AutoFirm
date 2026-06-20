"""event-log panel: mutation-hardening — exact title, four columns, panel id, and subtitle."""

from __future__ import annotations

from rich.table import Table
from textual.widgets import Static

from autofirm.cockpit.tui.cockpit_app import CockpitApp
from autofirm.cockpit.tui.event_log_panel import EventLogPanel
from tests.cockpit.tui.synthetic_cockpit_read_model import synthetic_model

_QUIET = 1000.0


async def test_event_log_panel_exact_title_columns_id_and_subtitle() -> None:
    app = CockpitApp(synthetic_model(populated=True), refresh_interval=_QUIET)
    async with app.run_test() as pilot:
        await pilot.pause()
        panel = app.query_one("#event-log-panel", EventLogPanel)
        assert panel.query_one(".panel-title", Static).render().plain == "Event log — recorded"
        table = getattr(panel.query_one(".panel-body", Static).render(), "_renderable", None)
        assert isinstance(table, Table)
        assert [c.header for c in table.columns] == ["Seq", "Kind", "Source", "When"]
        assert panel.subtitle == "2 event(s)"
