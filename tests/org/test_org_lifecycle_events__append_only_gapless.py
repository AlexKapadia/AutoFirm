"""Audit-trail tests: append-only, gapless, monotonic seq — fail-closed.

Proves :class:`OrgAuditTrail` only ever grows by exactly one consecutive seq and
refuses any gap, duplicate, or out-of-order insert (the append-only invariant,
CLAUDE.md §5.6/§3.8). Includes a Hypothesis property test that an arbitrary run of
correctly-sequenced appends always yields a 0..n-1 gapless seq sequence, and that
NO out-of-order seq is ever accepted. Synthetic only; no network.
"""

from __future__ import annotations

import pytest
from hypothesis import given
from hypothesis import strategies as st
from pydantic import ValidationError

from autofirm.org.org_lifecycle_events import OrgAuditTrail, OrgEvent, OrgEventKind

from .synthetic_clock_for_events import FIXED_TS


def _event(seq: int, detail: str = "x") -> OrgEvent:
    return OrgEvent(
        seq=seq,
        kind=OrgEventKind.ROLE_HIRED,
        subject_role_id="r",
        detail=detail,
        timestamp=FIXED_TS,
    )


@pytest.mark.unit
def test_append_extends_by_one_at_next_seq() -> None:
    trail = OrgAuditTrail()
    assert trail.next_seq == 0
    trail = trail.append(_event(0))
    assert trail.next_seq == 1
    trail = trail.append(_event(1))
    assert tuple(e.seq for e in trail.events) == (0, 1)


@pytest.mark.unit
def test_append_returns_new_trail_original_unchanged() -> None:
    trail = OrgAuditTrail()
    extended = trail.append(_event(0))
    assert trail.events == ()  # original untouched (immutable, append-only)
    assert len(extended.events) == 1


@pytest.mark.unit
@pytest.mark.parametrize("bad_seq", [1, 2, 5, -1])
def test_gap_or_overwrite_seq_is_refused_on_empty(bad_seq: int) -> None:
    # fail-closed: only seq==0 is accepted on an empty trail; a gap/overwrite that
    # could rewrite history is refused.
    with pytest.raises((ValueError, Exception)):
        OrgAuditTrail().append(_event(bad_seq))


@pytest.mark.unit
def test_duplicate_seq_is_refused() -> None:
    trail = OrgAuditTrail().append(_event(0))
    with pytest.raises(ValueError):
        trail.append(_event(0))  # seq 0 again -> would overwrite -> refused


@pytest.mark.unit
def test_negative_seq_event_is_refused_at_construction() -> None:
    with pytest.raises(ValidationError):
        _event(-1)


@pytest.mark.property
@given(n=st.integers(min_value=0, max_value=60))
def test_correctly_sequenced_appends_are_always_gapless(n: int) -> None:
    trail = OrgAuditTrail()
    for i in range(n):
        trail = trail.append(_event(i, detail=f"e{i}"))
    # Invariant: seqs are exactly 0..n-1, gapless and strictly increasing.
    assert tuple(e.seq for e in trail.events) == tuple(range(n))
    assert trail.next_seq == n


@pytest.mark.property
@given(
    good=st.integers(min_value=0, max_value=20),
    wrong=st.integers(min_value=-5, max_value=40),
)
def test_any_wrong_next_seq_is_refused(good: int, wrong: int) -> None:
    trail = OrgAuditTrail()
    for i in range(good):
        trail = trail.append(_event(i))
    if wrong == good:
        trail.append(_event(wrong))  # the ONE correct value succeeds
    else:
        with pytest.raises((ValueError, Exception)):
            trail.append(_event(wrong))  # every other value is refused (gapless)
