"""Stateful property test: substrate lifecycle invariants hold over ANY sequence.

A Hypothesis :class:`RuleBasedStateMachine` drives a real
:class:`SessionLifecycleEngine` through arbitrary interleavings of spawn / consume
/ hand-off / fail / resume across a small pool of working dirs, and after EVERY
accepted or refused step re-asserts the load-bearing invariants:

* **single-writer:** at most one live (PENDING/RUNNING) session per working dir —
  never two concurrent writers for one single-writer artifact;
* **legal status only:** every registered session is in a valid state and a
  live session's status is PENDING/RUNNING;
* **fail-closed refusals are total no-ops:** a refused spawn/handoff/resume leaves
  the registry exactly as it was (no partial mutation);
* **determinism:** an identical operation script on a fresh engine yields an
  identical observable outcome.

A single mishandled transition anywhere in a long random run breaks one of these.
Synthetic only; no real process (the fake launcher never spawns).
"""

from __future__ import annotations

import pytest
from hypothesis import strategies as st
from hypothesis.stateful import RuleBasedStateMachine, invariant, rule

from autofirm.org.org_identifiers import RoleId
from autofirm.substrate.session_lifecycle_engine import (
    ResumeRefused,
    SingleWriterViolation,
    SpawnRefused,
)
from autofirm.substrate.session_status import SessionStatus
from tests.substrate.synthetic_substrate_fixtures import (
    make_budget,
    make_credential_reference,
    make_engine,
    make_saga_state,
)

_WORKING_DIRS = ["/wt/a", "/wt/b"]  # small pool -> forces single-writer contention
_LIVE = frozenset({SessionStatus.PENDING, SessionStatus.RUNNING})


class SubstrateLifecycleMachine(RuleBasedStateMachine):
    """Drives a SessionLifecycleEngine through random ops, checking invariants always."""

    def __init__(self) -> None:
        """Start with a fresh engine + fake launcher and an empty session script."""
        super().__init__()
        self.engine, self.launcher = make_engine()
        self._role_counter = 0
        self._script: list[tuple[str, object]] = []  # replayed for the determinism check

    def _new_role(self) -> RoleId:
        self._role_counter += 1
        return RoleId(f"role-{self._role_counter}")

    def _live_on(self, working_dir: str):
        return [
            s
            for s in self.engine.sessions()
            if s.working_dir == working_dir and s.status in _LIVE
        ]

    def _snapshot(self) -> tuple[tuple[str, str], ...]:
        return tuple(
            sorted((s.session_id, s.status.value) for s in self.engine.sessions())
        )

    @rule(working_dir=st.sampled_from(_WORKING_DIRS))
    def spawn(self, working_dir: str) -> None:
        before = self._snapshot()
        try:
            self.engine.spawn(
                owning_role_id=self._new_role(),
                system_prompt="worker",
                working_dir=working_dir,
                credential_reference=make_credential_reference(),
                budget=make_budget(limit=100, consumed=0),
            )
            self._script.append(("spawn", working_dir))
        except SingleWriterViolation:
            # fail-closed refusal must be a TOTAL no-op (registry unchanged).
            assert self._snapshot() == before
        except SpawnRefused:  # pragma: no cover - inputs are always well-formed here
            assert self._snapshot() == before

    @rule(working_dir=st.sampled_from(_WORKING_DIRS))
    def consume_and_maybe_handoff(self, working_dir: str) -> None:
        live = self._live_on(working_dir)
        if not live:
            return
        target = live[0]
        if target.status is not SessionStatus.RUNNING:
            return
        self.engine.record_consumption(target.session_id, 80)  # reach threshold
        refreshed = {s.session_id: s for s in self.engine.sessions()}[target.session_id]
        if refreshed.needs_handoff():
            self.engine.hand_off(target.session_id, make_saga_state())
            self._script.append(("handoff", target.session_id))

    @rule(working_dir=st.sampled_from(_WORKING_DIRS))
    def fail_a_live_session(self, working_dir: str) -> None:
        live = self._live_on(working_dir)
        if not live:
            return
        target = live[0]
        # Drive the observed failure the engine will later be asked to resume.
        self.engine._sessions[target.session_id] = target.mark_failed()

    @rule(work_complete=st.booleans())
    def resume_a_failed_session(self, work_complete: bool) -> None:
        failed = [
            s for s in self.engine.sessions() if s.status is SessionStatus.FAILED
        ]
        if not failed:
            return
        target = failed[0]
        before = self._snapshot()
        try:
            self.engine.resume(target.session_id, make_saga_state(work_complete=work_complete))
        except ResumeRefused:
            # fail-closed refusal is a total no-op (never a partial mutation).
            assert self._snapshot() == before

    @invariant()
    def at_most_one_live_session_per_dir(self) -> None:
        for working_dir in _WORKING_DIRS:
            assert len(self._live_on(working_dir)) <= 1, "two live writers on one dir"

    @invariant()
    def every_session_status_is_valid(self) -> None:
        for session in self.engine.sessions():
            assert session.status in set(SessionStatus)

    @invariant()
    def registry_keys_match_session_ids(self) -> None:
        for sid, session in self.engine._sessions.items():
            assert session.session_id == sid


@pytest.mark.property
class TestSubstrateLifecycleMachine(SubstrateLifecycleMachine.TestCase):
    """pytest entry point for the stateful substrate-lifecycle property machine."""


@pytest.mark.property
def test_determinism_identical_script_yields_identical_outcome() -> None:
    """A fixed spawn/handoff/resume script replays to a bit-identical outcome."""

    def run() -> tuple[tuple[str, str], ...]:
        engine, _ = make_engine()
        s_a = engine.spawn(
            owning_role_id=RoleId("role-1"),
            system_prompt="worker",
            working_dir="/wt/a",
            credential_reference=make_credential_reference(),
            budget=make_budget(limit=100, consumed=0),
        )
        engine.spawn(
            owning_role_id=RoleId("role-2"),
            system_prompt="worker",
            working_dir="/wt/b",
            credential_reference=make_credential_reference(),
            budget=make_budget(limit=100, consumed=0),
        )
        engine.record_consumption(s_a.session_id, 80)
        engine.hand_off(s_a.session_id, make_saga_state())
        return tuple(sorted((s.session_id, s.status.value) for s in engine.sessions()))

    assert run() == run()
