"""The cockpit Textual application: header + panel grid + footer, on a fixed refresh tick.

What this does
--------------
Defines :class:`CockpitApp`, the Textual ``App`` the operator runs. It composes a header (title
+ the prominent kill-switch badge), a 2x2 grid of the four read-only panels (org, spend,
front-door, event-log), and a footer of the active keybindings. A :class:`CockpitReadModel` is
INJECTED via the constructor (never constructed ambiently), so a Pilot test drives the running
app with a synthetic stand-in. On a fixed ~2s tick (and on the ``r`` keybinding) it re-pulls
every snapshot in one coalesced refresh; a snapshot accessor that raises is caught per-panel so
one bad source can never crash the whole cockpit.

Why it exists / where it sits
-----------------------------
This is the first runnable cockpit surface — the read-only window onto the live company
(cockpit-research/PLAN.md §5). It holds NO business logic: it renders value types and translates
keypresses to actions, with all logic below it in composition/core. Sits at the top of the tui
layer; depends only on Textual, the panels, and the read-model protocols — never on the
composition root, the adapters, the event log, or an on-main domain package.

Security / compliance invariants upheld
---------------------------------------
* **Read-only projection (CLAUDE.md §3.2):** every action only re-reads snapshots; the app
  exposes no surface that mutates on-main state or flips the kill-switch.
* **Fail-soft refresh (§3.14):** a raising accessor surfaces as a per-panel error line, never an
  app crash — the cockpit keeps observing the sources that are still healthy.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import ClassVar, TypeVar

from textual.app import App, ComposeResult
from textual.binding import Binding, BindingType
from textual.containers import Grid, Horizontal
from textual.widgets import Footer, Static

from autofirm.cockpit.tui.cockpit_read_model_protocol import (
    CockpitReadModel,
    SupportsErrorDisplay,
)
from autofirm.cockpit.tui.event_log_panel import EventLogPanel
from autofirm.cockpit.tui.front_door_activity_panel import FrontDoorActivityPanel
from autofirm.cockpit.tui.kill_switch_status_panel import KillSwitchStatusPanel
from autofirm.cockpit.tui.org_snapshot_panel import OrgSnapshotPanel
from autofirm.cockpit.tui.spend_snapshot_panel import SpendSnapshotPanel

__all__ = ["CockpitApp"]

_T = TypeVar("_T")

# The fixed cadence (seconds) at which every snapshot is re-pulled in one coalesced refresh.
_DEFAULT_REFRESH_INTERVAL = 2.0


class CockpitApp(App[None]):
    """The read-only operator cockpit: a header badge, a panel grid, and a refresh tick."""

    CSS_PATH = "cockpit_theme.tcss"
    TITLE = "AutoFirm Operator Cockpit"
    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("q", "quit", "Quit"),
        Binding("ctrl+c", "quit", "Quit", show=False, priority=True),
        Binding("r", "refresh_now", "Refresh"),
    ]

    def __init__(
        self,
        read_model: CockpitReadModel,
        *,
        refresh_interval: float = _DEFAULT_REFRESH_INTERVAL,
    ) -> None:
        """Construct the app around an injected read model (no ambient construction).

        Args:
            read_model: The read-only snapshot source the panels render each tick.
            refresh_interval: Seconds between coalesced refreshes (the fixed tick).
        """
        super().__init__()
        self._read_model = read_model
        self._refresh_interval = refresh_interval
        self._refresh_count = 0
        self._kill_switch_panel = KillSwitchStatusPanel(panel_id="kill-switch-status-panel")
        self._org_panel = OrgSnapshotPanel()
        self._spend_panel = SpendSnapshotPanel()
        self._front_door_panel = FrontDoorActivityPanel()
        self._event_log_panel = EventLogPanel()

    def compose(self) -> ComposeResult:
        """Lay out the header (title + kill-switch), the 2x2 panel grid, and the footer."""
        with Horizontal(id="cockpit-header"):
            yield Static(self.TITLE, id="cockpit-title")
            yield self._kill_switch_panel
        with Grid(id="cockpit-grid"):
            yield self._org_panel
            yield self._spend_panel
            yield self._front_door_panel
            yield self._event_log_panel
        yield Footer()

    def on_mount(self) -> None:
        """Start the fixed refresh tick and paint the first snapshot once mounted."""
        self.set_interval(self._refresh_interval, self.refresh_snapshots)
        self.call_after_refresh(self.refresh_snapshots)

    def action_refresh_now(self) -> None:
        """Refresh every panel now (the ``r`` keybinding)."""
        self.refresh_snapshots()

    def refresh_snapshots(self) -> None:
        """Re-pull every snapshot in one coalesced pass, isolating per-panel failures."""
        self._refresh_count += 1
        model = self._read_model
        kill = self._kill_switch_panel
        events = self._event_log_panel
        self._refresh_panel(kill, model.kill_switch_epoch, kill.show)
        self._refresh_panel(self._org_panel, model.org_snapshot, self._org_panel.show)
        self._refresh_panel(self._spend_panel, model.spend_snapshot, self._spend_panel.show)
        self._refresh_panel(
            self._front_door_panel, model.front_door_activity, self._front_door_panel.show
        )
        self._refresh_panel(events, model.recorded_events, events.show)

    def _refresh_panel(
        self,
        panel: SupportsErrorDisplay,
        accessor: Callable[[], _T],
        render: Callable[[_T], None],
    ) -> None:
        """Pull one snapshot and render it; surface a raise as a per-panel error line.

        Args:
            panel: The panel to show an error on if the accessor raises.
            accessor: The read-model accessor that fetches this panel's snapshot.
            render: The panel's render method for the fetched snapshot.
        """
        try:
            snapshot = accessor()
        except Exception as exc:  # defensive UI boundary: one bad source must not crash the app
            panel.show_error(str(exc) or type(exc).__name__)
            return
        render(snapshot)

    @property
    def refresh_count(self) -> int:
        """How many coalesced refreshes have run (lets a test prove ``r`` re-pulled data)."""
        return self._refresh_count
