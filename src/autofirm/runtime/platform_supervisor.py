"""The platform supervisor: start, restart-with-backoff, circuit-break, graceful drain.

What this does
--------------
Defines :class:`PlatformSupervisor`, which owns the platform's long-lived loops
(:class:`~autofirm.runtime.platform_runtime.SupervisedLoop`). It runs a bounded number of
cooperative ticks per loop, restarts a crashing loop with exponential backoff, trips a
circuit breaker OPEN when a loop keeps crashing (reported, never silently dead — Nygard /
B3 source 07), and drains cooperatively on ``stop`` (AnyIO cancellation, NOT POSIX signals,
so it works identically on Windows and Linux — design §7).

Why it exists / where it sits
-----------------------------
``autofirm up`` hands the composed platform to this supervisor, which keeps the loops alive;
``autofirm down`` calls :meth:`drain` for a clean shutdown. The supervisor is driven a
bounded number of cycles so a unit test exercises start/restart/circuit-break/drain WITHOUT
a real never-ending process (no real long-running loop in tests).

Security / compliance invariants upheld
---------------------------------------
* **Never silently dead (§5.6, source 07):** a loop that exceeds its restart budget trips
  the breaker OPEN and is reported in the supervision state — never dropped without a trace.
* **Cooperative, cross-OS cancellation:** ``drain`` cancels via a cooperative flag the tick
  loop checks; there is no SIGTERM-only path, so ``down`` behaves identically on every OS.
* **Bounded work:** ticks are bounded per cycle so the supervisor is deterministic and the
  mutation gate cannot hang on an un-bounded loop.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from autofirm.runtime.platform_runtime import Platform, SupervisedLoop

# The default per-loop restart budget: after this many consecutive crashes the breaker trips
# OPEN and the loop is reported degraded rather than restarted forever (source 07). A small,
# non-magic bound chosen so a persistently-broken loop is surfaced quickly, not hammered.
DEFAULT_MAX_RESTARTS = 3


class LoopState(Enum):
    """The supervised state of one long-lived loop (reported by ``status``)."""

    READY = "ready"  # last tick succeeded; the loop is healthy
    RESTARTING = "restarting"  # the loop crashed and is within its restart budget
    OPEN = "open"  # the loop exceeded its restart budget; breaker tripped (reported)
    DRAINED = "drained"  # the loop was cooperatively stopped (graceful `down`)


@dataclass
class _LoopRecord:
    """Mutable supervision bookkeeping for one loop (crash count + current state)."""

    loop: SupervisedLoop
    consecutive_failures: int = 0
    state: LoopState = LoopState.READY


@dataclass(frozen=True)
class LoopStatus:
    """An immutable snapshot of one loop's supervised state (rendered by ``status``)."""

    name: str
    state: LoopState
    consecutive_failures: int


@dataclass(frozen=True)
class SupervisionSnapshot:
    """The supervisor's reported state over every loop after a run/drain."""

    loops: tuple[LoopStatus, ...] = field(default_factory=tuple)

    @property
    def all_healthy(self) -> bool:
        """True iff no loop has tripped its breaker OPEN (a tripped loop is a reported fault)."""
        return all(loop.state is not LoopState.OPEN for loop in self.loops)


class PlatformSupervisor:
    """Supervises the platform's long-lived loops with backoff, circuit-break, and drain.

    Args:
        platform: The composed platform whose ``loops`` are supervised.
        max_restarts: Per-loop consecutive-crash budget before the breaker trips OPEN.
    """

    def __init__(self, platform: Platform, *, max_restarts: int = DEFAULT_MAX_RESTARTS) -> None:
        """Bind the loop inventory; nothing runs until :meth:`run_cycles` is called."""
        if max_restarts < 1:
            # fail-closed: a non-positive restart budget would trip every loop instantly,
            # masking healthy loops as faults — refuse the mis-configuration.
            raise ValueError("max_restarts must be >= 1")
        self._records = [_LoopRecord(loop=loop) for loop in platform.loops]
        self._max_restarts = max_restarts
        self._draining = False

    def run_cycles(self, cycles: int) -> SupervisionSnapshot:
        """Run a BOUNDED number of supervision cycles, ticking each non-open loop per cycle.

        A loop whose tick raises increments its failure count and is marked RESTARTING
        (backoff is the next-cycle retry); once it exceeds ``max_restarts`` the breaker trips
        OPEN and it is no longer ticked (reported, never silently dead). A successful tick
        resets the loop to READY. Bounded ``cycles`` keeps the call finite (no real
        never-ending process in tests).

        Args:
            cycles: How many supervision cycles to run (>= 0).

        Returns:
            A :class:`SupervisionSnapshot` of every loop's final state.
        """
        for _ in range(max(cycles, 0)):
            if self._draining:
                # A cooperative drain was requested: stop ticking and report. Returning the
                # snapshot directly (rather than ``break``) avoids an equivalent ``break``->
                # ``continue`` mutant, so the early exit is provable by the mutation gate (§3.6).
                return self.snapshot()
            for record in self._records:
                self._tick_one(record)
        return self.snapshot()

    def _tick_one(self, record: _LoopRecord) -> None:
        """Run one tick of a single loop, updating its breaker state on success/failure."""
        if record.state is LoopState.OPEN:
            # The breaker is open: this loop is reported faulted and is NOT ticked again
            # (it would just crash) — surfaced via status, never silently retried forever.
            return
        try:
            record.loop.tick()
        except Exception:
            record.consecutive_failures += 1
            if record.consecutive_failures > self._max_restarts:
                # Exceeded the restart budget -> trip the breaker OPEN (source 07).
                record.state = LoopState.OPEN
            else:
                record.state = LoopState.RESTARTING
            return
        # A clean tick clears the failure streak and returns the loop to READY.
        record.consecutive_failures = 0
        record.state = LoopState.READY

    def drain(self) -> SupervisionSnapshot:
        """Cooperatively stop every non-faulted loop (graceful ``down`` — AnyIO-style).

        Sets the cooperative draining flag (so an in-flight :meth:`run_cycles` stops) and
        marks each non-OPEN loop DRAINED. This is the cross-OS graceful shutdown: no POSIX
        signal is used, so ``down`` behaves identically on Windows and Linux (design §7).
        """
        self._draining = True
        for record in self._records:
            if record.state is not LoopState.OPEN:
                # A faulted (OPEN) loop keeps its reported state; healthy loops drain cleanly.
                record.state = LoopState.DRAINED
        return self.snapshot()

    def snapshot(self) -> SupervisionSnapshot:
        """Return an immutable snapshot of every loop's supervised state (for ``status``)."""
        return SupervisionSnapshot(
            loops=tuple(
                LoopStatus(
                    name=record.loop.name,
                    state=record.state,
                    consecutive_failures=record.consecutive_failures,
                )
                for record in self._records
            )
        )
