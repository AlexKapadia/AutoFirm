"""Beat-definition tests: fail-closed validation of name and interval.

Proves :class:`BeatDefinition` refuses a blank name and any non-positive interval
(0 would be "due every instant"; negative is meaningless) — the fail-closed
registration guard (CLAUDE.md §5.6). A valid beat is frozen. Includes a Hypothesis
property that every non-positive interval is refused and every positive one is
accepted. Synthetic only; no network, no wall-clock.
"""

from __future__ import annotations

import math

import pytest
from hypothesis import given
from hypothesis import strategies as st
from pydantic import ValidationError

from autofirm.heartbeat.recurring_beat_definition import BeatDefinition


def _noop() -> None:
    return None


@pytest.mark.unit
def test_valid_beat_is_frozen() -> None:
    beat = BeatDefinition(name="north-star", interval_seconds=1800.0, callback=_noop)
    assert beat.name == "north-star"
    with pytest.raises(ValidationError):  # frozen — contract cannot mutate
        beat.interval_seconds = 60.0  # type: ignore[misc]


@pytest.mark.unit
@pytest.mark.parametrize("blank", ["", "   ", "\t"])
def test_blank_name_refused(blank: str) -> None:
    with pytest.raises(ValidationError, match="beat name must be non-empty"):
        BeatDefinition(name=blank, interval_seconds=1.0, callback=_noop)


@pytest.mark.unit
@pytest.mark.parametrize("bad", [0.0, -0.0, -1.0, -1e-9, -100.0])
def test_non_positive_interval_refused(bad: float) -> None:
    # fail-closed: a 0 interval is "due every instant" (busy-loop); negative is
    # meaningless. Only a strictly positive period is a valid beat.
    with pytest.raises(ValidationError, match="strictly positive"):
        BeatDefinition(name="b", interval_seconds=bad, callback=_noop)


@pytest.mark.property
@given(
    interval=st.floats(allow_nan=False, allow_infinity=False, min_value=-1e6, max_value=1e6)
)
def test_only_strictly_positive_intervals_accepted(interval: float) -> None:
    if interval > 0 and not math.isclose(interval, 0.0):
        beat = BeatDefinition(name="b", interval_seconds=interval, callback=_noop)
        assert beat.interval_seconds == interval
    else:
        with pytest.raises(ValidationError):
            BeatDefinition(name="b", interval_seconds=interval, callback=_noop)
