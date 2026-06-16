"""Adversarial tests: spawning a session is FAIL-CLOSED and process-free.

The engine refuses to spawn without a valid role id + working dir + a non-expired
credential reference, and refuses a second live session on one working dir
(single-writer). Crucially it NEVER spawns a real process — it depends only on the
:class:`SessionLauncher` Protocol, so the fake launcher records what WOULD launch
and no ``claude`` process is ever started. Synthetic only.
"""

from __future__ import annotations

from datetime import timedelta

import pytest

from autofirm.org.org_identifiers import RoleId
from autofirm.substrate.session_lifecycle_engine import (
    SingleWriterViolation,
    SpawnRefused,
)
from autofirm.substrate.session_status import SessionStatus
from tests.substrate.synthetic_substrate_fixtures import (
    FIXED_NOW,
    FrozenNow,
    make_budget,
    make_credential_reference,
    make_engine,
    make_saga_state,
)


def _spawn(engine, **overrides):
    """Spawn with valid defaults, overriding individual kwargs per test."""
    kwargs = {
        "owning_role_id": RoleId("role-1"),
        "system_prompt": "you are a worker",
        "working_dir": "/wt/a",
        "credential_reference": make_credential_reference(),
        "budget": make_budget(),
    }
    kwargs.update(overrides)
    return engine.spawn(**kwargs)


@pytest.mark.unit
def test_happy_spawn_registers_a_running_session_and_records_one_launch() -> None:
    engine, launcher = make_engine()
    session = _spawn(engine)
    assert session.status is SessionStatus.RUNNING
    assert session.session_id == "session-0"  # deterministic id from the fake
    # Exactly one launch was modelled; NO real process started (it is a fake).
    assert len(launcher.launched_specs()) == 1
    assert launcher.launched_specs()[0].resume_from is None  # fresh spawn


@pytest.mark.unit
@pytest.mark.security
@pytest.mark.parametrize(
    "overrides",
    [
        {"owning_role_id": RoleId("   ")},  # blank role refused
        {"working_dir": "   "},  # blank dir refused
    ],
)
def test_spawn_refuses_underspecified_request(overrides: dict) -> None:
    engine, launcher = make_engine()
    with pytest.raises(SpawnRefused):  # fail-closed: no-spawn-without-spec
        _spawn(engine, **overrides)
    assert launcher.launched_specs() == ()  # nothing was ever launched


@pytest.mark.unit
@pytest.mark.security
def test_spawn_refuses_expired_credential() -> None:
    # Clock is AFTER the credential's expiry -> spawn must fail closed.
    engine, launcher = make_engine(clock=FrozenNow(start=FIXED_NOW + timedelta(hours=2)))
    with pytest.raises(SpawnRefused, match="expired"):
        _spawn(engine, credential_reference=make_credential_reference())
    assert launcher.launched_specs() == ()  # no launch against a dead credential


@pytest.mark.unit
@pytest.mark.security
def test_spawn_refuses_second_live_session_on_same_working_dir() -> None:
    engine, _ = make_engine()
    _spawn(engine, working_dir="/wt/a")
    # A second spawn on the same dir would create two concurrent writers -> refuse.
    with pytest.raises(SingleWriterViolation):
        _spawn(engine, working_dir="/wt/a")


@pytest.mark.unit
def test_spawn_allows_distinct_working_dirs() -> None:
    engine, _ = make_engine()
    a = _spawn(engine, working_dir="/wt/a")
    b = _spawn(engine, working_dir="/wt/b")
    assert a.session_id != b.session_id
    assert {s.working_dir for s in engine.sessions()} == {"/wt/a", "/wt/b"}


@pytest.mark.unit
def test_handoff_keeps_exactly_one_live_session_on_the_dir() -> None:
    # Spawn, exhaust the budget, hand off: the predecessor releases the dir
    # (-> HANDED_OFF) and the successor takes it, so there is always exactly one
    # live session on the dir (single-writer preserved across the handoff).
    engine, _ = make_engine()
    first = _spawn(engine, working_dir="/wt/a", budget=make_budget(limit=100, consumed=0))
    engine.record_consumption(first.session_id, 80)  # reach the handoff threshold
    successor = engine.hand_off(first.session_id, make_saga_state())
    live = [s for s in engine.sessions() if s.status is SessionStatus.RUNNING]
    assert len(live) == 1
    assert live[0].session_id == successor.session_id
    assert successor.working_dir == "/wt/a"
