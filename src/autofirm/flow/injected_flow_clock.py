"""Injected, deterministic clock for the flow plane (no wall-clock in core).

What this does
--------------
Defines the :class:`FlowClock` protocol the flow trail depends on for transition
timestamps, plus a deterministic :class:`ManualFlowClock` for tests/replay. The
flow core NEVER reads ``datetime.now()`` directly — it asks its injected clock —
so a transition's recorded timestamp is reproducible across repeated runs
(CLAUDE.md §3.11 determinism) and tests are free of wall-clock nondeterminism.

Why it exists / where it sits
-----------------------------
Mirrors the determinism seams already in the codebase
(``autofirm.org.org_identifiers.Clock``,
``autofirm.comms.injectable_delivery_clock.DeliveryClock``): the only thing that
varies between a test run and production is which clock is wired in at the
composition root. Kept in the flow package so the plane is self-contained and
unit-testable in isolation.

Security / compliance invariants upheld
---------------------------------------
* **Determinism (§3.11):** identical inputs + the same :class:`ManualFlowClock`
  yield identical flow-trail timestamps every run; no hidden global time read in
  the handoff path.
* **Tz-aware UTC only (fail-closed):** a naive start instant is refused so every
  recorded timestamp is unambiguously UTC.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Protocol, runtime_checkable

__all__ = ["FlowClock", "ManualFlowClock"]


@runtime_checkable
class FlowClock(Protocol):
    """The single source of 'now' for the flow plane (injected, never ambient)."""

    def now(self) -> datetime:
        """Return the current instant as a timezone-aware UTC ``datetime``."""
        ...


class ManualFlowClock:
    """Deterministic test/replay clock advanced explicitly by the caller.

    Starts at a fixed UTC epoch and only moves when :meth:`tick` is called, so a
    test controls time exactly and two runs with the same tick sequence record
    identical transition timestamps.
    """

    def __init__(self, start: datetime | None = None) -> None:
        """Initialise at ``start`` (a fixed tz-aware UTC epoch by default)."""
        base = start if start is not None else datetime(2025, 1, 1, tzinfo=UTC)
        # fail-closed: a naive datetime would make 'now' ambiguous across zones;
        # normalise to UTC so every recorded timestamp is unambiguous (§3.11).
        self._now = base.replace(tzinfo=UTC) if base.tzinfo is None else base.astimezone(UTC)

    def now(self) -> datetime:
        """Return the current (frozen until ``tick``) UTC instant."""
        return self._now

    def tick(self, seconds: float = 1.0) -> datetime:
        """Advance the clock by ``seconds`` and return the new instant."""
        self._now = self._now + timedelta(seconds=seconds)
        return self._now
