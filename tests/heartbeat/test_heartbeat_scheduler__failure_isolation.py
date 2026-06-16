"""Scheduler failure-isolation tests: one bad beat must never wedge its siblings.

What these prove
----------------
The resilience fix (CLAUDE.md §3.2 institution-grade, fail-closed-but-resilient):
a beat whose callback RAISES must not abort the tick. Each due beat fires
independently; a raising callback is caught, recorded as a structured
:class:`BeatFailure` in the returned :class:`TickResult`, and the remaining due
beats still fire — over MULTIPLE consecutive ticks (the exact wedging scenario the
old ``try``/``finally`` re-raise caused).

Every test here is written to FAIL on the old behavior (where the exception
propagated out of ``tick`` and starved every later-sorted beat) and pass on the
new isolating behavior. Includes a Hypothesis property over arbitrary mixes of
healthy/failing beats: every healthy due beat ALWAYS fires regardless of how many
siblings fail. Synthetic only; injected clock; no network, no wall-clock.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from hypothesis import given
from hypothesis import strategies as st

from autofirm.heartbeat.heartbeat_scheduler import HeartbeatScheduler
from autofirm.heartbeat.injected_heartbeat_clock import ManualHeartbeatClock
from autofirm.heartbeat.recurring_beat_definition import BeatDefinition
from autofirm.heartbeat.tick_result import BeatFailure, TickResult

# A fixed, deterministic epoch so every due-time comparison is reproducible.
_EPOCH = datetime(2025, 1, 1, tzinfo=UTC)


class _Counter:
    """A healthy callback that records how many times it was invoked."""

    def __init__(self) -> None:
        self.calls = 0

    def __call__(self) -> None:
        self.calls += 1


class _Boom:
    """A persistently-failing callback that always raises and counts attempts."""

    def __init__(self, message: str = "boom") -> None:
        self.calls = 0
        self._message = message

    def __call__(self) -> None:
        self.calls += 1
        raise RuntimeError(self._message)


def _new_scheduler() -> tuple[HeartbeatScheduler, ManualHeartbeatClock]:
    clock = ManualHeartbeatClock(start=_EPOCH)
    return HeartbeatScheduler(clock), clock


@pytest.mark.unit
def test_failing_beat_does_not_block_a_later_sorted_sibling() -> None:
    # "a-boom" sorts BEFORE "z-ok": on the OLD code the exception from a-boom
    # aborted the loop before z-ok fired. The fix must fire z-ok regardless.
    sched, clock = _new_scheduler()
    boom = _Boom()
    ok = _Counter()
    sched.register(BeatDefinition(name="a-boom", interval_seconds=10.0, callback=boom))
    sched.register(BeatDefinition(name="z-ok", interval_seconds=10.0, callback=ok))

    clock.advance(10.0)
    result = sched.tick()

    assert ok.calls == 1  # the healthy sibling fired despite the earlier failure
    assert boom.calls == 1  # the failing beat was attempted
    assert result.fired == ("z-ok",)  # only the clean beat is in `fired`
    assert result.failed_names == ("a-boom",)  # the failure is surfaced, not hidden


@pytest.mark.unit
def test_persistent_failure_does_not_wedge_siblings_over_many_ticks() -> None:
    # The exact wedging scenario: a beat that fails on EVERY tick must not starve
    # its sibling on EVERY tick. Old behavior: ok.calls would stay at 0 forever.
    sched, clock = _new_scheduler()
    boom = _Boom()
    ok = _Counter()
    sched.register(BeatDefinition(name="a-boom", interval_seconds=10.0, callback=boom))
    sched.register(BeatDefinition(name="z-ok", interval_seconds=10.0, callback=ok))

    for expected in range(1, 6):  # five consecutive due ticks
        clock.advance(10.0)
        result = sched.tick()
        assert ok.calls == expected  # healthy beat fires every single tick
        assert boom.calls == expected  # failing beat keeps being retried
        assert result.failed_names == ("a-boom",)  # failure surfaced each tick


@pytest.mark.unit
def test_tick_never_raises_even_when_every_due_beat_fails() -> None:
    # All due beats fail: the tick must still return cleanly with every failure
    # surfaced, never propagate an exception out (which would crash the driver).
    sched, clock = _new_scheduler()
    booms = {name: _Boom(f"boom-{name}") for name in ("a", "b", "c")}
    for name, cb in booms.items():
        sched.register(BeatDefinition(name=name, interval_seconds=10.0, callback=cb))

    clock.advance(10.0)
    result = sched.tick()  # must not raise

    assert result.fired == ()
    assert result.failed_names == ("a", "b", "c")  # all failures surfaced, in order
    for failure in result.failures:
        assert isinstance(failure, BeatFailure)
        assert f"boom-{failure.name}" in failure.error  # name + error captured


@pytest.mark.unit
def test_failure_carries_the_exception_repr() -> None:
    sched, clock = _new_scheduler()
    sched.register(
        BeatDefinition(name="x", interval_seconds=5.0, callback=_Boom("disk full")),
    )
    clock.advance(5.0)
    result = sched.tick()

    assert len(result.failures) == 1
    failure = result.failures[0]
    assert failure.name == "x"
    assert "disk full" in failure.error  # the real error message is surfaced
    assert "RuntimeError" in failure.error  # the exception type too


@pytest.mark.unit
def test_healthy_beats_fire_in_deterministic_sorted_order_with_failures_mixed_in() -> None:
    # Healthy beats interleaved with failing ones must still fire in stable name
    # order; failures appear in the same fire order in `failures`.
    sched, clock = _new_scheduler()
    order: list[str] = []
    for name in ("a-ok", "m-boom", "z-ok"):
        if name.endswith("boom"):
            sched.register(BeatDefinition(name=name, interval_seconds=1.0, callback=_Boom()))
        else:
            sched.register(
                BeatDefinition(
                    name=name,
                    interval_seconds=1.0,
                    callback=lambda n=name: order.append(n),  # type: ignore[misc]
                ),
            )

    clock.advance(1.0)
    result = sched.tick()

    assert order == ["a-ok", "z-ok"]  # healthy beats fired in sorted order
    assert result.fired == ("a-ok", "z-ok")
    assert result.failed_names == ("m-boom",)
    assert result.due_count == 3  # all three due beats were acted on


@pytest.mark.unit
def test_failing_beat_reschedules_normally_and_does_not_refire_instantly() -> None:
    # A failing beat must roll its schedule forward like a healthy one: it is due
    # once per interval, never instantly-due-again (which would busy-spin).
    sched, clock = _new_scheduler()
    boom = _Boom()
    sched.register(BeatDefinition(name="b", interval_seconds=10.0, callback=boom))

    clock.advance(10.0)
    assert sched.tick().failed_names == ("b",)
    assert boom.calls == 1
    # Immediately tick again WITHOUT advancing: the beat is not due again.
    assert sched.tick() == TickResult(fired=(), failures=())
    assert boom.calls == 1  # not retried until the next interval boundary


@pytest.mark.unit
def test_idempotency_holds_when_callback_reenters_tick_and_then_raises() -> None:
    # A reentrant callback that ticks again (no double-fire) AND raises must be
    # isolated: the reentrant tick sees the beat in-flight (skips it) and the
    # outer tick records the failure without wedging anything.
    sched, clock = _new_scheduler()
    calls = {"n": 0}

    def reentrant_then_boom() -> None:
        calls["n"] += 1
        inner = sched.tick()  # re-enters: self is in-flight, must be skipped
        assert inner == TickResult(fired=(), failures=())  # no double-fire
        raise RuntimeError("after reentry")

    sched.register(BeatDefinition(name="r", interval_seconds=10.0, callback=reentrant_then_boom))
    clock.advance(10.0)
    result = sched.tick()

    assert calls["n"] == 1  # fired exactly once (idempotent), not re-entered
    assert result.failed_names == ("r",)  # the raise is still surfaced


@pytest.mark.property
@given(
    # Arbitrary mixes of healthy (True) / failing (False) beats, 1..12 of them.
    health=st.lists(st.booleans(), min_size=1, max_size=12),
    ticks=st.integers(min_value=1, max_value=5),
)
def test_every_healthy_due_beat_always_fires_regardless_of_failing_siblings(
    health: list[bool],
    ticks: int,
) -> None:
    """Property: no matter how many siblings fail, every healthy due beat fires.

    This is the generalised wedging guarantee — for any mix of healthy/failing
    beats and any number of consecutive due ticks, each healthy beat's call count
    equals the number of ticks (never starved), and each failing beat is surfaced
    every tick. On the old behavior a single failing beat could drive a healthy
    sibling's count to 0.
    """
    clock = ManualHeartbeatClock(start=_EPOCH)
    sched = HeartbeatScheduler(clock)
    healthy: dict[str, _Counter] = {}
    failing: set[str] = set()
    # Zero-padded names keep a known deterministic sort order across the mix.
    for index, is_healthy in enumerate(health):
        name = f"beat-{index:03d}"
        if is_healthy:
            counter = _Counter()
            healthy[name] = counter
            sched.register(BeatDefinition(name=name, interval_seconds=10.0, callback=counter))
        else:
            failing.add(name)
            sched.register(BeatDefinition(name=name, interval_seconds=10.0, callback=_Boom()))

    for tick_index in range(1, ticks + 1):
        clock.advance(10.0)
        result = sched.tick()
        # Every healthy beat fired on every tick — never starved by a failing one.
        for name, counter in healthy.items():
            assert counter.calls == tick_index, name
            assert name in result.fired
        # Every failing beat is surfaced (auditable), never silently swallowed.
        assert set(result.failed_names) == failing
        # Every due beat was acted on exactly once this tick.
        assert result.due_count == len(health)
