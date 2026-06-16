"""Adversarial tests: auto-RESUME is idempotent and fail-closed.

Resume relaunches a FAILED session ONLY if both gates pass: (a) no live session
already owns the working dir, AND (b) the work is not complete. Any ambiguity is
REFUSED — so resume is idempotent (calling it when a session is live or the work
is done changes nothing) and can never double-run work or create a second writer.
These tests pin every refusal branch and the one success path. Synthetic only.
"""

from __future__ import annotations

import pytest

from autofirm.org.org_identifiers import RoleId
from autofirm.substrate.session_lifecycle_engine import ResumeRefused
from autofirm.substrate.session_status import SessionStatus
from tests.substrate.synthetic_substrate_fixtures import (
    make_budget,
    make_credential_reference,
    make_engine,
    make_saga_state,
)


def _spawn_then_fail(engine, *, working_dir="/wt/a"):
    """Spawn a RUNNING session then drive it to FAILED, returning the failed session."""
    session = engine.spawn(
        owning_role_id=RoleId("role-1"),
        system_prompt="worker",
        working_dir=working_dir,
        credential_reference=make_credential_reference(),
        budget=make_budget(),
    )
    failed = session.mark_failed()
    engine._sessions[session.session_id] = failed
    return failed


@pytest.mark.unit
def test_resume_relaunches_a_failed_session_on_a_free_dir() -> None:
    engine, launcher = make_engine()
    failed = _spawn_then_fail(engine)
    successor = engine.resume(failed.session_id, make_saga_state(work_complete=False))
    assert successor.status is SessionStatus.RUNNING
    assert successor.working_dir == failed.working_dir
    # The relaunch carried --resume from the failed session (continues transcript).
    assert launcher.launched_specs()[-1].resume_from == failed.session_id


@pytest.mark.unit
@pytest.mark.security
def test_resume_refused_when_work_already_complete() -> None:
    engine, launcher = make_engine()
    failed = _spawn_then_fail(engine)
    before = len(launcher.launched_specs())
    # fail-closed gate (b): completed work must never be re-run.
    with pytest.raises(ResumeRefused, match="complete"):
        engine.resume(failed.session_id, make_saga_state(work_complete=True))
    assert len(launcher.launched_specs()) == before  # no relaunch -> idempotent no-op


@pytest.mark.unit
@pytest.mark.security
def test_resume_refused_when_a_live_session_owns_the_dir() -> None:
    engine, _ = make_engine()
    failed = _spawn_then_fail(engine, working_dir="/wt/a")
    # A different live session now owns the dir; resuming would create 2 writers.
    engine.spawn(
        owning_role_id=RoleId("role-2"),
        system_prompt="other",
        working_dir="/wt/a",
        credential_reference=make_credential_reference(),
        budget=make_budget(),
    )
    with pytest.raises(ResumeRefused, match="already owns"):  # fail-closed single-writer
        engine.resume(failed.session_id, make_saga_state())


@pytest.mark.unit
@pytest.mark.security
@pytest.mark.parametrize(
    "drive_to",
    [SessionStatus.COMPLETED, SessionStatus.HANDED_OFF],
)
def test_resume_refused_for_non_failed_terminal_states(drive_to: SessionStatus) -> None:
    engine, _ = make_engine()
    session = engine.spawn(
        owning_role_id=RoleId("role-1"),
        system_prompt="worker",
        working_dir="/wt/a",
        credential_reference=make_credential_reference(),
        budget=make_budget(limit=100, consumed=80),  # exhausted so HANDED_OFF is legal
    )
    if drive_to is SessionStatus.COMPLETED:
        terminal = session.mark_completed()
    else:
        terminal = session.mark_handed_off()
    engine._sessions[session.session_id] = terminal
    # Only a FAILED session is resumable; any other state is refused.
    with pytest.raises(ResumeRefused, match="only a FAILED"):
        engine.resume(session.session_id, make_saga_state())


@pytest.mark.unit
@pytest.mark.security
def test_resume_of_unknown_session_is_refused() -> None:
    engine, _ = make_engine()
    with pytest.raises(ResumeRefused, match="unknown session"):  # fail-closed
        engine.resume("session-does-not-exist", make_saga_state())  # type: ignore[arg-type]


@pytest.mark.unit
def test_resume_is_idempotent_under_repeated_refusal() -> None:
    # Calling resume repeatedly when the work is complete is a stable no-op-by-refusal.
    engine, launcher = make_engine()
    failed = _spawn_then_fail(engine)
    for _ in range(5):
        with pytest.raises(ResumeRefused):
            engine.resume(failed.session_id, make_saga_state(work_complete=True))
    # State never changed: still exactly the original spawn launch, session still FAILED.
    assert len(launcher.launched_specs()) == 1
    assert engine.sessions()[0].status is SessionStatus.FAILED
