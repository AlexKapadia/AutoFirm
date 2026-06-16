"""Adversarial + determinism tests for the budget-exhausted context handoff.

A handoff retires the budget-exhausted RUNNING predecessor (-> HANDED_OFF) and
launches a FRESH successor seeded with the re-grounded handoff summary (verbatim
goal + SA/SO/SD) and a zero-consumption budget at the same limit/threshold. These
tests pin: the refusal when a session does not need a handoff, the deterministic
predecessor/successor states, the fresh-window budget, the carried verbatim goal,
and bit-for-bit determinism across two identical runs. Synthetic only.
"""

from __future__ import annotations

import pytest

from autofirm.org.org_identifiers import RoleId
from autofirm.substrate.context_handoff_summary import ContextHandoffSummary
from autofirm.substrate.session_lifecycle_engine import SpawnRefused
from autofirm.substrate.session_status import SessionStatus
from tests.substrate.synthetic_substrate_fixtures import (
    make_budget,
    make_credential_reference,
    make_engine,
    make_saga_state,
)


def _spawn_running(engine, *, working_dir="/wt/a", budget=None):
    return engine.spawn(
        owning_role_id=RoleId("role-1"),
        system_prompt="worker",
        working_dir=working_dir,
        credential_reference=make_credential_reference(),
        budget=budget or make_budget(limit=100, consumed=0),
    )


@pytest.mark.unit
def test_handoff_refused_when_session_does_not_need_it() -> None:
    engine, launcher = make_engine()
    session = _spawn_running(engine, budget=make_budget(limit=100, consumed=10))
    # Budget is NOT exhausted -> a handoff would be spurious -> refuse it.
    with pytest.raises(SpawnRefused, match="exhausted budget"):
        engine.hand_off(session.session_id, make_saga_state())
    assert len(launcher.launched_specs()) == 1  # only the original spawn launched


@pytest.mark.unit
def test_handoff_retires_predecessor_and_spawns_fresh_successor() -> None:
    engine, launcher = make_engine()
    session = _spawn_running(engine)
    engine.record_consumption(session.session_id, 80)  # hit the threshold
    successor = engine.hand_off(session.session_id, make_saga_state(goal="ship it"))

    by_id = {s.session_id: s for s in engine.sessions()}
    # Predecessor is retired (terminal), successor is RUNNING on the same dir.
    assert by_id[session.session_id].status is SessionStatus.HANDED_OFF
    assert successor.status is SessionStatus.RUNNING
    assert successor.working_dir == session.working_dir
    assert successor.owning_role_id == session.owning_role_id
    # Successor got a FRESH window: same limit/threshold, zero consumed.
    assert successor.budget.consumed_tokens == 0
    assert successor.budget.limit_tokens == session.budget.limit_tokens
    assert successor.needs_handoff() is False
    # The successor launch carried --resume from the predecessor (continuity).
    assert launcher.launched_specs()[-1].resume_from == session.session_id


@pytest.mark.unit
def test_handoff_summary_carries_verbatim_goal_into_successor_prompt() -> None:
    engine, launcher = make_engine()
    session = _spawn_running(engine)
    engine.record_consumption(session.session_id, 80)
    goal = "do EXACTLY this, do not reinterpret"
    engine.hand_off(session.session_id, make_saga_state(goal=goal))
    # The successor's system prompt re-grounds on the VERBATIM goal (anti-drift).
    successor_prompt = launcher.launched_specs()[-1].system_prompt
    assert goal in successor_prompt
    assert "GOAL (verbatim" in successor_prompt


@pytest.mark.unit
def test_handoff_summary_from_session_resets_budget_only() -> None:
    engine, _ = make_engine()
    session = _spawn_running(engine, budget=make_budget(limit=200, consumed=160, threshold=0.8))
    summary = ContextHandoffSummary.from_session(session, make_saga_state())
    # Fresh window: same limit/threshold, zeroed consumption — the whole point.
    assert summary.successor_budget.limit_tokens == 200
    assert summary.successor_budget.handoff_threshold == 0.8
    assert summary.successor_budget.consumed_tokens == 0
    assert summary.predecessor_session_id == session.session_id


@pytest.mark.unit
def test_handoff_is_deterministic_across_identical_runs() -> None:
    def run() -> tuple[str, ...]:
        engine, _ = make_engine()
        session = _spawn_running(engine)
        engine.record_consumption(session.session_id, 80)
        successor = engine.hand_off(session.session_id, make_saga_state())
        # Capture the full observable outcome as a comparable tuple.
        return (
            *(
                f"{s.session_id}:{s.status.value}:{s.budget.consumed_tokens}"
                for s in sorted(engine.sessions(), key=lambda x: x.session_id)
            ),
            successor.session_id,
        )

    # Identical inputs (fresh engines, same fake seeds) -> identical outcomes.
    assert run() == run()
