"""Determinism-seam tests: FrozenClock and SequentialIdGenerator are reproducible.

Proves the injected clock and id-generator are deterministic and fail-closed on
bad seeds, so the whole engine is a pure function of its inputs (CLAUDE.md §3.11).
Synthetic only; no network.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from hypothesis import given
from hypothesis import strategies as st

from autofirm.org.org_identifiers import (
    Clock,
    FrozenClock,
    IdGenerator,
    SequentialIdGenerator,
)

_START = datetime(2026, 1, 1, tzinfo=UTC)


@pytest.mark.unit
def test_frozen_clock_without_step_is_constant() -> None:
    clock = FrozenClock(_START)
    assert clock.now() == _START
    assert clock.now() == _START  # never advances when step is 0
    assert isinstance(clock, Clock)  # satisfies the injected protocol


@pytest.mark.unit
def test_frozen_clock_advances_by_step() -> None:
    clock = FrozenClock(_START, step_seconds=5)
    assert clock.now() == _START
    assert clock.now() == _START + timedelta(seconds=5)
    assert clock.now() == _START + timedelta(seconds=10)


@pytest.mark.unit
def test_naive_datetime_is_refused() -> None:
    # fail-closed: a naive datetime makes 'now' ambiguous across zones.
    with pytest.raises(ValueError):
        FrozenClock(datetime(2026, 1, 1))  # no tzinfo


@pytest.mark.unit
def test_non_utc_start_is_normalised_to_utc() -> None:
    eastern = datetime(2026, 1, 1, 12, tzinfo=__import__("datetime").timezone(timedelta(hours=-5)))
    assert FrozenClock(eastern).now() == eastern.astimezone(UTC)


@pytest.mark.unit
def test_sequential_ids_are_monotonic_and_prefixed() -> None:
    gen = SequentialIdGenerator()
    assert gen.next_id("role") == "role-0"
    assert gen.next_id("role") == "role-1"
    assert gen.next_id("team") == "team-2"  # counter shared -> globally unique
    assert isinstance(gen, IdGenerator)


@pytest.mark.unit
def test_id_generator_start_offset() -> None:
    assert SequentialIdGenerator(start=10).next_id("r") == "r-10"


@pytest.mark.unit
def test_negative_start_is_refused() -> None:
    with pytest.raises(ValueError):
        SequentialIdGenerator(start=-1)  # fail-closed


@pytest.mark.unit
def test_empty_prefix_is_refused() -> None:
    with pytest.raises(ValueError):
        SequentialIdGenerator().next_id("")  # fail-closed: ids must be traceable


@pytest.mark.property
@given(n=st.integers(min_value=1, max_value=200), start=st.integers(min_value=0, max_value=50))
def test_ids_are_globally_unique_across_arbitrary_calls(n: int, start: int) -> None:
    gen = SequentialIdGenerator(start=start)
    prefixes = ["role", "team", "pod"]
    ids = [gen.next_id(prefixes[i % len(prefixes)]) for i in range(n)]
    assert len(set(ids)) == n  # never a collision (monotonic shared counter)
