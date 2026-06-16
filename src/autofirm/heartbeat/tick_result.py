"""The structured result of one scheduler tick: what fired, and what failed.

What this does
--------------
Defines the immutable value objects a :meth:`HeartbeatScheduler.tick` returns:

* :class:`BeatFailure` — one beat whose callback raised, captured as
  ``(name, error)`` so the failure is **surfaced and auditable**, never swallowed.
* :class:`TickResult` — the whole tick outcome: the names of beats that fired
  cleanly (in fire order) and the per-beat failures (in fire order).

Why it exists / where it sits
-----------------------------
Before this, ``tick`` returned a bare ``tuple[str, ...]`` and let a callback's
exception propagate out of the loop, which aborted the tick — one failing beat
wedged every later-sorted sibling on EVERY tick. Isolating failures requires a
return shape that can carry *both* successes and failures, so a failure is
reported (fail-closed: visible, not hidden) without blocking siblings. This is
that shape. It lives beside the scheduler so the scheduler file stays single-
responsibility and under the 300-line limit (CLAUDE.md §5.7).

Security / compliance invariants upheld
---------------------------------------
* **Fail-closed surfacing (§5.6):** a callback failure is captured as structured
  data and returned, so the orchestrator can audit/alert on it. A failure is never
  silently dropped, and it is never conflated with a clean fire.
* **Determinism (§3.11):** both tuples preserve the deterministic fire order, so
  identical inputs yield identical results every run. The objects are frozen.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

__all__ = ["BeatFailure", "TickResult"]


class BeatFailure(BaseModel):
    """One beat whose callback raised on a tick, captured for audit.

    ``error`` is the stringified exception (type + message) — enough to surface
    and triage the failure without holding a live exception object across the
    tick boundary. The model is frozen so a recorded failure cannot be mutated.
    """

    model_config = ConfigDict(frozen=True)

    name: str  # the beat whose callback raised
    error: str  # repr of the raised exception (surfaced, never swallowed)


class TickResult(BaseModel):
    """The outcome of one :meth:`HeartbeatScheduler.tick`.

    ``fired`` holds the names of beats whose callback completed without raising,
    in the order they fired. ``failures`` holds one :class:`BeatFailure` per beat
    whose callback raised, also in fire order. A failing beat appears ONLY in
    ``failures`` (never in ``fired``), so the two lists never double-count a beat
    and a failure is always distinguishable from a clean fire.
    """

    model_config = ConfigDict(frozen=True)

    fired: tuple[str, ...]  # names that fired cleanly, in fire order
    failures: tuple[BeatFailure, ...]  # per-beat failures, in fire order

    @property
    def failed_names(self) -> tuple[str, ...]:
        """The names of the beats that failed this tick, in fire order."""
        return tuple(failure.name for failure in self.failures)

    @property
    def due_count(self) -> int:
        """Total beats that became due and were fired this tick (clean + failed).

        Every due, non-in-flight beat rolls its schedule forward exactly once per
        tick whether or not its callback raised, so this is the count of beats the
        tick acted on — useful for asserting siblings were not starved.
        """
        return len(self.fired) + len(self.failures)
