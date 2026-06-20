"""cockpit TUI: the kill-switch header badge shows ARMED vs TRIPPED, colour-coded and distinct."""

from __future__ import annotations

from autofirm.cockpit.tui.cockpit_app import CockpitApp
from autofirm.cockpit.tui.kill_switch_status_panel import KillSwitchStatusPanel
from tests.cockpit.tui.synthetic_cockpit_read_model import synthetic_model

_QUIET = 1000.0


async def test_untripped_epoch_shows_armed() -> None:
    app = CockpitApp(synthetic_model(tripped=False), refresh_interval=_QUIET)
    async with app.run_test() as pilot:
        await pilot.pause()
        kill = app.query_one(KillSwitchStatusPanel)
        assert kill.tripped is False
        assert kill.version == 3
        assert "ARMED" in kill.status_text
        assert "epoch 3" in kill.status_text
        assert kill.has_class("armed")
        assert not kill.has_class("tripped")


async def test_tripped_epoch_shows_tripped_distinctly() -> None:
    app = CockpitApp(synthetic_model(tripped=True), refresh_interval=_QUIET)
    async with app.run_test() as pilot:
        await pilot.pause()
        kill = app.query_one(KillSwitchStatusPanel)
        assert kill.tripped is True
        assert "TRIPPED" in kill.status_text
        assert "ARMED" not in kill.status_text
        assert kill.has_class("tripped")
        assert not kill.has_class("armed")


async def test_armed_and_tripped_texts_differ() -> None:
    armed = synthetic_model(tripped=False)
    tripped = synthetic_model(tripped=True)
    armed_app = CockpitApp(armed, refresh_interval=_QUIET)
    tripped_app = CockpitApp(tripped, refresh_interval=_QUIET)
    async with armed_app.run_test() as pilot:
        await pilot.pause()
        armed_text = armed_app.query_one(KillSwitchStatusPanel).status_text
    async with tripped_app.run_test() as pilot:
        await pilot.pause()
        tripped_text = tripped_app.query_one(KillSwitchStatusPanel).status_text
    assert armed_text != tripped_text
