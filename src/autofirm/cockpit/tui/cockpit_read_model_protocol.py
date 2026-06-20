"""Structural read-only contracts the TUI renders against (no composition/on-main import).

What this does
--------------
Defines the small ``Protocol`` surface the Textual cockpit binds to instead of the concrete
:class:`~autofirm.cockpit.composition.cockpit_application.CockpitApplication`: :class:`EpochLike`
(a kill-switch epoch's ``version``/``tripped``), :class:`EventLike` (a recorded event's
``seq``/``kind``/``source``/``recorded_at``), :class:`CockpitReadModel` (the five read accessors
the app pulls each tick), and :class:`SupportsErrorDisplay` (the show-error contract every panel
satisfies). Protocol members are read-only properties so a concrete type (or a test fake) is
accepted structurally without inheritance.

Why it exists / where it sits
-----------------------------
Typing the app against these protocols is what lets the ``tui`` layer stay free of any DIRECT
import of the composition root, the event-log module, or the gateway epoch — the import-linter
fences (CLAUDE.md §3.10) forbid the tui from naming the on-main packages, and a Pilot test can
drive the running app with a synthetic stand-in that satisfies the same shape. Sits in the tui
layer; depends only on stdlib and the read-model DTOs.

Security / compliance invariants upheld
---------------------------------------
* **Read-only projection (CLAUDE.md §3.2):** every accessor returns an immutable view; the
  protocol exposes no mutate/trip surface, so the UI can never flip a kill-switch or edit state.
"""

from __future__ import annotations

from datetime import datetime
from typing import Protocol

from autofirm.cockpit.readmodels.front_door_activity_view import FrontDoorActivityView
from autofirm.cockpit.readmodels.org_snapshot_view import OrgSnapshotView
from autofirm.cockpit.readmodels.spend_snapshot_view import SpendSnapshotView

__all__ = [
    "CockpitReadModel",
    "EpochLike",
    "EventLike",
    "SupportsErrorDisplay",
]


class EpochLike(Protocol):
    """The kill-switch epoch fields the header renders (read-only, no gateway import)."""

    @property
    def version(self) -> int:
        """The monotonic epoch version (a reset/re-arm bumps it)."""
        ...

    @property
    def tripped(self) -> bool:
        """``True`` when the global egress kill-switch is engaged (halt)."""
        ...


class EventLike(Protocol):
    """The recorded-event fields the event-log panel renders (read-only, no eventlog import)."""

    @property
    def seq(self) -> int:
        """The monotonic, strictly-increasing sequence number."""
        ...

    @property
    def kind(self) -> object:
        """The event kind; rendered via ``str(...)`` (a ``StrEnum`` yields its value)."""
        ...

    @property
    def source(self) -> str:
        """The non-blank provenance string (who/what produced the event)."""
        ...

    @property
    def recorded_at(self) -> datetime:
        """When the event was recorded (tz-aware; injected clock, never wall-clock)."""
        ...


class CockpitReadModel(Protocol):
    """The five read-only accessors the cockpit app pulls each refresh tick.

    The concrete :class:`CockpitApplication` satisfies this structurally, so the app never
    imports it; a Pilot test supplies a synthetic stand-in of the same shape.
    """

    def org_snapshot(self) -> OrgSnapshotView:
        """Project the current org state into an immutable snapshot."""
        ...

    def spend_snapshot(self) -> SpendSnapshotView:
        """Project the cost ledger into a spend snapshot (total, rollups, band, verify)."""
        ...

    def front_door_activity(self) -> FrontDoorActivityView:
        """Project the front-door provenance trail into an activity snapshot."""
        ...

    def kill_switch_epoch(self) -> EpochLike:
        """Return the currently observed kill-switch epoch (observe-only, never flips it)."""
        ...

    def recorded_events(self) -> tuple[EventLike, ...]:
        """Replay every recorded cockpit event in order (the audit read path)."""
        ...


class SupportsErrorDisplay(Protocol):
    """A panel that can surface an unavailable-source error instead of crashing the app."""

    def show_error(self, message: str) -> None:
        """Render an error line for a failed snapshot accessor (the app stays alive)."""
        ...
