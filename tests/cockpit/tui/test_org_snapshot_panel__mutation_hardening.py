"""org panel: mutation-hardening — exact title, columns, panel id, and subtitle summary."""

from __future__ import annotations

from rich.table import Table
from textual.widgets import Static

from autofirm.cockpit.tui.cockpit_app import CockpitApp
from autofirm.cockpit.tui.org_snapshot_panel import OrgSnapshotPanel
from tests.cockpit.tui.synthetic_cockpit_read_model import synthetic_model

_QUIET = 1000.0


async def test_org_panel_exact_title_columns_id_and_subtitle() -> None:
    app = CockpitApp(synthetic_model(populated=True), refresh_interval=_QUIET)
    async with app.run_test() as pilot:
        await pilot.pause()
        panel = app.query_one("#org-snapshot-panel", OrgSnapshotPanel)
        assert panel.query_one(".panel-title", Static).render().plain == "Org — fleet tree"
        table = getattr(panel.query_one(".panel-body", Static).render(), "_renderable", None)
        assert isinstance(table, Table)
        headers = [c.header for c in table.columns]
        assert headers == ["Role", "Title", "Reports to", "Direct reports"]
        assert panel.subtitle == "2 role(s) · root Founder"
