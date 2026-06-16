"""Adversarial tests for the ClaudeSession value object's guarded transitions.

The session model routes every state change through the legal-transition table:
an illegal move raises :class:`SessionTransitionError` rather than corrupting the
lifecycle, transitions never mutate in place (frozen + copy), and ``needs_handoff``
fires only for a RUNNING+exhausted session. These tests pin every refusal and the
no-spawn-without-spec construction guard. Synthetic only.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from autofirm.org.org_identifiers import RoleId
from autofirm.substrate.claude_session_model import ClaudeSession, SessionTransitionError
from autofirm.substrate.session_status import SessionStatus
from tests.substrate.synthetic_substrate_fixtures import (
    make_budget,
    make_credential_reference,
)


def _pending_session(*, budget=None) -> ClaudeSession:
    return ClaudeSession(
        session_id="session-0",  # type: ignore[arg-type]
        owning_role_id=RoleId("role-1"),
        credential_reference=make_credential_reference(),
        working_dir="/wt/a",
        status=SessionStatus.PENDING,
        budget=budget or make_budget(),
    )


@pytest.mark.unit
def test_empty_working_dir_is_refused_at_construction() -> None:
    with pytest.raises(ValidationError):  # fail-closed: no orphan-dir session
        ClaudeSession(
            session_id="session-0",  # type: ignore[arg-type]
            owning_role_id=RoleId("role-1"),
            credential_reference=make_credential_reference(),
            working_dir="   ",
            status=SessionStatus.PENDING,
            budget=make_budget(),
        )


@pytest.mark.unit
def test_happy_path_transitions_return_new_frozen_sessions() -> None:
    pending = _pending_session()
    running = pending.mark_running()
    assert running.status is SessionStatus.RUNNING
    assert pending.status is SessionStatus.PENDING  # original unchanged (immutable)
    completed = running.mark_completed()
    assert completed.status is SessionStatus.COMPLETED
    assert completed.is_terminal() is True


@pytest.mark.unit
def test_illegal_transition_raises_not_corrupts() -> None:
    pending = _pending_session()
    # PENDING -> COMPLETED is not a legal edge: must refuse, not silently allow.
    with pytest.raises(SessionTransitionError, match="illegal transition"):
        pending.mark_completed()
    # PENDING -> HANDED_OFF is also illegal.
    with pytest.raises(SessionTransitionError):
        pending.mark_handed_off()


@pytest.mark.unit
def test_completed_session_refuses_all_further_transitions() -> None:
    completed = _pending_session().mark_running().mark_completed()
    for transition in (
        completed.mark_running,
        completed.mark_completed,
        completed.mark_failed,
        completed.mark_handed_off,
    ):
        with pytest.raises(SessionTransitionError):  # terminal: no successor
            transition()


@pytest.mark.unit
def test_needs_handoff_only_when_running_and_exhausted() -> None:
    exhausted = make_budget(limit=100, consumed=80, threshold=0.8)
    # A PENDING session never needs handoff even with an exhausted budget.
    pending = _pending_session(budget=exhausted)
    assert pending.needs_handoff() is False
    # Once RUNNING and exhausted, it needs a handoff.
    running = pending.mark_running()
    assert running.needs_handoff() is True
    # With budget remaining, no handoff.
    fresh = _pending_session(budget=make_budget(limit=100, consumed=10)).mark_running()
    assert fresh.needs_handoff() is False


@pytest.mark.unit
def test_with_consumed_advances_budget_without_changing_status() -> None:
    running = _pending_session(budget=make_budget(limit=100, consumed=0)).mark_running()
    advanced = running.with_consumed(81)  # over the 80-token threshold
    assert advanced.status is SessionStatus.RUNNING
    assert advanced.needs_handoff() is True
    assert running.needs_handoff() is False  # original untouched
