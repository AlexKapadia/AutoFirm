"""cockpit TUI: boot/mount every panel; populated / empty / error states render real data."""

from __future__ import annotations

from textual.widgets import Footer

from autofirm.cockpit.tui.cockpit_app import CockpitApp
from autofirm.cockpit.tui.event_log_panel import EventLogPanel
from autofirm.cockpit.tui.front_door_activity_panel import FrontDoorActivityPanel
from autofirm.cockpit.tui.kill_switch_status_panel import KillSwitchStatusPanel
from autofirm.cockpit.tui.org_snapshot_panel import OrgSnapshotPanel
from autofirm.cockpit.tui.spend_snapshot_panel import SpendSnapshotPanel
from tests.cockpit.tui.synthetic_cockpit_read_model import synthetic_model

# A large interval so the only refreshes are the initial one + any we trigger by hand.
_QUIET = 1000.0


async def test_app_boots_and_mounts_every_panel() -> None:
    app = CockpitApp(synthetic_model(), refresh_interval=_QUIET)
    async with app.run_test() as pilot:
        await pilot.pause()
        # Every panel + the header badge + the footer are present (not just "the app ran").
        assert app.query_one(KillSwitchStatusPanel) is not None
        assert app.query_one(OrgSnapshotPanel) is not None
        assert app.query_one(SpendSnapshotPanel) is not None
        assert app.query_one(FrontDoorActivityPanel) is not None
        assert app.query_one(EventLogPanel) is not None
        assert app.query_one(Footer) is not None


async def test_populated_state_renders_exact_rows_in_each_panel() -> None:
    app = CockpitApp(synthetic_model(populated=True), refresh_interval=_QUIET)
    async with app.run_test() as pilot:
        await pilot.pause()

        org = app.query_one(OrgSnapshotPanel)
        assert org.state == "populated"
        assert ("founder", "Founder", "—", "1") in org.rows
        assert ("coo", "Chief Operating Officer", "founder", "0") in org.rows
        assert "2 role(s)" in org.subtitle

        spend = app.query_one(SpendSnapshotPanel)
        assert spend.state == "populated"
        assert ("openai/gpt-4", "60.00 USD") in spend.rows
        assert "Total 60.00 USD" in spend.subtitle
        assert "band WARN_50" in spend.subtitle
        assert "ledger verified" in spend.subtitle

        front = app.query_one(FrontDoorActivityPanel)
        assert front.state == "populated"
        assert front.rows[0][0] == "req-001"
        assert front.rows[0][1] == "Jane Owner"
        assert front.rows[0][2] == "routed_to_capable_role"
        assert front.rows[0][4] == "delivered"

        events = app.query_one(EventLogPanel)
        assert events.state == "populated"
        assert ("0", "org_changed", "lifecycle", "2026-06-19T12:30:00+00:00") in events.rows
        assert ("1", "spend_recorded", "ledger", "2026-06-19T12:30:00+00:00") in events.rows


async def test_empty_state_shows_nothing_yet_message_and_does_not_crash() -> None:
    app = CockpitApp(synthetic_model(populated=False), refresh_interval=_QUIET)
    async with app.run_test() as pilot:
        await pilot.pause()

        org = app.query_one(OrgSnapshotPanel)
        assert org.state == "empty"
        assert org.rows == ()
        assert org.message == "No roles in the org yet."

        spend = app.query_one(SpendSnapshotPanel)
        assert spend.state == "empty"
        assert spend.message == "No spend recorded yet."
        # The subtitle still surfaces the zero total even with no rollup rows.
        assert "Total 0.00 USD" in spend.subtitle

        front = app.query_one(FrontDoorActivityPanel)
        assert front.state == "empty"
        assert front.message == "No front-door activity yet."

        events = app.query_one(EventLogPanel)
        assert events.state == "empty"
        assert events.message == "No events recorded yet."

        assert app.is_running  # the app survived an entirely empty company


async def test_error_state_shows_error_line_and_app_stays_alive() -> None:
    model = synthetic_model(populated=True)
    model.failing = {"org", "spend", "front_door", "kill_switch", "events"}
    app = CockpitApp(model, refresh_interval=_QUIET)
    async with app.run_test() as pilot:
        await pilot.pause()

        for panel_type in (
            OrgSnapshotPanel,
            SpendSnapshotPanel,
            FrontDoorActivityPanel,
            EventLogPanel,
        ):
            panel = app.query_one(panel_type)
            assert panel.state == "error"
            assert panel.message.startswith("unavailable:")

        kill = app.query_one(KillSwitchStatusPanel)
        assert kill.available is False
        assert "UNAVAILABLE" in kill.status_text
        assert kill.has_class("unavailable")

        assert app.is_running  # a raising accessor must never crash the cockpit


async def test_one_failing_source_does_not_take_down_healthy_panels() -> None:
    model = synthetic_model(populated=True)
    model.failing = {"spend"}  # only spend is down
    app = CockpitApp(model, refresh_interval=_QUIET)
    async with app.run_test() as pilot:
        await pilot.pause()
        assert app.query_one(SpendSnapshotPanel).state == "error"
        assert app.query_one(OrgSnapshotPanel).state == "populated"
        assert app.query_one(EventLogPanel).state == "populated"
        assert app.query_one(KillSwitchStatusPanel).available is True
