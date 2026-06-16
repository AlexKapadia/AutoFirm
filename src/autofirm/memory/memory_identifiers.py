"""Typed identifiers and injectable determinism seams for the memory layer (A4).

What this does
--------------
Defines the opaque, typed identifiers the memory layer uses
(:class:`OwnerId`, :class:`MemoryId`) and the two **injectable seams** that make
every memory operation deterministic and replayable: :class:`MemoryClock` (the
only source of "now", used for the injected-timestamp on every record) and
:class:`MemoryIdGenerator` (the only source of new record ids). No module in the
memory package ever calls ``datetime.now()`` or a UUID/random factory directly --
they take a clock / id-generator, so a test can pin time and ids and assert
exact, reproducible provenance trails (CLAUDE.md §3.11 determinism).

Why it exists / where it sits
-----------------------------
This is the lowest layer of ``autofirm.memory``: the record contract, the store,
and the retrieval ranker all depend on it and nothing depends back on them.
Keeping the clock and id-generator as injected Protocols (rather than module
globals) is what lets the property tests drive *arbitrary* write/supersede/delete
sequences and still get a single canonical, comparable result every run.

Security / compliance invariants upheld
---------------------------------------
* **Determinism (§3.11):** time and identity are inputs, never ambient. A run is
  a pure function of (initial state, injected clock, injected id-generator,
  operation sequence).
* **Typed boundaries (§5.6 validate-at-boundary):** ids are distinct ``NewType``
  aliases so an owner id can never be silently passed where a memory id is
  expected, and vice-versa.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import NewType, Protocol, runtime_checkable

__all__ = [
    "FrozenMemoryClock",
    "MemoryClock",
    "MemoryId",
    "MemoryIdGenerator",
    "OwnerId",
    "SequentialMemoryIdGenerator",
]

# Distinct opaque id types. NewType gives static separation at zero runtime cost;
# both are just strings at runtime. OwnerId names the principal that OWNS a memory
# (an agent id or a role id, or the shared/org scope) -- it is the access key.
OwnerId = NewType("OwnerId", str)
MemoryId = NewType("MemoryId", str)


@runtime_checkable
class MemoryClock(Protocol):
    """The single source of 'now' for the memory layer (injected, never ambient).

    Returns a timezone-aware UTC instant used to stamp every record's
    ``injected_at``. Injecting it (instead of reading the wall clock) is what
    makes provenance timestamps deterministic and lets tests assert exact times.
    """

    def now(self) -> datetime:
        """Return the current instant as a timezone-aware UTC ``datetime``."""
        ...


@runtime_checkable
class MemoryIdGenerator(Protocol):
    """The single source of new record identifiers for the memory layer (injected).

    Every newly-written record gets its id from here, so id allocation is
    reproducible across runs and a test can predict the exact id of the Nth write.
    """

    def next_id(self, prefix: str) -> str:
        """Return a fresh, unique id string carrying ``prefix`` for readability."""
        ...


class FrozenMemoryClock:
    """A deterministic :class:`MemoryClock`, optionally advancing on each call.

    Used in tests and replay: ``now()`` returns the seeded instant and (if
    ``step_seconds`` is non-zero) advances by that step on each call, so a
    sequence of writes gets strictly increasing, predictable timestamps -- which
    is exactly what the recency component of the retrieval score needs.
    """

    def __init__(self, start: datetime, step_seconds: float = 0.0) -> None:
        """Seed at ``start`` (must be tz-aware), advancing ``step_seconds``/call."""
        # fail-closed: a naive datetime makes 'now' zone-ambiguous; refuse it so
        # every provenance timestamp is unambiguously UTC (§3.11 determinism).
        if start.tzinfo is None:
            raise ValueError("FrozenMemoryClock requires a timezone-aware datetime")
        self._current = start.astimezone(UTC)
        self._step_seconds = step_seconds

    def now(self) -> datetime:
        """Return the current instant, then advance by ``step_seconds``."""
        value = self._current
        if self._step_seconds:
            self._current = self._current + timedelta(seconds=self._step_seconds)
        return value


class SequentialMemoryIdGenerator:
    """A deterministic :class:`MemoryIdGenerator` emitting ``{prefix}-{n}`` ids.

    The counter is monotonic and shared across prefixes so two records never
    collide even if written with different prefixes, making ids globally unique
    and replay-stable (the Nth ``next_id`` is always ``...-N``).
    """

    def __init__(self, start: int = 0) -> None:
        """Seed the monotonic counter at ``start`` (must be >= 0, fail-closed)."""
        if start < 0:
            raise ValueError("id counter start must be >= 0")  # fail-closed
        self._counter = start

    def next_id(self, prefix: str) -> str:
        """Return ``{prefix}-{n}`` and increment the monotonic counter."""
        if not prefix:
            raise ValueError("id prefix must be non-empty")  # fail-closed: traceable ids
        value = f"{prefix}-{self._counter}"
        self._counter += 1
        return value
