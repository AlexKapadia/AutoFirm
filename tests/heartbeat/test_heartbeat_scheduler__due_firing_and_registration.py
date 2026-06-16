"""Scheduler core tests: due-time firing, ordering, coalescing, registration.

What these prove
----------------
The deterministic scheduling contract of :class:`HeartbeatScheduler` independent
of the failure-isolation path (covered in the sibling test file): beats fire only
once a full interval has elapsed, in stable name-sorted order; a large time jump
coalesces missed periods into a single fire (no catch-up burst); duplicate names
are refused fail-closed; and the in-flight guard prevents re-entrant double-fires.
Synthetic only; injected clock; no network, no wall-clock.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from hypothesis import given
from hypothesis import strategies as st

from autofirm.heartbeat.heartbeat_scheduler import DuplicateBeatError, HeartbeatScheduler
from autofirm.heartbeat.injected_heartbeat_clock import ManualHeartbeatClock
from autofirm.heartbeat.recurring_beat_definition import BeatDefinition
from autofirm.heartbeat.tick_result import TickResult

_EPOCH = datetime(2025, 1, 1, tzinfo=UTC)


class _Counter:
    def __init__(self) -> None:
        self.calls = 0

    def __call__(self) -> None:
        self.calls += 1


def _new() -> tuple[HeartbeatScheduler, ManualHeartbeatClock]:
    clock = ManualHeartbeatClock(start=_EPOCH)
    return HeartbeatScheduler(clock), clock


@pytest.mark.unit
def test_beat_does_not_fire_before_one_full_interval() -> None:
    sched, clock = _new()
    cb = _Counter()
    sched.register(BeatDefinition(name="b", interval_seconds=10.0, callback=cb))

    clock.advance(9.999)  # just under the interval — not yet due
    assert sched.tick() == TickResult(fired=(), failures=())
    assert cb.calls == 0


@pytest.mark.unit
def test_beat_fires_exactly_on_the_interval_boundary() -> None:
    sched, clock = _new()
    cb = _Counter()
    sched.register(BeatDefinition(name="b", interval_seconds=10.0, callback=cb))

    clock.advance(10.0)  # exactly due (now == next_due, fires)
    result = sched.tick()
    assert result.fired == ("b",)
    assert cb.calls == 1


@pytest.mark.unit
def test_large_jump_coalesces_missed_periods_into_a_single_fire() -> None:
    sched, clock = _new()
    cb = _Counter()
    sched.register(BeatDefinition(name="b", interval_seconds=10.0, callback=cb))

    clock.advance(95.0)  # nine missed periods — must fire ONCE, not nine times
    result = sched.tick()
    assert result.fired == ("b",)
    assert cb.calls == 1
    # And the next due time is strictly in the future (no instant re-fire).
    assert sched.tick() == TickResult(fired=(), failures=())
    assert cb.calls == 1


@pytest.mark.unit
def test_beats_fire_in_stable_name_sorted_order() -> None:
    sched, clock = _new()
    order: list[str] = []
    for name in ("zebra", "alpha", "mike"):  # registered out of order
        sched.register(
            BeatDefinition(
                name=name,
                interval_seconds=1.0,
                callback=lambda n=name: order.append(n),  # type: ignore[misc]
            ),
        )
    clock.advance(1.0)
    result = sched.tick()
    assert order == ["alpha", "mike", "zebra"]  # sorted, deterministic
    assert result.fired == ("alpha", "mike", "zebra")


@pytest.mark.unit
def test_duplicate_name_is_refused_fail_closed() -> None:
    sched, _ = _new()
    sched.register(BeatDefinition(name="dup", interval_seconds=1.0, callback=_Counter()))
    with pytest.raises(DuplicateBeatError, match="already registered"):
        sched.register(BeatDefinition(name="dup", interval_seconds=2.0, callback=_Counter()))


@pytest.mark.unit
def test_registered_names_is_a_readonly_snapshot() -> None:
    sched, _ = _new()
    sched.register(BeatDefinition(name="one", interval_seconds=1.0, callback=_Counter()))
    sched.register(BeatDefinition(name="two", interval_seconds=1.0, callback=_Counter()))
    assert sched.registered_names() == frozenset({"one", "two"})


@pytest.mark.unit
def test_in_flight_beat_is_not_re_entered_on_reentrant_tick() -> None:
    sched, clock = _new()
    calls = {"n": 0}

    def reentrant() -> None:
        calls["n"] += 1
        # Re-enter: self is in-flight and must be skipped (no double-fire).
        assert sched.tick() == TickResult(fired=(), failures=())

    sched.register(BeatDefinition(name="r", interval_seconds=10.0, callback=reentrant))
    clock.advance(10.0)
    result = sched.tick()
    assert calls["n"] == 1
    assert result.fired == ("r",)


@pytest.mark.unit
def test_empty_scheduler_tick_is_a_noop() -> None:
    sched, clock = _new()
    clock.advance(1000.0)
    assert sched.tick() == TickResult(fired=(), failures=())


@pytest.mark.property
@given(data=st.data())
def test_beat_fires_iff_a_full_interval_has_elapsed(data: st.DataObject) -> None:
    """Property: a beat fires on a tick exactly when the elapsed jump >= interval.

    Generalises the boundary test over arbitrary intervals/jumps, proving the
    due-time predicate has no off-by-one or sign error (mutation-relevant). The
    jump is bounded to a few thousand intervals so the (pre-existing) coalescing
    catch-up loop in ``_advance_due`` stays fast — the predicate under test is the
    fire/no-fire boundary, not the catch-up loop's worst-case throughput.
    """
    interval = data.draw(
        st.floats(min_value=0.001, max_value=1e5, allow_nan=False, allow_infinity=False)
    )
    # Bound jump relative to interval: cover both sides of the boundary without
    # forcing millions of catch-up steps for tiny intervals + huge jumps.
    jump = data.draw(
        st.floats(
            min_value=0.0,
            max_value=interval * 5000.0,
            allow_nan=False,
            allow_infinity=False,
        )
    )
    clock = ManualHeartbeatClock(start=_EPOCH)
    sched = HeartbeatScheduler(clock)
    cb = _Counter()
    sched.register(BeatDefinition(name="b", interval_seconds=interval, callback=cb))

    clock.advance(jump)
    result = sched.tick()
    should_fire = jump >= interval
    assert (result.fired == ("b",)) is should_fire
    assert cb.calls == (1 if should_fire else 0)
