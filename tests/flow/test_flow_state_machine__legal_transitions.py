"""State-machine tests: ONLY legal edges accepted, no skipped states, sinks hold.

Proves the deterministic transition table is the single authority for legality:
every CREATED->...->DONE path passes through intervening states (no skips), every
edge absent from the table is rejected, DONE is a terminal sink, and BLOCKED is
recoverable. Includes a Hypothesis property over arbitrary (source, target) pairs
asserting ``is_allowed_transition`` agrees with table membership exactly, and that
no skipping edge (e.g. CREATED->DONE) is ever legal. Synthetic only; no network.
"""

from __future__ import annotations

import pytest
from hypothesis import given
from hypothesis import strategies as st

from autofirm.flow.flow_state_machine import (
    ALLOWED_TRANSITIONS,
    TERMINAL_STATES,
    WorkState,
    is_allowed_transition,
    is_terminal,
)

_ALL_STATES = list(WorkState)
_states = st.sampled_from(_ALL_STATES)

# Edges that must NEVER be legal: state skips and reopening a finished item.
_SKIPPING_EDGES = [
    (WorkState.CREATED, WorkState.IN_PROGRESS),  # skipped ASSIGNED
    (WorkState.CREATED, WorkState.DONE),  # skipped the whole lifecycle
    (WorkState.CREATED, WorkState.HANDED_OFF),  # skipped ASSIGNED + IN_PROGRESS
    (WorkState.ASSIGNED, WorkState.DONE),  # skipped IN_PROGRESS
    (WorkState.ASSIGNED, WorkState.HANDED_OFF),  # cannot hand off un-started work
    (WorkState.DONE, WorkState.IN_PROGRESS),  # reopening a terminal item
    (WorkState.DONE, WorkState.ASSIGNED),  # reopening a terminal item
    (WorkState.HANDED_OFF, WorkState.IN_PROGRESS),  # must re-assign before resuming
]


@pytest.mark.unit
def test_done_is_the_single_terminal_sink() -> None:
    assert frozenset({WorkState.DONE}) == TERMINAL_STATES
    assert is_terminal(WorkState.DONE)
    # Every non-DONE state has at least one outgoing edge (flow never dead-ends
    # except at DONE).
    for state in WorkState:
        has_out = any(src == state for src, _ in ALLOWED_TRANSITIONS)
        assert has_out is (state is not WorkState.DONE)


@pytest.mark.unit
def test_blocked_is_recoverable_only_to_in_progress() -> None:
    out = {tgt for src, tgt in ALLOWED_TRANSITIONS if src is WorkState.BLOCKED}
    assert out == {WorkState.IN_PROGRESS}


@pytest.mark.unit
@pytest.mark.parametrize(("src", "tgt"), _SKIPPING_EDGES)
def test_skipping_or_reopening_edges_are_illegal(src: WorkState, tgt: WorkState) -> None:
    # No skipped states and no reopening a terminal item.
    assert is_allowed_transition(src, tgt) is False


@pytest.mark.unit
def test_self_loops_are_illegal() -> None:
    # A "transition" to the same state is not a move and is never in the table.
    for state in WorkState:
        assert is_allowed_transition(state, state) is False


@pytest.mark.unit
def test_every_listed_edge_is_accepted() -> None:
    # The table IS the authority: each listed edge is allowed, exactly.
    for src, tgt in ALLOWED_TRANSITIONS:
        assert is_allowed_transition(src, tgt) is True


@pytest.mark.property
@given(source=_states, target=_states)
def test_is_allowed_iff_in_table(source: WorkState, target: WorkState) -> None:
    # Property: legality is membership in the table and nothing else — a pure,
    # deterministic function over every possible (source, target) pair.
    assert is_allowed_transition(source, target) == ((source, target) in ALLOWED_TRANSITIONS)


@pytest.mark.property
@given(source=_states, target=_states)
def test_no_edge_out_of_terminal_state_is_ever_legal(
    source: WorkState, target: WorkState
) -> None:
    # Property: a terminal state has no legal successor, for ANY target.
    if is_terminal(source):
        assert is_allowed_transition(source, target) is False


@pytest.mark.property
@given(data=st.data())
def test_determinism_same_pair_same_answer(data: st.DataObject) -> None:
    # Property/determinism: re-evaluating the same edge always agrees with itself.
    source = data.draw(_states)
    target = data.draw(_states)
    first = is_allowed_transition(source, target)
    for _ in range(5):
        assert is_allowed_transition(source, target) is first
