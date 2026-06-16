"""Heartbeat plane: recurring cadences as a first-class, deterministic primitive.

What this package does
----------------------
Implements AutoFirm's first-class *heartbeat* primitive — named recurring beats
(each with a positive interval and a callback/check) registered on a
:class:`~autofirm.heartbeat.heartbeat_scheduler.HeartbeatScheduler` that, when
driven by an **injected clock**, fires exactly the beats that are due for a given
advance of time. It is the in-process scheduling abstraction behind the AutoFirm
ethos line "everything has a heartbeat" (the North Star alignment review, the
design check-in, the market-intelligence sweep all register as beats).

Determinism is the whole point: ticks are driven by an injected clock, never the
wall clock, so a test advances time explicitly and two runs with the same advance
fire the same beats in the same order. Beats are idempotent (a beat already
in-flight is not re-entered) and registration is fail-closed (no duplicate names,
positive intervals only).

Where it sits
-------------
This is the **in-process** scheduler only. The OS-level auto-resume watchdog and
the orchestrator's cron are separate, deliberately-not-duplicated concerns
(CLAUDE.md §4.8); this primitive is what they (or any in-process loop) would tick.
"""

from __future__ import annotations

from autofirm.heartbeat.heartbeat_scheduler import (
    DuplicateBeatError,
    HeartbeatScheduler,
)
from autofirm.heartbeat.injected_heartbeat_clock import (
    HeartbeatClock,
    ManualHeartbeatClock,
)
from autofirm.heartbeat.recurring_beat_definition import BeatDefinition

__all__ = [
    "BeatDefinition",
    "DuplicateBeatError",
    "HeartbeatClock",
    "HeartbeatScheduler",
    "ManualHeartbeatClock",
]
