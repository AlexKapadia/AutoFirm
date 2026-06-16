"""Typed identifiers and injectable determinism seams for the dynamic-org core.

What this does
--------------
Defines the opaque, typed identifiers the org engine uses (:class:`RoleId`,
:class:`ArtifactId`) and the two **injectable seams** that make every org
mutation deterministic and replayable: :class:`Clock` (the only source of
"now") and :class:`IdGenerator` (the only source of new ids). No module in the
org package ever calls ``datetime.now()`` or a random/UUID factory directly —
they take a :class:`Clock` / :class:`IdGenerator` so a test can pin time and ids
and assert exact, reproducible audit trails (CLAUDE.md §3.11 determinism).

Why it exists / where it sits
-----------------------------
This is the lowest layer of ``autofirm.org``: the lifecycle engine, the
hierarchy state, and the ownership ledger all depend on it and nothing depends
back on them. Keeping the clock and id-generator as injected Protocols (rather
than module-level globals) is what lets the property tests drive *arbitrary*
sequences of hire/fire/re-scope and still get a single canonical, comparable
result every run.

Security / compliance invariants upheld
---------------------------------------
* **Determinism (CLAUDE.md §3.11):** time and identity are inputs, never
  ambient. A run is a pure function of (initial state, injected clock, injected
  id-generator, operation sequence).
* **Typed boundaries (§5.6 validate-at-boundary):** ids are distinct ``NewType``
  aliases so a role id can never be silently passed where an artifact id is
  expected.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import NewType, Protocol, runtime_checkable

__all__ = [
    "ArtifactId",
    "Clock",
    "FrozenClock",
    "IdGenerator",
    "RoleId",
    "SequentialIdGenerator",
]

# Distinct opaque id types. NewType gives static separation (a RoleId is not an
# ArtifactId) at zero runtime cost; both are just strings at runtime.
RoleId = NewType("RoleId", str)
ArtifactId = NewType("ArtifactId", str)


@runtime_checkable
class Clock(Protocol):
    """The single source of 'now' for the org engine (injected, never ambient).

    A :class:`Clock` returns a timezone-aware UTC instant. Injecting it (instead
    of calling ``datetime.now()``) is what makes audit timestamps deterministic
    and lets tests assert exact event times.
    """

    def now(self) -> datetime:
        """Return the current instant as a timezone-aware UTC ``datetime``."""
        ...


@runtime_checkable
class IdGenerator(Protocol):
    """The single source of new identifiers for the org engine (injected).

    Every newly-spawned role gets its id from here, so id allocation is
    reproducible across runs and a test can predict the exact id of the Nth role.
    """

    def next_id(self, prefix: str) -> str:
        """Return a fresh, unique id string carrying ``prefix`` for readability."""
        ...


class FrozenClock:
    """A deterministic :class:`Clock` that returns a fixed, optionally-advancing instant.

    Used in tests and replay: ``now()`` returns the seeded instant and (if
    ``step`` is non-zero) advances by ``step`` on each call, so a sequence of
    mutations gets strictly increasing, predictable timestamps.
    """

    def __init__(self, start: datetime, step_seconds: float = 0.0) -> None:
        # fail-closed: a naive datetime would make 'now' ambiguous across zones;
        # refuse it so every audit timestamp is unambiguously UTC (§3.11).
        if start.tzinfo is None:
            raise ValueError("FrozenClock requires a timezone-aware datetime")
        self._current = start.astimezone(UTC)
        self._step_seconds = step_seconds

    def now(self) -> datetime:
        """Return the current instant, then advance by ``step_seconds``."""
        value = self._current
        if self._step_seconds:
            from datetime import timedelta

            self._current = self._current + timedelta(seconds=self._step_seconds)
        return value


class SequentialIdGenerator:
    """A deterministic :class:`IdGenerator` emitting ``{prefix}-{n}`` ids.

    The counter is monotonic and shared across prefixes so two roles never
    collide even if spawned with different prefixes, making ids globally unique
    and replay-stable (the Nth ``next_id`` is always ``...-N``).
    """

    def __init__(self, start: int = 0) -> None:
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
