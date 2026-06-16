"""Injected, deterministic clock for the heartbeat plane (no wall-clock in core).

What this does
--------------
Defines the :class:`HeartbeatClock` protocol the scheduler depends on for "now",
plus a deterministic :class:`ManualHeartbeatClock` for tests/replay. The
scheduler NEVER reads ``datetime.now()`` directly — a test advances the manual
clock explicitly and the scheduler fires exactly the beats that became due — so
which beats fire is a pure function of the injected time advance (CLAUDE.md §3.11
determinism) with no wall-clock sleeping anywhere in the tests.

Why it exists / where it sits
-----------------------------
Mirrors the determinism seams already in the codebase
(``autofirm.org.org_identifiers.Clock``, the flow plane's ``FlowClock``): only the
wired-in clock differs between a test run and production. Kept in the heartbeat
package so the plane is self-contained and unit-testable in isolation.

Security / compliance invariants upheld
---------------------------------------
* **Determinism (§3.11):** identical advances of the same
  :class:`ManualHeartbeatClock` fire identical beat sequences every run.
* **Tz-aware UTC only (fail-closed):** a naive start instant is refused so every
  due-time comparison is unambiguous.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Protocol, runtime_checkable

__all__ = ["HeartbeatClock", "ManualHeartbeatClock"]


@runtime_checkable
class HeartbeatClock(Protocol):
    """The single source of 'now' for the heartbeat plane (injected, never ambient)."""

    def now(self) -> datetime:
        """Return the current instant as a timezone-aware UTC ``datetime``."""
        ...


class ManualHeartbeatClock:
    """Deterministic test/replay clock advanced explicitly by the caller.

    Starts at a fixed UTC epoch and only moves when :meth:`advance` is called, so
    a test controls time exactly and two runs with the same advance sequence fire
    the same beats. No wall-clock sleeping is ever required.
    """

    def __init__(self, start: datetime | None = None) -> None:
        """Initialise at ``start`` (a fixed tz-aware UTC epoch by default)."""
        base = start if start is not None else datetime(2025, 1, 1, tzinfo=UTC)
        # fail-closed: normalise to UTC so every due-time comparison is unambiguous.
        self._now = base.replace(tzinfo=UTC) if base.tzinfo is None else base.astimezone(UTC)

    def now(self) -> datetime:
        """Return the current (frozen until ``advance``) UTC instant."""
        return self._now

    def advance(self, seconds: float) -> datetime:
        """Advance the clock by ``seconds`` (must be >= 0) and return the new instant.

        Fail-closed: time never runs backwards on a heartbeat clock — a negative
        advance would let a beat's due-time logic see a non-monotonic clock and is
        refused.
        """
        if seconds < 0:
            raise ValueError("heartbeat clock cannot advance by a negative amount")
        self._now = self._now + timedelta(seconds=seconds)
        return self._now
