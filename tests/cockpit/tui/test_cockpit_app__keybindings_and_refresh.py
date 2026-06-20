"""cockpit TUI: every keybinding fires its real effect — r re-pulls data, q quits, ctrl+c bound."""

from __future__ import annotations

from autofirm.cockpit.tui.cockpit_app import CockpitApp
from autofirm.cockpit.tui.event_log_panel import EventLogPanel
from tests.cockpit.tui.synthetic_cockpit_read_model import (
    FakeEvent,
    populated_events,
    synthetic_model,
)

_QUIET = 1000.0  # large interval: the automatic tick never fires during the test


async def test_r_keybinding_repulls_mutated_data() -> None:
    model = synthetic_model(populated=True)
    app = CockpitApp(model, refresh_interval=_QUIET)
    async with app.run_test() as pilot:
        await pilot.pause()
        events = app.query_one(EventLogPanel)
        assert len(events.rows) == 2
        count_before = app.refresh_count

        # Mutate the source, then prove `r` actually re-pulls it (not a stale render).
        when = model.events[0].recorded_at
        added = FakeEvent(2, "kill_switch_observed", "watchdog", when)
        model.events = (*populated_events(), added)
        await pilot.press("r")
        await pilot.pause()

        assert app.refresh_count == count_before + 1
        assert len(events.rows) == 3
        assert ("2", "kill_switch_observed", "watchdog", "2026-06-19T12:30:00+00:00") in events.rows


async def test_q_keybinding_quits_the_app() -> None:
    app = CockpitApp(synthetic_model(), refresh_interval=_QUIET)
    async with app.run_test() as pilot:
        await pilot.pause()
        assert app.is_running
        await pilot.press("q")
        await pilot.pause()
    assert app.return_code == 0  # the app exited cleanly via the quit action


async def test_ctrl_c_is_bound_to_quit() -> None:
    bindings = {binding.key: binding.action for binding in CockpitApp.BINDINGS}
    assert bindings["ctrl+c"] == "quit"
    assert bindings["q"] == "quit"
    assert bindings["r"] == "refresh_now"
