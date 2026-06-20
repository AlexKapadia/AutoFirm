"""kill-switch badge: mutation-hardening — exact status text, classes, defaults, transitions.

The kill-switch is the cockpit's most safety-critical signal, so these assert the *exact* badge
text (label + spacing + epoch), the exact colour-class set for ARMED / TRIPPED / UNAVAILABLE, the
pre-first-refresh defaults, and that switching state correctly clears the previous state's class.
"""

from __future__ import annotations

from textual.app import App, ComposeResult

from autofirm.cockpit.tui.cockpit_app import CockpitApp
from autofirm.cockpit.tui.kill_switch_status_panel import KillSwitchStatusPanel
from tests.cockpit.tui.synthetic_cockpit_read_model import FakeEpoch, synthetic_model

_QUIET = 1000.0


class _SoloBadgeApp(App[None]):
    """Mounts the kill-switch badge and never refreshes it, exposing its pre-show defaults."""

    def __init__(self, badge: KillSwitchStatusPanel) -> None:
        super().__init__()
        self._badge = badge

    def compose(self) -> ComposeResult:
        yield self._badge


async def test_fresh_badge_defaults_before_any_refresh() -> None:
    badge = KillSwitchStatusPanel(panel_id="kill-switch-status-panel")
    async with _SoloBadgeApp(badge).run_test() as pilot:
        await pilot.pause()
        assert badge.tripped is False  # default, not True / not None
        assert badge.version == -1  # sentinel "no epoch observed yet"
        assert badge.available is False  # default, not True / not None
        assert badge.status_text == "KILL-SWITCH …"
        assert badge.render().plain == "KILL-SWITCH …"  # exact initial Static content
        assert badge.has_class("kill-switch")


async def test_armed_badge_exact_text_and_classes() -> None:
    app = CockpitApp(synthetic_model(tripped=False), refresh_interval=_QUIET)
    async with app.run_test() as pilot:
        await pilot.pause()
        badge = app.query_one(KillSwitchStatusPanel)
        assert badge.status_text == "KILL-SWITCH ARMED  ·  epoch 3"
        assert badge.render().plain == "KILL-SWITCH ARMED  ·  epoch 3"
        assert badge.has_class("armed")
        assert not badge.has_class("tripped")
        assert not badge.has_class("unavailable")  # show() must not mark the badge unavailable


async def test_tripped_badge_exact_text_and_classes() -> None:
    app = CockpitApp(synthetic_model(tripped=True), refresh_interval=_QUIET)
    async with app.run_test() as pilot:
        await pilot.pause()
        badge = app.query_one(KillSwitchStatusPanel)
        assert badge.status_text == "KILL-SWITCH TRIPPED  ·  epoch 3"
        assert badge.render().plain == "KILL-SWITCH TRIPPED  ·  epoch 3"
        assert badge.has_class("tripped")
        assert not badge.has_class("armed")
        assert not badge.has_class("unavailable")


async def test_unavailable_badge_exact_text_and_classes() -> None:
    model = synthetic_model(tripped=False)
    model.failing = {"kill_switch"}
    app = CockpitApp(model, refresh_interval=_QUIET)
    async with app.run_test() as pilot:
        await pilot.pause()
        badge = app.query_one(KillSwitchStatusPanel)
        assert badge.available is False
        assert badge.status_text == "KILL-SWITCH UNAVAILABLE  ·  kill_switch source unavailable"
        assert badge.has_class("unavailable")
        assert not badge.has_class("armed")
        assert not badge.has_class("tripped")


async def test_state_transitions_clear_the_previous_class() -> None:
    badge = KillSwitchStatusPanel(panel_id="kill-switch-status-panel")
    async with _SoloBadgeApp(badge).run_test() as pilot:
        await pilot.pause()
        # error -> armed must clear "unavailable".
        badge.show_error("boom")
        badge.show(FakeEpoch(version=1, tripped=False))
        assert badge.has_class("armed")
        assert not badge.has_class("unavailable")
        # armed -> error must clear "armed".
        badge.show_error("boom")
        assert badge.has_class("unavailable")
        assert not badge.has_class("armed")
        # tripped -> error must clear "tripped".
        badge.show(FakeEpoch(version=2, tripped=True))
        assert badge.has_class("tripped")
        badge.show_error("boom")
        assert not badge.has_class("tripped")
