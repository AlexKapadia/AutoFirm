"""The typed model of one orchestrated ``claude`` CLI session.

What this does
--------------
Defines :class:`ClaudeSession` — the immutable, validated record of a single
running (or retired) Claude Code CLI session that backs one AutoFirm role. It
binds together: the session id, the owning role id, a *secret-free*
:class:`~autofirm.substrate.scoped_credential_reference.ScopedCredentialReference`,
the working directory the session runs in (its single-writer worktree), its
:class:`~autofirm.substrate.session_status.SessionStatus`, and its
:class:`~autofirm.substrate.context_budget_state.ContextBudgetState`.

Transitions are expressed as pure methods that return a *new* session object
(``model_copy``), each guarded by
:func:`~autofirm.substrate.session_status.is_legal_transition`, so an illegal
state change is impossible to perform and the whole history is replayable.

Why it exists / where it sits
-----------------------------
This is the substrate's central value object: the lifecycle engine creates and
transitions it; the launcher contract is invoked to actually start the process
it describes; the handoff summary is derived from it. It deliberately holds NO
secret material — only the secret-free credential reference — so a session can
be logged, audited, or handed off without ever leaking a credential.

Security / compliance invariants upheld (CLAUDE.md §3.2, §5.6)
-------------------------------------------------------------
* **No-spawn-without-spec/credential (§5.6):** a session cannot be constructed
  without a role id, a working dir, and a credential reference — the fields are
  required and validated non-empty.
* **Secret never logged (§5.6):** the only credential data is the secret-free
  reference; there is no field that could carry secret material.
* **Fail-closed transitions (§5.6):** every transition method refuses an illegal
  status change rather than forcing it.
* **Determinism (§3.11):** the model is frozen and transitions are pure; a
  session's history is a function of its operation sequence.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, field_validator

from autofirm.org.org_identifiers import RoleId
from autofirm.substrate.context_budget_state import ContextBudgetState
from autofirm.substrate.scoped_credential_reference import ScopedCredentialReference
from autofirm.substrate.session_identity import SessionId
from autofirm.substrate.session_status import SessionStatus, is_legal_transition

__all__ = ["ClaudeSession", "SessionTransitionError"]


class SessionTransitionError(RuntimeError):
    """Raised when an illegal session status transition is attempted (fail-closed)."""


class ClaudeSession(BaseModel):
    """An immutable record of one orchestrated ``claude`` CLI session.

    State changes never mutate in place: each transition method validates the
    move against the legal-transition table and returns a NEW frozen session, so
    the sequence of sessions is an append-only, replayable history.
    """

    model_config = ConfigDict(frozen=True)

    session_id: SessionId  # opaque CLI session id (from the JSON envelope)
    owning_role_id: RoleId  # the org role this session executes on behalf of
    credential_reference: ScopedCredentialReference  # secret-free; never the secret
    working_dir: str  # single-writer worktree/dir the session runs in
    status: SessionStatus  # current lifecycle state
    budget: ContextBudgetState  # context-window accounting

    @field_validator("working_dir")
    @classmethod
    def _non_empty_working_dir(cls, value: str) -> str:
        # fail-closed: a session with no working dir is ambiguous (which worktree
        # owns it?) -> refuse it, preserving single-writer isolation by dir.
        if not value or not value.strip():
            raise ValueError("working_dir must be non-empty")
        return value

    def _transition_to(self, target: SessionStatus) -> ClaudeSession:
        """Return a copy in ``target`` state, refusing any illegal transition.

        The single internal chokepoint every public transition routes through, so
        the legal-transition table is the one authority and no method can bypass
        it.
        """
        if not is_legal_transition(self.status, target):
            # fail-closed: refuse the illegal move rather than corrupting the
            # lifecycle; the caller must handle a refused transition explicitly.
            raise SessionTransitionError(
                f"illegal transition {self.status.value} -> {target.value}"
            )
        return self.model_copy(update={"status": target})

    def mark_running(self) -> ClaudeSession:
        """Confirm a spawned session is now actively running (PENDING -> RUNNING)."""
        return self._transition_to(SessionStatus.RUNNING)

    def mark_completed(self) -> ClaudeSession:
        """Record that the session's work finished (RUNNING -> COMPLETED, terminal)."""
        return self._transition_to(SessionStatus.COMPLETED)

    def mark_failed(self) -> ClaudeSession:
        """Record an abnormal termination (PENDING/RUNNING -> FAILED, resumable)."""
        return self._transition_to(SessionStatus.FAILED)

    def mark_handed_off(self) -> ClaudeSession:
        """Retire this session after a budget-driven handoff (RUNNING -> HANDED_OFF)."""
        return self._transition_to(SessionStatus.HANDED_OFF)

    def with_consumed(self, tokens: int) -> ClaudeSession:
        """Return a copy whose budget has consumed ``tokens`` more (status unchanged)."""
        return self.model_copy(update={"budget": self.budget.consume(tokens)})

    def needs_handoff(self) -> bool:
        """Return True iff a RUNNING session has exhausted its context budget.

        Only a RUNNING session can need a handoff — a PENDING, terminal, or
        already-handed-off session never does (fail-closed: no spurious handoff of
        a non-running session).
        """
        return self.status is SessionStatus.RUNNING and self.budget.is_exhausted()

    def is_terminal(self) -> bool:
        """Return True iff the session is in a state with no further transitions."""
        return self.status in (
            SessionStatus.HANDED_OFF,
            SessionStatus.COMPLETED,
            SessionStatus.FAILED,
        )
