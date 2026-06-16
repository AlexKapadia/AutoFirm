"""Fail-closed construction edges for the substrate value objects.

These pin the validators that refuse under-specified inputs — the security
boundary that stops a vague/empty spec, saga state, or handoff summary from ever
being built. Each empty/blank field must raise at construction (fail-closed),
never silently produce a degenerate object a successor could drift on. Synthetic
only.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from autofirm.org.org_identifiers import RoleId
from autofirm.substrate.context_handoff_summary import ContextHandoffSummary
from autofirm.substrate.regrounded_saga_state import RegroundedSagaState
from autofirm.substrate.session_launcher_protocol import LaunchSpec
from tests.substrate.synthetic_substrate_fixtures import (
    make_budget,
    make_credential_reference,
)


@pytest.mark.unit
@pytest.mark.parametrize("blank_goal", ["", "   ", "\t\n"])
def test_saga_state_refuses_blank_goal(blank_goal: str) -> None:
    # fail-closed: a handoff/resume with no verbatim goal cannot re-ground (A3).
    with pytest.raises(ValidationError, match="goal_verbatim"):
        RegroundedSagaState(
            goal_verbatim=blank_goal,
            application_state="x",
            operation_state="y",
            dependency_state="z",
            work_complete=False,
        )


@pytest.mark.unit
@pytest.mark.parametrize(
    "overrides",
    [
        {"system_prompt": "   "},  # blank prompt -> under-specified launch refused
        {"system_prompt": ""},
        {"working_dir": "  "},  # blank dir -> no single-writer pin refused
        {"owning_role_id": RoleId("   ")},  # blank role -> orphan session refused
    ],
)
def test_launch_spec_refuses_underspecified_fields(overrides: dict[str, object]) -> None:
    kwargs: dict[str, object] = {
        "owning_role_id": RoleId("role-1"),
        "system_prompt": "worker",
        "working_dir": "/wt/a",
        "credential_reference": make_credential_reference(),
    }
    kwargs.update(overrides)
    with pytest.raises(ValidationError):  # fail-closed: no-spawn-from-vague-spec
        LaunchSpec(**kwargs)  # type: ignore[arg-type]


@pytest.mark.unit
@pytest.mark.parametrize(
    ("goal", "working_dir"),
    [("", "/wt/a"), ("   ", "/wt/a"), ("goal", "  ")],
)
def test_handoff_summary_refuses_blank_goal_or_dir(goal: str, working_dir: str) -> None:
    # The summary's OWN validator must also refuse a blank goal/dir (defence in
    # depth: even a hand-built summary, not via from_session, cannot under-specify).
    with pytest.raises(ValidationError):
        ContextHandoffSummary(
            predecessor_session_id="session-0",  # type: ignore[arg-type]
            owning_role_id=RoleId("role-1"),
            credential_reference=make_credential_reference(),
            working_dir=working_dir,
            goal_verbatim=goal,
            application_state="a",
            operation_state="o",
            dependency_state="d",
            work_complete=False,
            successor_budget=make_budget(),
        )
