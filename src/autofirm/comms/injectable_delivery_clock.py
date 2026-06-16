"""Injectable, deterministic clock for the comms plane (no wall-clock in core).

What this does
--------------
Defines the :class:`DeliveryClock` protocol the bus depends on for timestamps,
plus a deterministic :class:`ManualClock` for tests/replay and a thin
:class:`SystemClock` for production. The bus core NEVER reads ``datetime.now()``
directly -- it asks its injected clock -- so envelope timestamps are reproducible
across repeated runs (CLAUDE §3.11 determinism) and tests are free of wall-clock
nondeterminism.

Why it exists / where it sits
-----------------------------
The A2 requirement is "no wall-clock nondeterminism in the core -- inject a
clock". Mirrors the saga substrate's dependency-injection style: the only thing
that varies between a test run and production is which clock is wired in.

Security / compliance invariants upheld
---------------------------------------
* **Determinism (§3.11):** identical inputs + the same :class:`ManualClock` ->
  identical envelope timestamps and audit records, every run. No hidden global
  time read in the routing path.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Protocol, runtime_checkable

__all__ = ["DeliveryClock", "ManualClock", "SystemClock"]


@runtime_checkable
class DeliveryClock(Protocol):
    """A monotonic-enough source of UTC timestamps for envelope stamping."""

    def now(self) -> datetime:
        """Return the current instant as a timezone-aware UTC datetime."""
        ...


class ManualClock:
    """Deterministic test/replay clock advanced explicitly by the caller.

    Starts at a fixed epoch and only moves when :meth:`tick` is called, so a test
    controls time exactly and two runs with the same tick sequence are identical.
    """

    def __init__(self, start: datetime | None = None) -> None:
        """Initialise at ``start`` (a fixed UTC epoch by default)."""
        base = start if start is not None else datetime(2025, 1, 1, tzinfo=UTC)
        # Normalise to UTC so every stamped timestamp is comparable (determinism).
        self._now = base.replace(tzinfo=UTC) if base.tzinfo is None else base.astimezone(UTC)

    def now(self) -> datetime:
        """Return the current (frozen until ``tick``) UTC instant."""
        return self._now

    def tick(self, seconds: float = 1.0) -> datetime:
        """Advance the clock by ``seconds`` and return the new instant."""
        self._now = self._now + timedelta(seconds=seconds)
        return self._now


class SystemClock:
    """Production clock reading the real UTC wall clock.

    Used ONLY at the composition root in production; never inside tests of the
    core (those use :class:`ManualClock`) so the core stays deterministic.
    """

    def now(self) -> datetime:
        """Return the real current UTC instant (timezone-aware)."""
        return datetime.now(UTC)
