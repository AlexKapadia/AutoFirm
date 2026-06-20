"""cockpit app shell: mutation-hardening — defaults, bindings, layout ids, theme, error text.

Pins the constructor defaults (refresh interval + count), the exact keybinding metadata
(description / show / priority), the header/grid/title/badge widget ids, that the deliberate
theme stylesheet is actually loaded, the rendered app title, and that an empty-message exception
falls back to the exception *type name* rather than a blank error line.
"""

from __future__ import annotations

from textual.widgets import Static

from autofirm.cockpit.tui.cockpit_app import CockpitApp
from autofirm.cockpit.tui.kill_switch_status_panel import KillSwitchStatusPanel
from autofirm.cockpit.tui.org_snapshot_panel import OrgSnapshotPanel
from tests.cockpit.tui.synthetic_cockpit_read_model import synthetic_model

_QUIET = 1000.0


def test_constructor_defaults_interval_and_zero_count() -> None:
    default_app = CockpitApp(synthetic_model())
    assert default_app._refresh_interval == 2.0  # the fixed ~2s cadence default
    assert default_app.refresh_count == 0  # no refresh has run before mount
    custom_app = CockpitApp(synthetic_model(), refresh_interval=1000.0)
    assert custom_app._refresh_interval == 1000.0  # the injected interval flows through


def test_keybindings_carry_exact_metadata() -> None:
    by_key = {b.key: b for b in CockpitApp.BINDINGS}
    assert by_key["q"].description == "Quit"
    assert by_key["r"].description == "Refresh"
    assert by_key["ctrl+c"].description == "Quit"
    assert by_key["ctrl+c"].show is False  # ctrl+c is hidden from the footer
    assert by_key["ctrl+c"].priority is True  # ...but takes priority so it always quits


async def test_layout_ids_and_rendered_title() -> None:
    app = CockpitApp(synthetic_model(populated=True), refresh_interval=_QUIET)
    async with app.run_test() as pilot:
        await pilot.pause()
        assert app.query_one("#cockpit-header") is not None
        assert app.query_one("#cockpit-grid") is not None
        assert app.query_one("#kill-switch-status-panel", KillSwitchStatusPanel) is not None
        assert app.query_one("#cockpit-title", Static).render().plain == "AutoFirm Operator Cockpit"


async def test_theme_stylesheet_is_loaded() -> None:
    # The header docks to the top and the kill-switch colour encodes ARMED vs TRIPPED only when
    # the deliberate .tcss theme is actually loaded; CSS_PATH=None would drop both.
    armed = CockpitApp(synthetic_model(tripped=False), refresh_interval=_QUIET)
    tripped = CockpitApp(synthetic_model(tripped=True), refresh_interval=_QUIET)
    async with armed.run_test() as pilot:
        await pilot.pause()
        assert armed.query_one("#cockpit-header").styles.dock == "top"
        armed_color = armed.query_one(KillSwitchStatusPanel).styles.color
    async with tripped.run_test() as pilot:
        await pilot.pause()
        tripped_color = tripped.query_one(KillSwitchStatusPanel).styles.color
    assert armed_color != tripped_color  # success vs error colour from the loaded theme


async def test_empty_exception_message_falls_back_to_type_name() -> None:
    model = synthetic_model(populated=True)

    def _raise_blank() -> object:
        raise RuntimeError("")  # an exception whose str() is empty

    model.org_snapshot = _raise_blank  # type: ignore[method-assign]
    app = CockpitApp(model, refresh_interval=_QUIET)
    async with app.run_test() as pilot:
        await pilot.pause()
        # `str(exc) or type(exc).__name__` => "RuntimeError"; an `and` mutation would blank it.
        assert app.query_one(OrgSnapshotPanel).message == "unavailable: RuntimeError"
