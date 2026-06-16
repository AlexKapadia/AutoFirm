"""Register the DAILY market-sensing beat on the heartbeat scheduler.

What this does
--------------
Provides :func:`register_daily_sensing_beat`, which registers a single named beat
on an existing :class:`~autofirm.heartbeat.heartbeat_scheduler.HeartbeatScheduler`
that fires :meth:`MarketSensingSweep.run` once per day. The beat is driven by the
scheduler's injected clock — advancing the clock by a day and ticking fires the
sweep exactly once; advancing by less fires nothing — so the daily cadence is
fully deterministic and never sleeps on the wall clock.

Why it exists / where it sits
-----------------------------
This is the "always-on / heartbeat-driven" wiring of the market-intel plane: it
realises the AutoFirm ethos line "everything has a heartbeat" for market sensing,
reusing the existing heartbeat primitive rather than inventing a second scheduler.
The sweep records its latest :class:`SweepResult` so the caller (or the green-light
gate) can read what the most recent beat sensed.

Security / compliance invariants upheld
---------------------------------------
* **Determinism (§3.11):** the beat fires as a pure function of the injected
  clock advance; two identical advance sequences fire identically.
* **No wall-clock / no sleep:** the daily cadence is expressed as an interval in
  seconds the injected clock advances over — tests never sleep.
"""

from __future__ import annotations

from collections.abc import Callable

from autofirm.heartbeat.heartbeat_scheduler import HeartbeatScheduler
from autofirm.heartbeat.recurring_beat_definition import BeatDefinition
from autofirm.market_intel.market_sensing_sweep import MarketSensingSweep, SweepResult

__all__ = ["DAILY_INTERVAL_SECONDS", "register_daily_sensing_beat"]

# One day expressed in seconds — the beat's interval. The heartbeat scheduler
# compares this against injected-clock advances, so a 24h advance makes the beat
# due exactly once (missed days coalesce into one fire, never a catch-up burst).
DAILY_INTERVAL_SECONDS = 24 * 60 * 60

# The stable beat name the scheduler dedupes on (registering twice is refused
# fail-closed by the scheduler — one daily sensing beat, never two).
DAILY_SENSING_BEAT_NAME = "market-intel.daily-sensing-sweep"


def register_daily_sensing_beat(
    scheduler: HeartbeatScheduler,
    sweep: MarketSensingSweep,
    on_result: Callable[[SweepResult], None] | None = None,
) -> str:
    """Register the daily sensing beat and return its name.

    On each due day the beat runs ``sweep.run()`` and, if supplied, hands the
    resulting :class:`SweepResult` to ``on_result`` (e.g. to stash it for the
    green-light gate or flow it onward). The beat's callback is zero-argument as
    the heartbeat plane requires; it closes over ``sweep``/``on_result``.

    Args:
        scheduler: the heartbeat scheduler to register the beat on.
        sweep: the configured sensing sweep to run each day.
        on_result: optional sink for each day's sweep result.

    Returns:
        The registered beat name (``market-intel.daily-sensing-sweep``).
    """
    def _run_daily_sweep() -> None:
        # The beat callback: run one sensing sweep and surface its result. Any
        # failure here is isolated by the scheduler's per-beat try/except (one bad
        # day can never starve other beats) and surfaced in the tick result.
        result = sweep.run()
        if on_result is not None:
            on_result(result)

    scheduler.register(
        BeatDefinition(
            name=DAILY_SENSING_BEAT_NAME,
            interval_seconds=DAILY_INTERVAL_SECONDS,
            callback=_run_daily_sweep,
        )
    )
    return DAILY_SENSING_BEAT_NAME
