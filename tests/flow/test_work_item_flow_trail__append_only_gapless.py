"""Flow-trail tests: append-only, gapless, complete provenance — fail-closed.

Proves :class:`FlowTrail` only ever grows by exactly one consecutive seq and
refuses any gap, duplicate, or out-of-order insert (append-only, CLAUDE.md
§5.6/§3.8), and that :class:`FlowTransition` refuses a blank recipient or reason
(complete provenance). Includes Hypothesis properties that any correctly-sequenced
run is gapless and any wrong next-seq is refused. Synthetic only; no network.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from hypothesis import given
from hypothesis import strategies as st
from pydantic import ValidationError

from autofirm.flow.flow_state_machine import WorkState
from autofirm.flow.work_item_flow_trail import FlowTrail, FlowTransition

_TS = datetime(2025, 1, 1, tzinfo=UTC)


def _transition(seq: int, reason: str = "r", to_role: str = "cto") -> FlowTransition:
    return FlowTransition(
        seq=seq,
        from_state=WorkState.ASSIGNED,
        to_state=WorkState.IN_PROGRESS,
        from_role="coo",
        to_role=to_role,
        reason=reason,
        timestamp=_TS,
    )


@pytest.mark.unit
def test_append_extends_by_one_and_is_immutable() -> None:
    trail = FlowTrail()
    assert trail.next_seq == 0
    extended = trail.append(_transition(0))
    assert trail.transitions == ()  # original untouched (append-only)
    assert extended.next_seq == 1
    assert extended.is_gapless()


@pytest.mark.unit
@pytest.mark.parametrize("bad_seq", [1, 2, 5])
def test_gap_seq_is_refused_on_empty(bad_seq: int) -> None:
    with pytest.raises(ValueError, match="non-consecutive flow seq"):
        FlowTrail().append(_transition(bad_seq))


@pytest.mark.unit
def test_duplicate_seq_is_refused() -> None:
    trail = FlowTrail().append(_transition(0))
    with pytest.raises(ValueError, match="non-consecutive flow seq"):
        trail.append(_transition(0))  # seq 0 again -> would overwrite -> refused


@pytest.mark.unit
def test_negative_seq_refused_at_construction() -> None:
    with pytest.raises(ValidationError):
        _transition(-1)


@pytest.mark.unit
@pytest.mark.parametrize("blank", ["", "   ", "\t"])
def test_blank_reason_or_role_refused(blank: str) -> None:
    # fail-closed: an unexplained move or anonymous recipient breaks provenance.
    with pytest.raises(ValidationError):
        _transition(0, reason=blank)
    with pytest.raises(ValidationError):
        _transition(0, to_role=blank)


@pytest.mark.property
@given(n=st.integers(min_value=0, max_value=60))
def test_correctly_sequenced_appends_are_always_gapless(n: int) -> None:
    trail = FlowTrail()
    for i in range(n):
        trail = trail.append(_transition(i, reason=f"e{i}"))
    assert trail.is_gapless()
    assert tuple(t.seq for t in trail.transitions) == tuple(range(n))
    assert trail.next_seq == n


@pytest.mark.property
@given(good=st.integers(min_value=0, max_value=20), wrong=st.integers(min_value=-5, max_value=40))
def test_any_wrong_next_seq_is_refused(good: int, wrong: int) -> None:
    trail = FlowTrail()
    for i in range(good):
        trail = trail.append(_transition(i))
    if wrong == good:
        assert trail.append(_transition(wrong)).is_gapless()  # the ONE correct value
    else:
        # Refused either at the trail (gap/overwrite) or at construction (seq < 0);
        # both are valid fail-closed paths. Only seq==good is ever accepted.
        with pytest.raises((ValueError, ValidationError)):
            trail.append(_transition(wrong))
