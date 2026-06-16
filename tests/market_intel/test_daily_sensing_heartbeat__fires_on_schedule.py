"""Daily-beat tests: the sensing sweep fires exactly once per day, via the clock.

What these prove
----------------
The daily cadence is deterministic and driven only by the injected clock — never
the wall clock. Advancing less than a day and ticking fires nothing; advancing
exactly a day fires the sweep exactly once; advancing several days coalesces into a
single fire (no catch-up burst). The beat actually runs the sweep (the on_result
sink receives the SweepResult) and registering the beat twice is refused fail-closed
by the scheduler. Property-based: number of fires over N daily ticks == N, and a
sub-day advance never fires. No sleeping anywhere.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from hypothesis import given
from hypothesis import strategies as st

from autofirm.heartbeat.heartbeat_scheduler import DuplicateBeatError, HeartbeatScheduler
from autofirm.heartbeat.injected_heartbeat_clock import ManualHeartbeatClock
from autofirm.market_intel.daily_sensing_heartbeat import (
    DAILY_INTERVAL_SECONDS,
    register_daily_sensing_beat,
)
from autofirm.market_intel.market_insight_audit_sink import InMemoryMarketInsightAuditSink
from autofirm.market_intel.market_insight_contract import InsightCategory
from autofirm.market_intel.market_sensing_sweep import MarketSensingSweep, SweepResult
from autofirm.market_intel.market_signal_source import (
    InMemoryMarketSignalSource,
    RawMarketSignal,
)

_TEAM = "growth-team"
_ROLES = frozenset({_TEAM})
_EPOCH = datetime(2025, 6, 1, tzinfo=UTC)


def _build() -> tuple[HeartbeatScheduler, ManualHeartbeatClock, list[SweepResult]]:
    clock = ManualHeartbeatClock(start=_EPOCH)
    sweep = MarketSensingSweep(
        sources=(
            InMemoryMarketSignalSource(
                "feed",
                (
                    RawMarketSignal(
                        source_name="feed",
                        observation="market is moving",
                        proposed_category=InsightCategory.MARKET_TREND,
                    ),
                ),
            ),
        ),
        audit_sink=InMemoryMarketInsightAuditSink(),
        clock=clock,
        owning_team=_TEAM,
        known_roles=_ROLES,
    )
    scheduler = HeartbeatScheduler(clock)
    results: list[SweepResult] = []
    register_daily_sensing_beat(scheduler, sweep, on_result=results.append)
    return scheduler, clock, results


def test_sub_day_advance_does_not_fire() -> None:
    scheduler, clock, results = _build()
    clock.advance(DAILY_INTERVAL_SECONDS - 1)  # one second short of a day
    fired = scheduler.tick()
    assert fired.fired == ()
    assert results == []


def test_exact_day_fires_sweep_once() -> None:
    scheduler, clock, results = _build()
    clock.advance(DAILY_INTERVAL_SECONDS)  # exactly one day
    fired = scheduler.tick()
    assert fired.fired == ("market-intel.daily-sensing-sweep",)
    assert len(results) == 1
    assert len(results[0].insights) == 1  # the sweep really ran


def test_multi_day_jump_coalesces_to_single_fire() -> None:
    scheduler, clock, results = _build()
    clock.advance(DAILY_INTERVAL_SECONDS * 5)  # five days at once
    scheduler.tick()
    assert len(results) == 1  # no catch-up burst — one fire, not five


def test_duplicate_registration_refused_fail_closed() -> None:
    scheduler, _clock, _results = _build()
    sweep = MarketSensingSweep(
        sources=(),
        audit_sink=InMemoryMarketInsightAuditSink(),
        clock=ManualHeartbeatClock(start=_EPOCH),
        owning_team=_TEAM,
        known_roles=_ROLES,
    )
    with pytest.raises(DuplicateBeatError):
        register_daily_sensing_beat(scheduler, sweep)


@pytest.mark.property
@given(days=st.integers(min_value=0, max_value=30))
def test_fires_once_per_daily_tick(days: int) -> None:
    # Advancing a full day then ticking, N times, fires exactly N times — the
    # cadence is an exact function of the injected clock (no drift, no double-fire).
    scheduler, clock, results = _build()
    for _ in range(days):
        clock.advance(DAILY_INTERVAL_SECONDS)
        scheduler.tick()
    assert len(results) == days


@pytest.mark.property
@given(seconds=st.integers(min_value=0, max_value=DAILY_INTERVAL_SECONDS - 1))
def test_never_fires_before_a_full_day(seconds: int) -> None:
    scheduler, clock, results = _build()
    clock.advance(seconds)
    scheduler.tick()
    assert results == []  # nothing under a full day ever fires
