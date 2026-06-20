"""system_clock: the production clock returns a timezone-aware UTC instant."""

from __future__ import annotations

from datetime import UTC, datetime

from autofirm.cockpit.composition.system_clock import SystemClock
from autofirm.org.org_identifiers import Clock


def test_now_is_timezone_aware_utc() -> None:
    now = SystemClock().now()
    assert isinstance(now, datetime)
    assert now.tzinfo is not None
    assert now.utcoffset() == UTC.utcoffset(None)


def test_system_clock_satisfies_clock_protocol() -> None:
    clock: Clock = SystemClock()
    assert isinstance(clock.now(), datetime)


def test_now_is_monotonic_nondecreasing() -> None:
    clock = SystemClock()
    first = clock.now()
    second = clock.now()
    assert second >= first  # wall-clock never goes backwards within a call pair
