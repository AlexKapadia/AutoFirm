"""The in-process heartbeat scheduler: register beats, fire the due ones on a tick.

What this does
--------------
Defines :class:`HeartbeatScheduler`, which holds a set of registered
:class:`~autofirm.heartbeat.recurring_beat_definition.BeatDefinition` beats and,
when its injected clock is advanced and :meth:`tick` is called, fires **exactly
the beats whose next-due time has been reached** — deterministically, in a stable
name order. Each fired beat's next-due time rolls forward to the first boundary
strictly after "now" (missed periods coalesce into one fire, so a large time jump
fires each due beat once, never an unbounded catch-up burst).

Three guarantees make it safe for long-running autonomous use:

* **Idempotent re-entrancy:** a beat already executing is never re-entered. If a
  beat's callback itself calls :meth:`tick` (directly or transitively), the
  in-flight beat is skipped, so a beat can never double-fire within one logical
  tick.
* **Per-beat failure isolation:** if one beat's callback raises, the failure is
  caught, recorded as a structured failure in the returned ``TickResult``, and the
  remaining due beats still fire. One bad beat can never starve its siblings, and
  the failure is surfaced (fail-closed), never silently swallowed.
* **Fail-closed registration:** registering a duplicate beat name, or a
  mis-specified beat, is refused — the schedule can never hold two beats fighting
  over one name.

Why it exists / where it sits
-----------------------------
This is the public face of the heartbeat plane — "everything has a heartbeat"
made concrete and testable. It depends only on the beat definition and the
injected clock, so it is unit-testable with no wall-clock and no network. The
OS-level watchdog / cron (CLAUDE.md §4.8) are separate concerns that would drive
*this* on each external tick; they are deliberately not duplicated here.

Security / compliance invariants upheld
---------------------------------------
* **Determinism (§3.11):** firing is a pure function of (registered beats, their
  next-due times, the injected clock). Beats fire in a stable, name-sorted order.
* **Fail-closed (§5.6):** duplicate names and out-of-contract beats are refused.
* **Bounded work per tick:** each beat fires at most once per :meth:`tick`, so a
  mutated/large time advance can never spin the scheduler unboundedly.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from autofirm.heartbeat.injected_heartbeat_clock import HeartbeatClock
from autofirm.heartbeat.recurring_beat_definition import BeatDefinition
from autofirm.heartbeat.tick_result import BeatFailure, TickResult

__all__ = ["DuplicateBeatError", "HeartbeatScheduler"]


class DuplicateBeatError(Exception):
    """Raised when a beat is registered under a name already in the schedule."""


class HeartbeatScheduler:
    """Registers named recurring beats and fires the due ones on each tick.

    The scheduler is driven by an injected :class:`HeartbeatClock`; it never reads
    the wall clock. Call :meth:`register` to add beats, advance the clock, then
    call :meth:`tick` to fire whichever beats have become due.
    """

    __slots__ = ("_beats", "_clock", "_in_flight", "_next_due")

    def __init__(self, clock: HeartbeatClock) -> None:
        """Create an empty scheduler driven by the injected ``clock``."""
        self._clock = clock
        self._beats: dict[str, BeatDefinition] = {}
        # The earliest future instant each beat is allowed to fire at. Seeded one
        # interval after the clock's "now" at registration, so a freshly-registered
        # beat fires after one full interval, never immediately.
        self._next_due: dict[str, datetime] = {}
        # Names of beats currently executing — the re-entrancy guard (idempotency).
        self._in_flight: set[str] = set()

    def register(self, beat: BeatDefinition) -> None:
        """Register ``beat``, scheduling its first fire one interval from now.

        Fail-closed: a name already registered is refused (:class:`DuplicateBeatError`)
        so two beats can never share a name and silently shadow each other.
        """
        if beat.name in self._beats:
            # fail-closed (§5.6): duplicate beat names would make firing ambiguous
            # and let one beat overwrite another's schedule — refuse it.
            raise DuplicateBeatError(f"beat {beat.name!r} is already registered")
        self._beats[beat.name] = beat
        # First fire is one full interval after the current injected instant.
        self._next_due[beat.name] = self._clock.now() + timedelta(seconds=beat.interval_seconds)

    def registered_names(self) -> frozenset[str]:
        """The set of currently-registered beat names (a read-only snapshot)."""
        return frozenset(self._beats)

    def tick(self) -> TickResult:
        """Fire every due beat independently; return what fired and what failed.

        Beats fire in stable name-sorted order (determinism). A beat already
        executing (in-flight) is skipped — the idempotent re-entrancy guard — so a
        callback that re-enters :meth:`tick` can never cause a double-fire. Each
        due beat's next-due time rolls forward to the first boundary strictly
        after "now", coalescing any missed periods into a single fire.

        **Per-beat failure isolation (the resilience guarantee):** each due beat's
        callback runs inside its own ``try``/``except``. If a callback raises, the
        exception is CAUGHT, recorded as a structured :class:`BeatFailure`, and the
        loop CONTINUES to the remaining due beats. A single persistently-failing
        beat therefore can never starve its siblings — without this, one bad beat
        wedged every later-sorted beat on every tick. The failure is surfaced in
        the returned :class:`TickResult` (fail-closed: reported and auditable, not
        silently swallowed), never re-raised out of the tick.

        Returns:
            A :class:`TickResult` carrying the names that fired cleanly and the
            per-beat failures, both in fire order.
        """
        now = self._clock.now()
        fired: list[str] = []
        failures: list[BeatFailure] = []
        # Stable, deterministic order: sort by name so two runs fire identically.
        for name in sorted(self._beats):
            if name in self._in_flight:
                # idempotency: a beat mid-execution is not re-entered (no double-fire).
                continue
            due = self._next_due[name]
            if now < due:
                continue  # not yet due — leave its schedule untouched
            beat = self._beats[name]
            self._in_flight.add(name)  # guard set BEFORE calling out (re-entrancy)
            try:
                beat.callback()
            except Exception as exc:  # isolate ANY callback failure (broad on purpose)
                # Resilience: one beat's failure must not wedge its siblings. Capture
                # the failure as structured data and keep going round the loop so
                # every other due beat still fires. fail-closed (§5.6): the failure
                # is SURFACED in the result below, never silently swallowed.
                failures.append(BeatFailure(name=name, error=repr(exc)))
            else:
                fired.append(name)  # clean fire — recorded only on success
            finally:
                # Always clear the guard and roll the schedule forward, even on a
                # failure, so a failing beat reschedules normally and never re-fires
                # instantly or blocks the rest of this tick.
                self._in_flight.discard(name)
                self._next_due[name] = self._advance_due(due, beat.interval_seconds, now)
        return TickResult(fired=tuple(fired), failures=tuple(failures))

    @staticmethod
    def _advance_due(due: datetime, interval_seconds: float, now: datetime) -> datetime:
        """Roll ``due`` forward by whole intervals until it is strictly after ``now``.

        Coalesces missed periods: after a fire, the next due time is the first
        interval boundary strictly greater than the current instant, so a single
        large advance fires the beat once (not once per missed period) and the
        beat is never instantly due again.
        """
        step = timedelta(seconds=interval_seconds)
        next_due = due
        # Bounded by construction: interval is strictly positive, so each step makes
        # strict forward progress and the loop terminates once we pass ``now``.
        while next_due <= now:
            next_due = next_due + step
        return next_due
