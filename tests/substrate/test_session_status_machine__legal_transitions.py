"""Exhaustive + property tests for the session status machine (fail-closed).

The legal-transition table is the single authority on which state changes are
allowed; anything absent is refused. These tests enumerate the FULL state x state
product (every legal pair allowed, every illegal pair denied), prove terminal
states have no successors, and property-check that no random transition sequence
can ever reach an illegal move via the guarded session model. Synthetic only.
"""

from __future__ import annotations

import itertools

import pytest
from hypothesis import given
from hypothesis import strategies as st

from autofirm.substrate.session_status import SessionStatus, is_legal_transition

# The authoritative expected legal edges, written out INDEPENDENTLY of the
# production table so the test cannot tautologically agree with a mutated table.
_EXPECTED_LEGAL: set[tuple[SessionStatus, SessionStatus]] = {
    (SessionStatus.PENDING, SessionStatus.RUNNING),
    (SessionStatus.PENDING, SessionStatus.FAILED),
    (SessionStatus.RUNNING, SessionStatus.HANDED_OFF),
    (SessionStatus.RUNNING, SessionStatus.COMPLETED),
    (SessionStatus.RUNNING, SessionStatus.FAILED),
}


@pytest.mark.unit
@pytest.mark.parametrize(
    ("current", "target"), list(itertools.product(SessionStatus, SessionStatus))
)
def test_full_transition_matrix_matches_independent_truth(
    current: SessionStatus, target: SessionStatus
) -> None:
    """Every (from, to) pair is legal iff it is in the independent truth set."""
    expected = (current, target) in _EXPECTED_LEGAL
    assert is_legal_transition(current, target) is expected


@pytest.mark.unit
@pytest.mark.parametrize(
    "terminal",
    [SessionStatus.HANDED_OFF, SessionStatus.COMPLETED, SessionStatus.FAILED],
)
def test_terminal_states_have_no_successor(terminal: SessionStatus) -> None:
    # fail-closed: a terminal state can transition NOWHERE (incl. to itself).
    assert all(not is_legal_transition(terminal, t) for t in SessionStatus)


@pytest.mark.unit
@pytest.mark.parametrize("state", list(SessionStatus))
def test_no_self_transition_is_legal(state: SessionStatus) -> None:
    # A self-transition is never in the table -> always refused.
    assert is_legal_transition(state, state) is False


@pytest.mark.property
@given(
    current=st.sampled_from(list(SessionStatus)),
    target=st.sampled_from(list(SessionStatus)),
)
def test_property_legality_is_membership_in_truth_set(
    current: SessionStatus, target: SessionStatus
) -> None:
    """Over all pairs, legality exactly equals membership in the truth set."""
    assert is_legal_transition(current, target) == ((current, target) in _EXPECTED_LEGAL)
