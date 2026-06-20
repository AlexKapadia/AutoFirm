"""The kill-switch status panel: a prominent, colour-coded ARMED / TRIPPED header badge.

What this does
--------------
Defines :class:`KillSwitchStatusPanel`, the header badge that renders the global egress
kill-switch state from an
:class:`~autofirm.cockpit.tui.cockpit_read_model_protocol.EpochLike`: ``ARMED`` (untripped, shown
in the success colour) versus ``TRIPPED`` (engaged, shown in the error colour), each with the
epoch version. If the source is unavailable it renders an "UNAVAILABLE" line rather than
crashing the app. It exposes :attr:`tripped`, :attr:`version`, :attr:`available`, and
:attr:`status_text` so a Pilot test can assert the real state reached the screen.

Why it exists / where it sits
-----------------------------
The kill-switch is the single most safety-critical signal on the cockpit, so it lives in the
header rather than a grid cell (CLAUDE.md §3.14 visual hierarchy). It is observe-only — there is
no trip/reset control here (read-only projection, §3.2). Sits in the tui layer; renders via the
read-only ``EpochLike`` attributes, so the tui never imports the gateway epoch type directly.
"""

from __future__ import annotations

from textual.widgets import Static

from autofirm.cockpit.tui.cockpit_read_model_protocol import EpochLike

__all__ = ["KillSwitchStatusPanel"]


class KillSwitchStatusPanel(Static):
    """A colour-coded header badge showing the kill-switch ARMED / TRIPPED / UNAVAILABLE state."""

    def __init__(self, *, panel_id: str) -> None:
        """Build the badge in an unknown (pre-first-refresh) state."""
        super().__init__("KILL-SWITCH …", id=panel_id, classes="kill-switch")
        self._tripped = False
        self._version = -1
        self._available = False
        self._status_text = "KILL-SWITCH …"

    def show(self, epoch: EpochLike) -> None:
        """Render the epoch as ARMED (untripped) or TRIPPED (engaged), colour-coded."""
        self._available = True
        self._tripped = epoch.tripped
        self._version = epoch.version
        label = "TRIPPED" if epoch.tripped else "ARMED"
        # Distinct classes drive the colour (success vs error) so the state is unmistakable.
        self.set_class(epoch.tripped, "tripped")
        self.set_class(not epoch.tripped, "armed")
        self.set_class(False, "unavailable")
        self._status_text = f"KILL-SWITCH {label}  ·  epoch {epoch.version}"
        self.update(self._status_text)

    def show_error(self, message: str) -> None:
        """Render an UNAVAILABLE badge for a failed kill-switch source (the app stays alive)."""
        self._available = False
        self.set_class(False, "armed")
        self.set_class(False, "tripped")
        self.set_class(True, "unavailable")
        self._status_text = f"KILL-SWITCH UNAVAILABLE  ·  {message}"
        self.update(self._status_text)

    @property
    def tripped(self) -> bool:
        """Whether the most recent observed epoch was tripped (egress halted)."""
        return self._tripped

    @property
    def version(self) -> int:
        """The most recent observed epoch version (``-1`` before the first refresh)."""
        return self._version

    @property
    def available(self) -> bool:
        """Whether the kill-switch source was readable on the last refresh."""
        return self._available

    @property
    def status_text(self) -> str:
        """The exact badge text currently displayed."""
        return self._status_text
