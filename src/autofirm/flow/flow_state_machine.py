"""The deterministic work-item state machine: the only legal transitions.

What this does
--------------
Defines :class:`WorkState` — the exhaustive lifecycle a unit of work moves
through as it flows across the org — and the **single source of truth for which
transitions are legal** (:data:`ALLOWED_TRANSITIONS`). The machine is a pure,
deterministic transition table: ``is_allowed_transition(a, b)`` is a total
function of its two inputs with no hidden state, so the same edge is always
judged the same way (CLAUDE.md §3.11 determinism) and no state can be skipped.

Why it exists / where it sits
-----------------------------
This is the lowest layer of ``autofirm.flow``: :class:`~autofirm.flow.work_item.WorkItem`
and the trail depend on it and nothing depends back. Keeping the legal-edge maths
in one table (rather than scattered ``if`` checks) is what lets the property tests
drive *arbitrary* transition sequences and assert "no illegal transition is ever
accepted" against a single authority.

Security / compliance invariants upheld
---------------------------------------
* **Closed transition set (fail-closed, CLAUDE.md §5.6):** an edge not in
  :data:`ALLOWED_TRANSITIONS` is illegal by default — the machine denies by
  default, it does not allow-by-omission.
* **No skipped states:** the table only wires *adjacent* lifecycle steps, so a
  work item cannot jump (e.g. CREATED -> DONE) without passing through the
  intervening states.
* **Terminal states are sinks:** DONE has no outgoing edges; a finished item can
  never be silently reopened. BLOCKED can only resume to IN_PROGRESS (it is
  recoverable, not a dead end).
"""

from __future__ import annotations

from enum import StrEnum

__all__ = [
    "ALLOWED_TRANSITIONS",
    "TERMINAL_STATES",
    "WorkState",
    "is_allowed_transition",
    "is_terminal",
]


class WorkState(StrEnum):
    """The exhaustive deterministic lifecycle of a unit of work in the org.

    Ordered by flow: a work item is CREATED, ASSIGNED to a role, taken
    IN_PROGRESS, optionally HANDED_OFF to another role (which returns it to the
    assigned state under the new owner), and ends either DONE or BLOCKED. BLOCKED
    is recoverable (it can resume to IN_PROGRESS); DONE is terminal.
    """

    CREATED = "CREATED"  # exists, not yet owned by any role
    ASSIGNED = "ASSIGNED"  # owned by a role, not yet started
    IN_PROGRESS = "IN_PROGRESS"  # the owning role is actively working it
    HANDED_OFF = "HANDED_OFF"  # ownership transferred mid-flight to a new role
    DONE = "DONE"  # completed (terminal sink — never reopened)
    BLOCKED = "BLOCKED"  # stalled on a dependency (recoverable -> IN_PROGRESS)


# The closed set of legal directed edges. Anything NOT listed here is illegal by
# default (fail-closed): the machine denies by omission rather than allowing it.
# Edges only ever connect adjacent lifecycle steps, so no state can be skipped.
ALLOWED_TRANSITIONS: frozenset[tuple[WorkState, WorkState]] = frozenset(
    {
        (WorkState.CREATED, WorkState.ASSIGNED),  # a new item is given an owner
        (WorkState.ASSIGNED, WorkState.IN_PROGRESS),  # the owner starts work
        (WorkState.ASSIGNED, WorkState.BLOCKED),  # blocked before it could start
        (WorkState.IN_PROGRESS, WorkState.HANDED_OFF),  # ownership transferred
        (WorkState.IN_PROGRESS, WorkState.DONE),  # work completed
        (WorkState.IN_PROGRESS, WorkState.BLOCKED),  # stalled mid-flight
        # A handoff lands the item back under its NEW owner, re-assigned:
        (WorkState.HANDED_OFF, WorkState.ASSIGNED),
        (WorkState.BLOCKED, WorkState.IN_PROGRESS),  # dependency cleared -> resume
    }
)

# States with no outgoing edge in the table: a work item that reaches one of
# these can make no further transition. DONE is the single terminal sink.
TERMINAL_STATES: frozenset[WorkState] = frozenset(
    {state for state in WorkState if not any(src == state for src, _ in ALLOWED_TRANSITIONS)}
)


def is_allowed_transition(source: WorkState, target: WorkState) -> bool:
    """Return True iff ``source -> target`` is a legal edge in the machine.

    This is a total, deterministic function of its two inputs — the single
    authority every caller (the work item, the property tests) consults. An edge
    absent from :data:`ALLOWED_TRANSITIONS` returns False (fail-closed).

    Args:
        source: The current state.
        target: The proposed next state.

    Returns:
        True if the transition is permitted, False otherwise.
    """
    return (source, target) in ALLOWED_TRANSITIONS


def is_terminal(state: WorkState) -> bool:
    """Return True iff ``state`` has no outgoing transition (a flow sink)."""
    return state in TERMINAL_STATES
