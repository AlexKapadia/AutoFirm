"""Tests for the supervisor: healthy ticks, restart-with-backoff, circuit-break, graceful drain."""

from __future__ import annotations

import dataclasses

import pytest

from autofirm.runtime.platform_runtime import Platform, SupervisedLoop
from autofirm.runtime.platform_supervisor import (
    DEFAULT_MAX_RESTARTS,
    LoopState,
    LoopStatus,
    PlatformSupervisor,
    SupervisionSnapshot,
)


def _platform_with(loops: tuple[SupervisedLoop, ...]) -> Platform:
    return Platform(capabilities=(), loops=loops)


def test_supervisor__healthy_loop_stays_ready_across_cycles() -> None:
    """A loop whose tick never raises stays READY and accumulates no failures."""
    ticks = {"n": 0}

    def _tick() -> None:
        ticks["n"] += 1

    supervisor = PlatformSupervisor(_platform_with((SupervisedLoop(name="ok", tick=_tick),)))
    snapshot = supervisor.run_cycles(5)
    assert ticks["n"] == 5  # ticked every cycle
    assert snapshot.loops[0].state is LoopState.READY
    assert snapshot.all_healthy


def test_supervisor__a_crashing_then_recovering_loop_returns_to_ready() -> None:
    """A loop that crashes once then succeeds is RESTARTING then back to READY (clears streak)."""
    calls = {"n": 0}

    def _tick() -> None:
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError("transient")

    supervisor = PlatformSupervisor(_platform_with((SupervisedLoop(name="flaky", tick=_tick),)))
    supervisor.run_cycles(1)  # crash -> RESTARTING
    assert supervisor.snapshot().loops[0].state is LoopState.RESTARTING
    supervisor.run_cycles(1)  # recover -> READY
    final = supervisor.snapshot().loops[0]
    assert final.state is LoopState.READY
    assert final.consecutive_failures == 0


def test_supervisor__a_persistently_crashing_loop_trips_the_breaker_open() -> None:
    """A loop that always crashes trips its breaker OPEN after the restart budget (never silent)."""

    def _always_crash() -> None:
        raise RuntimeError("permanently broken")

    supervisor = PlatformSupervisor(
        _platform_with((SupervisedLoop(name="dead", tick=_always_crash),))
    )
    snapshot = supervisor.run_cycles(DEFAULT_MAX_RESTARTS + 2)
    assert snapshot.loops[0].state is LoopState.OPEN
    assert not snapshot.all_healthy  # the fault is reported, not hidden


def test_supervisor__an_open_loop_is_not_ticked_again() -> None:
    """Once OPEN, the loop is no longer ticked (it would just crash) — count stops climbing."""
    calls = {"n": 0}

    def _crash() -> None:
        calls["n"] += 1
        raise RuntimeError("broken")

    supervisor = PlatformSupervisor(
        _platform_with((SupervisedLoop(name="dead", tick=_crash),)), max_restarts=2
    )
    supervisor.run_cycles(3)  # 3 crashes -> trips OPEN (budget 2)
    calls_at_open = calls["n"]
    supervisor.run_cycles(5)  # further cycles must NOT tick the open loop
    assert calls["n"] == calls_at_open


def test_supervisor__drain_marks_healthy_loops_drained_cross_os() -> None:
    """drain() cooperatively stops every healthy loop (graceful down, no POSIX signals)."""
    supervisor = PlatformSupervisor(
        _platform_with((SupervisedLoop(name="a", tick=lambda: None),))
    )
    supervisor.run_cycles(2)
    snapshot = supervisor.drain()
    assert snapshot.loops[0].state is LoopState.DRAINED


def test_supervisor__drain_preserves_a_tripped_loops_reported_open_state() -> None:
    """A loop that already tripped OPEN keeps its reported fault through a drain (not hidden)."""

    def _crash() -> None:
        raise RuntimeError("broken")

    supervisor = PlatformSupervisor(
        _platform_with((SupervisedLoop(name="dead", tick=_crash),)), max_restarts=1
    )
    supervisor.run_cycles(3)
    snapshot = supervisor.drain()
    assert snapshot.loops[0].state is LoopState.OPEN  # fault preserved across drain


def test_supervisor__draining_stops_further_cycles() -> None:
    """After drain(), run_cycles does no more work (the cooperative flag is honoured)."""
    calls = {"n": 0}

    def _tick() -> None:
        calls["n"] += 1

    supervisor = PlatformSupervisor(_platform_with((SupervisedLoop(name="a", tick=_tick),)))
    supervisor.drain()
    supervisor.run_cycles(5)
    assert calls["n"] == 0  # nothing ticked after a drain


def test_supervisor__rejects_non_positive_restart_budget() -> None:
    """A non-positive max_restarts is refused (would trip every loop instantly — fail-closed)."""
    with pytest.raises(ValueError, match="max_restarts must be >= 1"):
        PlatformSupervisor(_platform_with(()), max_restarts=0)


def test_supervisor__run_cycles_with_zero_is_a_no_op() -> None:
    """Running zero cycles ticks nothing and reports the initial READY state."""
    supervisor = PlatformSupervisor(
        _platform_with((SupervisedLoop(name="a", tick=lambda: None),))
    )
    snapshot = supervisor.run_cycles(0)
    assert snapshot.loops[0].state is LoopState.READY


# ---------------------------------------------------------------------------
# Mutation-hardening (CLAUDE.md §3.6): pin enum/status string contracts, the
# frozen snapshots, the exact restart-budget arithmetic and its boundary, and
# the zero/negative-cycle clamp. Each kills a specific surviving mutant.
# ---------------------------------------------------------------------------


def _crash() -> None:
    raise RuntimeError("always broken")


def test_loop_state__enum_values_are_the_exact_status_strings() -> None:
    """The LoopState wire values are pinned exactly (kills value-wrap and ``=None`` mutants).

    These strings are surfaced by ``status``; a mutant that wraps or nulls a value would
    corrupt the reported loop state, so every member's value is asserted literally.
    """
    assert LoopState.READY.value == "ready"
    assert LoopState.RESTARTING.value == "restarting"
    assert LoopState.OPEN.value == "open"
    assert LoopState.DRAINED.value == "drained"


def test_loop_status__is_frozen_immutable() -> None:
    """A LoopStatus snapshot row is immutable (kills the ``frozen=True`` mutant)."""
    status = LoopStatus(name="a", state=LoopState.READY, consecutive_failures=0)
    with pytest.raises(dataclasses.FrozenInstanceError):
        status.state = LoopState.OPEN  # type: ignore[misc]


def test_supervision_snapshot__is_frozen_immutable() -> None:
    """A SupervisionSnapshot is immutable (kills the ``frozen=True`` mutant)."""
    snapshot = SupervisionSnapshot()
    with pytest.raises(dataclasses.FrozenInstanceError):
        snapshot.loops = ()  # type: ignore[misc]


def test_supervision_snapshot__defaults_to_empty_loops_tuple() -> None:
    """An empty snapshot defaults to ``()`` loops (kills the ``= None`` default mutant)."""
    snapshot = SupervisionSnapshot()
    assert snapshot.loops == ()
    assert snapshot.all_healthy  # no loop is OPEN -> vacuously healthy


def test_supervisor__initial_state_is_not_draining() -> None:
    """A freshly-built supervisor is NOT draining (kills the ``self._draining = None`` mutant).

    The draining flag is a strict boolean: it starts ``False`` (run proceeds) and only
    ``drain()`` flips it ``True``. ``None`` would be falsy-equivalent at runtime, so the exact
    boolean initial state is asserted to prove the documented start condition.
    """
    supervisor = PlatformSupervisor(_platform_with(()))
    assert supervisor._draining is False


def test_supervisor__rejects_non_positive_restart_budget_message_is_exact() -> None:
    """The mis-configuration error text is pinned EXACTLY (kills the string-wrap mutant)."""
    with pytest.raises(ValueError) as exc:
        PlatformSupervisor(_platform_with(()), max_restarts=0)
    assert str(exc.value) == "max_restarts must be >= 1"


def test_supervisor__default_restart_budget_is_three_cycles() -> None:
    """With the DEFAULT budget a loop trips OPEN only on the 4th crash (kills the ``3`` mutant).

    Four always-crashing cycles must trip the breaker under ``DEFAULT_MAX_RESTARTS = 3``
    (4 > 3); a mutant raising the default to 4 would leave it RESTARTING after four crashes.
    """
    assert DEFAULT_MAX_RESTARTS == 3
    supervisor = PlatformSupervisor(_platform_with((SupervisedLoop(name="d", tick=_crash),)))
    snapshot = supervisor.run_cycles(4)
    assert snapshot.loops[0].state is LoopState.OPEN


def test_supervisor__single_crash_increments_failures_by_exactly_one() -> None:
    """One crash records exactly ONE failure (kills the ``+= 2`` increment mutant)."""
    supervisor = PlatformSupervisor(_platform_with((SupervisedLoop(name="c", tick=_crash),)))
    supervisor.run_cycles(1)
    record = supervisor.snapshot().loops[0]
    assert record.consecutive_failures == 1
    assert record.state is LoopState.RESTARTING


def test_supervisor__breaker_trips_strictly_above_budget_not_at_it() -> None:
    """At EXACTLY the budget the loop is still RESTARTING (kills the ``>`` -> ``>=`` mutant).

    With ``max_restarts=2`` a second crash leaves failures==2, which must NOT trip the breaker
    (``2 > 2`` is False); a mutant using ``>=`` would trip OPEN one crash too early.
    """
    supervisor = PlatformSupervisor(
        _platform_with((SupervisedLoop(name="b", tick=_crash),)), max_restarts=2
    )
    supervisor.run_cycles(2)  # exactly budget-many crashes
    at_budget = supervisor.snapshot().loops[0]
    assert at_budget.consecutive_failures == 2
    assert at_budget.state is LoopState.RESTARTING  # NOT yet OPEN


def test_supervisor__zero_cycles_ticks_zero_times() -> None:
    """run_cycles(0) ticks the loop ZERO times (kills the ``max(cycles, 1)`` clamp mutant)."""
    ticks = {"n": 0}

    def _count() -> None:
        ticks["n"] += 1

    supervisor = PlatformSupervisor(_platform_with((SupervisedLoop(name="z", tick=_count),)))
    supervisor.run_cycles(0)
    assert ticks["n"] == 0  # a mutant clamping to range(1) would tick once


def test_supervisor__negative_cycles_ticks_zero_times() -> None:
    """A negative cycle count is clamped to zero work (boundary for ``max(cycles, 0)``)."""
    ticks = {"n": 0}

    def _count() -> None:
        ticks["n"] += 1

    supervisor = PlatformSupervisor(_platform_with((SupervisedLoop(name="n", tick=_count),)))
    supervisor.run_cycles(-5)
    assert ticks["n"] == 0
