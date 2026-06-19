"""Tests for the supervisor: healthy ticks, restart-with-backoff, circuit-break, graceful drain."""

from __future__ import annotations

import pytest

from autofirm.runtime.platform_runtime import Platform, SupervisedLoop
from autofirm.runtime.platform_supervisor import (
    DEFAULT_MAX_RESTARTS,
    LoopState,
    PlatformSupervisor,
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
