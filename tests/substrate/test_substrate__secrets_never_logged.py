"""The headline security property: a secret NEVER appears anywhere in the substrate.

A session, handoff summary, launch spec, and every transition hold only the
SECRET-FREE credential reference — the raw secret lives in the access layer and is
revealed only at the production launcher's point of use. These tests plant a
high-entropy sentinel secret in a real credential and prove it appears in NO
projection a log/audit/exception could capture: str / repr / model_dump /
model_dump_json of the reference, session, handoff summary, launch spec, AND the
re-grounding system prompt. Proven over arbitrary secrets via Hypothesis.
Synthetic only.
"""

from __future__ import annotations

import pytest
from hypothesis import given
from hypothesis import strategies as st

from autofirm.org.org_identifiers import RoleId
from autofirm.substrate.claude_session_model import ClaudeSession
from autofirm.substrate.context_handoff_summary import ContextHandoffSummary
from autofirm.substrate.scoped_credential_reference import ScopedCredentialReference
from autofirm.substrate.session_launcher_protocol import LaunchSpec
from autofirm.substrate.session_status import SessionStatus
from tests.substrate.synthetic_substrate_fixtures import (
    SECRET_SENTINEL,
    LeakScanningLauncher,
    make_budget,
    make_engine,
    make_saga_state,
    make_scoped_credential_with_sentinel,
)

# High-entropy secret tails: every example is a distinct sentinel-prefixed value.
_secret_tail = st.text(
    alphabet=st.characters(min_codepoint=33, max_codepoint=126),
    min_size=8,
    max_size=48,
)


def _all_projections(obj: object) -> str:
    """Flatten every string projection of a pydantic model into one searchable blob."""
    parts = [str(obj), repr(obj)]
    if hasattr(obj, "model_dump"):
        parts.append(str(obj.model_dump()))  # type: ignore[attr-defined]
        parts.append(obj.model_dump_json())  # type: ignore[attr-defined]
    return " ".join(parts)


@pytest.mark.property
@pytest.mark.security
@given(tail=_secret_tail)
def test_property_secret_never_in_reference_projections(tail: str) -> None:
    """Building a reference from a real credential never carries the secret."""
    cred = make_scoped_credential_with_sentinel(tail)
    ref = ScopedCredentialReference.from_scoped_credential(cred)
    secret = SECRET_SENTINEL + tail
    assert secret not in _all_projections(ref)
    # The secret IS still reachable from the credential's reveal() (point of use).
    assert cred.secret.reveal() == secret


@pytest.mark.property
@pytest.mark.security
@given(tail=_secret_tail)
def test_property_secret_never_in_session_or_handoff_or_spec(tail: str) -> None:
    """Secret appears in NO session/handoff/spec/system-prompt projection."""
    cred = make_scoped_credential_with_sentinel(tail)
    ref = ScopedCredentialReference.from_scoped_credential(cred)
    secret = SECRET_SENTINEL + tail

    session = ClaudeSession(
        session_id="session-0",  # type: ignore[arg-type]
        owning_role_id=RoleId("role-1"),
        credential_reference=ref,
        working_dir="/wt/a",
        status=SessionStatus.RUNNING,
        budget=make_budget(),
    )
    summary = ContextHandoffSummary.from_session(session, make_saga_state())
    spec = LaunchSpec(
        owning_role_id=RoleId("role-1"),
        system_prompt=summary.render_system_prompt(),
        working_dir="/wt/a",
        credential_reference=ref,
    )
    # The secret must appear in NONE of these projections (incl. the re-ground prompt).
    for projected in (
        _all_projections(session),
        _all_projections(summary),
        _all_projections(spec),
        summary.render_system_prompt(),
    ):
        assert secret not in projected


@pytest.mark.security
def test_exception_message_from_failed_transition_carries_no_secret() -> None:
    cred = make_scoped_credential_with_sentinel("inexceptiontail")
    ref = ScopedCredentialReference.from_scoped_credential(cred)
    session = ClaudeSession(
        session_id="session-0",  # type: ignore[arg-type]
        owning_role_id=RoleId("role-1"),
        credential_reference=ref,
        working_dir="/wt/a",
        status=SessionStatus.PENDING,
        budget=make_budget(),
    )
    # An illegal transition raises; the message must never embed credential material.
    from autofirm.substrate.claude_session_model import SessionTransitionError

    with pytest.raises(SessionTransitionError) as exc_info:
        session.mark_completed()  # PENDING -> COMPLETED is illegal
    assert SECRET_SENTINEL not in str(exc_info.value)


@pytest.mark.security
def test_engine_launch_path_never_receives_the_secret() -> None:
    # Wire the engine with a launcher that ASSERTS no secret reaches a launch spec.
    cred = make_scoped_credential_with_sentinel("enginepathtail")
    ref = ScopedCredentialReference.from_scoped_credential(cred)
    engine, _ = make_engine()
    # Swap in the leak-scanning launcher for this assertion.
    engine._launcher = LeakScanningLauncher(SECRET_SENTINEL + "enginepathtail")
    session = engine.spawn(
        owning_role_id=RoleId("role-1"),
        system_prompt="worker",
        working_dir="/wt/a",
        credential_reference=ref,
        budget=make_budget(limit=100, consumed=0),
    )
    engine.record_consumption(session.session_id, 80)
    # Drive a handoff too, so the successor-launch spec is also leak-scanned.
    engine.hand_off(session.session_id, make_saga_state())
