"""WorkItem tests: legal flow, fail-closed handoffs, determinism, full provenance.

Proves the work-item primitive (1) drives only legal state-machine edges, (2)
fail-closes a handoff/assignment to an unknown role, (3) records complete,
gapless provenance with injected-clock timestamps, and (4) is immutable (a
rejected move leaves the prior item untouched). The marquee property test drives
*arbitrary* sequences of transition verbs and asserts the invariants hold over
every reachable path: no illegal transition is ever accepted, the trail stays
gapless and complete, and from/to roles are always traceable. Synthetic only; no
network, no wall-clock.
"""

from __future__ import annotations

import pytest
from hypothesis import given
from hypothesis import strategies as st

from autofirm.flow.flow_state_machine import WorkState, is_allowed_transition, is_terminal
from autofirm.flow.injected_flow_clock import ManualFlowClock
from autofirm.flow.work_item import IllegalTransitionError, UnknownRoleError, WorkItem

_ROLES = frozenset({"coo", "cto", "cdo"})


def _new_item(clock: ManualFlowClock | None = None) -> WorkItem:
    return WorkItem.create(
        work_id="WI-1",
        clock=clock if clock is not None else ManualFlowClock(),
        known_roles=_ROLES,
    )


# --------------------------------------------------------------------------- #
# Happy-path flow                                                             #
# --------------------------------------------------------------------------- #


@pytest.mark.unit
def test_full_lifecycle_to_done_records_complete_trail() -> None:
    clock = ManualFlowClock()
    item = _new_item(clock)
    assert item.state is WorkState.CREATED and item.owner is None

    item = item.assign_to("coo", "kickoff")
    clock.tick()
    item = item.start("begin")
    clock.tick()
    item = item.complete("finished")

    assert item.state is WorkState.DONE
    assert is_terminal(item.state)
    trail = item.trail
    assert trail.is_gapless()
    # First transition has no prior owner; it is recorded as None (created item).
    assert trail.transitions[0].from_role is None
    assert trail.transitions[0].to_role == "coo"
    # Every transition's reason is the one we supplied (explain-every-decision).
    assert [t.reason for t in trail.transitions] == ["kickoff", "begin", "finished"]


@pytest.mark.unit
def test_handoff_transfers_ownership_and_records_both_roles() -> None:
    item = _new_item().assign_to("coo", "k").start("s").hand_off("cto", "delegate")
    assert item.state is WorkState.HANDED_OFF
    assert item.owner == "cto"
    last = item.trail.transitions[-1]
    assert last.from_role == "coo" and last.to_role == "cto"
    # The new owner can receive and continue the flow.
    resumed = item.receive("accepted").start("continue")
    assert resumed.state is WorkState.IN_PROGRESS and resumed.owner == "cto"


@pytest.mark.unit
def test_block_then_resume_is_recoverable() -> None:
    item = _new_item().assign_to("coo", "k").start("s").block("waiting on dep")
    assert item.state is WorkState.BLOCKED
    resumed = item.resume("dep cleared")
    assert resumed.state is WorkState.IN_PROGRESS
    assert resumed.trail.transitions[-1].reason == "dep cleared"


# --------------------------------------------------------------------------- #
# Fail-closed cases                                                           #
# --------------------------------------------------------------------------- #


@pytest.mark.security
def test_handoff_to_unknown_role_is_refused() -> None:
    item = _new_item().assign_to("coo", "k").start("s")
    with pytest.raises(UnknownRoleError, match="unknown/unauthorised role"):
        item.hand_off("attacker", "exfiltrate")
    # fail-closed: the rejected move left the item untouched (still IN_PROGRESS).
    assert item.state is WorkState.IN_PROGRESS and item.owner == "coo"


@pytest.mark.security
def test_assign_to_unknown_role_is_refused() -> None:
    item = _new_item()
    with pytest.raises(UnknownRoleError):
        item.assign_to("ghost", "k")
    assert item.state is WorkState.CREATED  # untouched


@pytest.mark.unit
def test_illegal_transition_is_refused() -> None:
    item = _new_item()
    # Cannot start work that was never assigned (CREATED -> IN_PROGRESS is illegal).
    with pytest.raises(IllegalTransitionError):
        item.start("jump")
    # Cannot complete from CREATED either.
    with pytest.raises(IllegalTransitionError):
        item.complete("jump")


@pytest.mark.unit
def test_done_is_terminal_no_further_moves() -> None:
    done = _new_item().assign_to("coo", "k").start("s").complete("f")
    for verb in (
        lambda i: i.start("x"),
        lambda i: i.hand_off("cto", "x"),
        lambda i: i.block("x"),
        lambda i: i.resume("x"),
    ):
        with pytest.raises(IllegalTransitionError):
            verb(done)


@pytest.mark.unit
@pytest.mark.parametrize("bad_id", ["", "   "])
def test_blank_work_id_refused(bad_id: str) -> None:
    with pytest.raises(ValueError, match="work_id must be non-empty"):
        WorkItem.create(work_id=bad_id, clock=ManualFlowClock(), known_roles=_ROLES)


@pytest.mark.unit
def test_empty_known_roles_refused() -> None:
    # fail-closed: with no known roles the item could never legally be assigned.
    with pytest.raises(ValueError, match="known_roles must be non-empty"):
        WorkItem.create(work_id="WI-1", clock=ManualFlowClock(), known_roles=frozenset())


# --------------------------------------------------------------------------- #
# Determinism                                                                 #
# --------------------------------------------------------------------------- #


@pytest.mark.unit
def test_timestamps_come_from_injected_clock_deterministically() -> None:
    clock = ManualFlowClock()
    t0 = clock.now()
    item = _new_item(clock).assign_to("coo", "k")
    # No tick yet -> the recorded timestamp equals the frozen injected instant.
    assert item.trail.transitions[0].timestamp == t0
    clock.tick(60)
    item = item.start("s")
    assert item.trail.transitions[1].timestamp == clock.now()


# --------------------------------------------------------------------------- #
# Marquee property: arbitrary verb sequences preserve every invariant         #
# --------------------------------------------------------------------------- #

# Each verb is (name, callable, requires-a-target-role) applied to a WorkItem.
_VERBS = ["assign", "start", "hand_off", "receive", "block", "resume", "complete"]


def _apply(item: WorkItem, verb: str, role: str) -> WorkItem:
    if verb == "assign":
        return item.assign_to(role, "k")
    if verb == "start":
        return item.start("s")
    if verb == "hand_off":
        return item.hand_off(role, "h")
    if verb == "receive":
        return item.receive("rcv")
    if verb == "block":
        return item.block("b")
    if verb == "resume":
        return item.resume("res")
    return item.complete("done")  # verb == "complete"


@pytest.mark.property
@given(
    ops=st.lists(
        st.tuples(st.sampled_from(_VERBS), st.sampled_from(sorted(_ROLES))),
        min_size=0,
        max_size=25,
    )
)
def test_arbitrary_verb_sequences_never_break_invariants(ops: list[tuple[str, str]]) -> None:
    item = _new_item()
    for verb, role in ops:
        prior_state = item.state
        prior_len = len(item.trail.transitions)
        try:
            item = _apply(item, verb, role)
        except (IllegalTransitionError, UnknownRoleError):
            # A refused move must be a true no-op: nothing changed (immutability).
            assert item.state is prior_state
            assert len(item.trail.transitions) == prior_len
            continue
        # An ACCEPTED move must have been a legal state-machine edge ...
        assert is_allowed_transition(prior_state, item.state)
        # ... appended exactly one transition ...
        assert len(item.trail.transitions) == prior_len + 1
        last = item.trail.transitions[-1]
        assert last.from_state is prior_state and last.to_state is item.state
        # ... routed only to a known role, with complete provenance ...
        assert last.to_role in _ROLES
        assert last.reason != ""
    # Across the WHOLE run the trail is always gapless and complete.
    assert item.trail.is_gapless()
