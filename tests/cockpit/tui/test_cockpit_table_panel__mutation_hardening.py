"""cockpit base panel: mutation-hardening — exact defaults, table props, and state styles.

These drive the running panel via Pilot and assert the *exact* rendered artefact (render state,
fresh-panel defaults, the Rich table's construction flags + column overflow, and the empty/error
style spans) so a single flipped literal/flag/branch in :mod:`cockpit_table_panel` fails a test.
"""

from __future__ import annotations

from rich.table import Table
from textual.app import App, ComposeResult
from textual.widgets import Static

from autofirm.cockpit.tui.cockpit_app import CockpitApp
from autofirm.cockpit.tui.cockpit_table_panel import CockpitTablePanel
from autofirm.cockpit.tui.org_snapshot_panel import OrgSnapshotPanel
from tests.cockpit.tui.synthetic_cockpit_read_model import synthetic_model

_QUIET = 1000.0  # large interval: only the initial refresh (or none, for solo panels) fires


class _SoloPanelApp(App[None]):
    """Mounts a single panel and never refreshes it, exposing its pre-show defaults."""

    def __init__(self, panel: CockpitTablePanel) -> None:
        super().__init__()
        self._panel = panel

    def compose(self) -> ComposeResult:
        yield self._panel


async def test_fresh_panel_defaults_before_any_show() -> None:
    panel = OrgSnapshotPanel()
    async with _SoloPanelApp(panel).run_test() as pilot:
        await pilot.pause()
        assert panel.state == "empty"  # __init__ default state
        assert panel.rows == ()  # __init__ default rows (not None)
        assert panel.subtitle == ""  # __init__ default subtitle (not None / not "XX")
        assert panel.message == "No roles in the org yet."
        assert panel.has_class("cockpit-panel")  # base widget class hook
        # The titled Static carries the exact class and exact title text.
        title = panel.query_one(".panel-title", Static)
        assert title.render().plain == "Org — fleet tree"
        # The subtitle Static starts blank and hidden until set_subtitle reveals it.
        subtitle = panel.query_one(".panel-subtitle", Static)
        assert subtitle.render().plain == ""
        assert subtitle.display is False


async def test_populated_renders_a_real_table_with_exact_construction_flags() -> None:
    app = CockpitApp(synthetic_model(populated=True), refresh_interval=_QUIET)
    async with app.run_test() as pilot:
        await pilot.pause()
        panel = app.query_one(OrgSnapshotPanel)
        assert panel.state == "populated"
        assert panel.message == ""  # populated => the empty/error message is cleared
        body = panel.query_one(".panel-body", Static)
        table = getattr(body.render(), "_renderable", None)
        # Populated MUST render the Rich table (not fall through to a Text message).
        assert isinstance(table, Table)
        assert table.expand is True
        assert table.show_edge is False
        assert table.pad_edge is False
        assert table.columns[0].overflow == "fold"


async def test_empty_state_uses_dim_italic_style() -> None:
    app = CockpitApp(synthetic_model(populated=False), refresh_interval=_QUIET)
    async with app.run_test() as pilot:
        await pilot.pause()
        panel = app.query_one(OrgSnapshotPanel)
        assert panel.state == "empty"
        content = panel.query_one(".panel-body", Static).render()
        assert content.plain == "No roles in the org yet."
        assert content.spans[0].style == "dim italic"


async def test_error_state_uses_bold_red_style_and_clears_rows() -> None:
    model = synthetic_model(populated=True)
    model.failing = {"org"}
    app = CockpitApp(model, refresh_interval=_QUIET)
    async with app.run_test() as pilot:
        await pilot.pause()
        panel = app.query_one(OrgSnapshotPanel)
        assert panel.state == "error"
        assert panel.rows == ()  # show_error must clear any prior rows
        content = panel.query_one(".panel-body", Static).render()
        assert content.plain == "unavailable: org source unavailable"
        assert content.spans[0].style == "bold red"
