"""Adversarial tests for the injectable determinism seams (A4; §3.11).

Proves teeth (CLAUDE.md §3.6): the clock refuses naive datetimes (fail-closed),
advances exactly by its step, and the id-generator refuses a negative start and an
empty prefix and emits strictly monotonic ids. Designed to KILL mutants on the
tz-aware guard, the step advance, and the counter increment.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from autofirm.memory.memory_identifiers import (
    FrozenMemoryClock,
    SequentialMemoryIdGenerator,
)

_EPOCH = datetime(2025, 1, 1, tzinfo=UTC)


def test_clock_refuses_naive_datetime_fail_closed() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        FrozenMemoryClock(datetime(2025, 1, 1))  # intentionally naive -> must be refused


def test_clock_frozen_without_step_does_not_advance() -> None:
    clock = FrozenMemoryClock(_EPOCH)  # step defaults to 0 -> frozen
    assert clock.now() == _EPOCH
    assert clock.now() == _EPOCH  # still frozen on the second read


def test_clock_advances_exactly_by_step() -> None:
    clock = FrozenMemoryClock(_EPOCH, step_seconds=60.0)
    first = clock.now()
    second = clock.now()
    assert first == _EPOCH
    assert second == _EPOCH + timedelta(seconds=60)  # exact step, killing off-by-one


def test_clock_normalises_aware_input_to_utc() -> None:
    # A tz-aware non-UTC instant is converted to UTC so all timestamps compare.
    from datetime import timezone

    plus2 = timezone(timedelta(hours=2))
    clock = FrozenMemoryClock(datetime(2025, 1, 1, 12, tzinfo=plus2))
    assert clock.now() == datetime(2025, 1, 1, 10, tzinfo=UTC)


def test_id_generator_refuses_negative_start() -> None:
    with pytest.raises(ValueError, match="counter start must be >= 0"):
        SequentialMemoryIdGenerator(start=-1)


def test_id_generator_refuses_empty_prefix() -> None:
    gen = SequentialMemoryIdGenerator()
    with pytest.raises(ValueError, match="prefix must be non-empty"):
        gen.next_id("")


def test_id_generator_is_monotonic_and_shared_across_prefixes() -> None:
    gen = SequentialMemoryIdGenerator(start=5)
    assert gen.next_id("mem") == "mem-5"
    assert gen.next_id("ref") == "ref-6"  # counter shared -> globally unique
    assert gen.next_id("mem") == "mem-7"
