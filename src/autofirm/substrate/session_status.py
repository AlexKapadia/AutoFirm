"""The session lifecycle status enum + its single source of legal transitions.

What this does
--------------
Defines :class:`SessionStatus` — the closed set of states a ``claude`` CLI
session can be in — and :func:`is_legal_transition`, the one authority on which
state changes are allowed. The status machine is intentionally small and
acyclic-with-one-exit so the lifecycle is auditable and every transition the
engine performs is checkable against a single table.

States
------
* ``PENDING`` — modelled/spawned but not yet confirmed running.
* ``RUNNING`` — actively executing (single-writer: at most one RUNNING session
  per owned single-writer artifact; enforced by the lifecycle engine).
* ``HANDED_OFF`` — voluntarily retired because its context budget was exhausted;
  a fresh successor session was spawned with its handoff summary (terminal here).
* ``COMPLETED`` — its work finished; no resume is ever needed (terminal).
* ``FAILED`` — terminated abnormally; eligible for fail-closed resume.

Why it exists / where it sits
-----------------------------
A5 SYNTHESIS §1: sessions are persisted and resumable; A3 SYNTHESIS L1.A3.3:
recovery is modelled as a saga of locally-atomic, checkpointed phases. Keeping
the legal-transition table in one pure function lets the property tests assert
the invariant "no illegal transition is ever reachable" across arbitrary
operation sequences (CLAUDE.md §3.6).

Security / compliance invariants upheld
---------------------------------------
* **Fail-closed (§5.6):** any transition not explicitly in the legal table is
  refused. Terminal states (``COMPLETED``) have no successors; ``HANDED_OFF`` is
  terminal for the *outgoing* session (its successor is a new session).
* **Determinism (§3.11):** transition legality is a pure lookup, no I/O.
"""

from __future__ import annotations

from enum import StrEnum

__all__ = ["SessionStatus", "is_legal_transition"]


class SessionStatus(StrEnum):
    """The closed set of session lifecycle states (deny-by-default transitions)."""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    HANDED_OFF = "HANDED_OFF"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


# The single, explicit table of legal forward transitions. Anything not listed
# here is refused (fail-closed). Read as "from -> {allowed next states}":
#   PENDING   -> RUNNING (spawn confirmed) | FAILED (spawn aborted)
#   RUNNING   -> HANDED_OFF (budget exhausted) | COMPLETED (work done) | FAILED
#   HANDED_OFF/COMPLETED/FAILED are terminal for THIS session id (a resume of a
#   FAILED session produces a NEW session id, modelled as a fresh PENDING object,
#   so FAILED itself has no outgoing edge here).
_LEGAL_TRANSITIONS: dict[SessionStatus, frozenset[SessionStatus]] = {
    SessionStatus.PENDING: frozenset({SessionStatus.RUNNING, SessionStatus.FAILED}),
    SessionStatus.RUNNING: frozenset(
        {SessionStatus.HANDED_OFF, SessionStatus.COMPLETED, SessionStatus.FAILED}
    ),
    SessionStatus.HANDED_OFF: frozenset(),  # terminal for the outgoing session
    SessionStatus.COMPLETED: frozenset(),  # terminal: work finished, never resumed
    SessionStatus.FAILED: frozenset(),  # terminal id; resume spawns a NEW session
}


def is_legal_transition(current: SessionStatus, target: SessionStatus) -> bool:
    """Return True iff moving ``current -> target`` is an allowed transition.

    Deny-by-default: a self-transition or any pair absent from the table is
    refused. This is the only definition of transition legality, so the engine
    and the tests agree by construction.
    """
    # fail-closed: unknown 'current' (shouldn't happen for a closed enum) -> deny.
    return target in _LEGAL_TRANSITIONS.get(current, frozenset())
