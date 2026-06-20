"""The shared tabular cockpit panel: title + subtitle + a body with three render states.

What this does
--------------
Defines :class:`CockpitTablePanel`, the base widget every tabular cockpit panel (org, spend,
front-door, event-log) extends. It owns the three-state render contract the design bar requires:
``populated`` (a Rich table of the snapshot rows), ``empty`` (a deliberate "nothing yet"
message — never a blank or a crash), and ``error`` (an "unavailable" line when a snapshot
accessor raises). It exposes the rendered content (:attr:`state`, :attr:`rows`, :attr:`message`,
:attr:`subtitle`) so a Pilot test can assert real data reached the screen, not just that a
widget mounted.

Why it exists / where it sits
-----------------------------
Centralising the empty/populated/error rendering in one base keeps each concrete panel tiny
(it only maps its view type to rows) and guarantees every panel handles all three states
identically. Sits in the tui layer; depends only on Textual, Rich, and stdlib — never on the
composition root, the adapters, or an on-main domain package.

Security / compliance invariants upheld
---------------------------------------
* **Nothing static (CLAUDE.md §3.14):** the displayed content is derived solely from the
  injected snapshot rows, so the panel can never show stale or fabricated data.
* **Fail-soft rendering (§3.14):** :meth:`show_error` renders a visible error line rather than
  letting a raising accessor crash the whole cockpit.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Literal

from rich.table import Table
from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Static

__all__ = ["CockpitTablePanel"]

_PanelState = Literal["empty", "populated", "error"]


class CockpitTablePanel(Vertical):
    """A titled panel that renders snapshot rows, an empty message, or an error line."""

    def __init__(
        self,
        *,
        title: str,
        columns: tuple[str, ...],
        empty_message: str,
        panel_id: str,
    ) -> None:
        """Build a panel with a fixed title, column headers, and empty-state message.

        Args:
            title: The panel's heading (rendered bold in the accent colour).
            columns: The table column headers, in display order.
            empty_message: The message shown when the snapshot has no rows.
            panel_id: The widget id (also used as a stable CSS hook for tests).
        """
        super().__init__(id=panel_id, classes="cockpit-panel")
        self._title_text = title
        self._columns = columns
        self._empty_message = empty_message
        self._state: _PanelState = "empty"
        self._rows: tuple[tuple[str, ...], ...] = ()
        self._message = empty_message
        self._subtitle = ""

    def compose(self) -> ComposeResult:
        """Lay out the title, the (initially hidden) subtitle, and the body."""
        yield Static(self._title_text, classes="panel-title")
        yield Static("", classes="panel-subtitle")
        yield Static("", classes="panel-body")

    def on_mount(self) -> None:
        """Hide the empty subtitle and paint the initial (empty) state."""
        self.query_one(".panel-subtitle", Static).display = False
        self._repaint_body()

    def display_rows(self, rows: Iterable[tuple[str, ...]]) -> None:
        """Show ``rows`` (populated) or the empty message when there are none."""
        self._rows = tuple(rows)
        self._state = "populated" if self._rows else "empty"
        self._message = "" if self._rows else self._empty_message
        self._repaint_body()

    def show_error(self, message: str) -> None:
        """Render an "unavailable" error line for a failed snapshot accessor."""
        self._state = "error"
        self._rows = ()
        self._message = f"unavailable: {message}"
        self._repaint_body()

    def set_subtitle(self, text: str) -> None:
        """Set (and reveal) a one-line summary above the table, or hide it when blank."""
        self._subtitle = text
        subtitle = self.query_one(".panel-subtitle", Static)
        subtitle.update(text)
        subtitle.display = bool(text)

    def _repaint_body(self) -> None:
        """Repaint the body to reflect the current state (populated / empty / error)."""
        body = self.query_one(".panel-body", Static)
        if self._state == "populated":
            body.update(self._build_table())
            return
        style = "dim italic" if self._state == "empty" else "bold red"
        body.update(Text(self._message, style=style))

    def _build_table(self) -> Table:
        """Build the Rich table for the current rows (one source for screen and assertions)."""
        table = Table(expand=True, show_edge=False, pad_edge=False, header_style="bold")
        for column in self._columns:
            table.add_column(column, overflow="fold")
        for row in self._rows:
            table.add_row(*row)
        return table

    @property
    def state(self) -> _PanelState:
        """The current render state: ``"populated"`` / ``"empty"`` / ``"error"``."""
        return self._state

    @property
    def rows(self) -> tuple[tuple[str, ...], ...]:
        """The exact rows currently displayed (empty when not populated)."""
        return self._rows

    @property
    def message(self) -> str:
        """The empty/error message currently displayed (blank when populated)."""
        return self._message

    @property
    def subtitle(self) -> str:
        """The current one-line summary above the table (blank when none set)."""
        return self._subtitle
