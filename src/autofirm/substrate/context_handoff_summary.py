"""The typed handoff/resume state carried from a retiring session to its successor.

What this does
--------------
Defines :class:`ContextHandoffSummary` — the immutable, re-grounded state a
session externalizes when its context budget is exhausted (handoff) or when it
failed and must be resumed. A fresh successor session is launched with this
summary injected into its system prompt, so it re-grounds on the *verbatim*
goal and the externalized state rather than re-inferring its purpose from a
drifted transcript (A3 SYNTHESIS L1.A3.3 mandate: re-ground on resume; never let
a resumed session re-infer its goal).

The fields mirror A3's checkpoint data contract (SagaLLM SA/SO/SD, src 10) plus
the resume-state sources from CLAUDE.md §4.8 (git / task-list / roadmap):

* ``goal_verbatim`` — the goal stored ONCE and re-injected unchanged (defends
  against goal misgeneralization / silent drift, A3 src 07).
* ``application_state`` (SA) — git ref / working-dir markers: where the work is.
* ``operation_state`` (SO) — the saga step + decision reasoning so far.
* ``dependency_state`` (SD) — outstanding dependencies / compensation metadata.
* ``work_complete`` — the authority on "is there work left?", consulted by the
  fail-closed resume gate (no resume of completed work).

Why it exists / where it sits
-----------------------------
This is the saga checkpoint payload the lifecycle engine produces at a handoff
and consumes at a resume. It is built FROM a :class:`ClaudeSession` plus the
externalized state, and it carries only the secret-free credential reference, so
a handoff can be logged/audited without leaking a secret.

Security / compliance invariants upheld (CLAUDE.md §3.6, §5.6)
-------------------------------------------------------------
* **Re-ground, don't re-infer (A3):** ``goal_verbatim`` is required and non-empty;
  a handoff with no stored goal is refused (a successor could otherwise drift).
* **Secret never logged (§5.6):** the only credential data is the secret-free
  reference; there is no secret field.
* **Fail-closed completeness signal (§5.6):** ``work_complete`` is an explicit
  boolean the resume gate trusts; ambiguity is resolved by refusing to resume.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, field_validator

from autofirm.org.org_identifiers import RoleId
from autofirm.substrate.claude_session_model import ClaudeSession
from autofirm.substrate.context_budget_state import ContextBudgetState
from autofirm.substrate.regrounded_saga_state import RegroundedSagaState
from autofirm.substrate.scoped_credential_reference import ScopedCredentialReference
from autofirm.substrate.session_identity import SessionId

__all__ = ["ContextHandoffSummary"]


class ContextHandoffSummary(BaseModel):
    """Immutable, re-grounded state handed from one session to its successor.

    Built via :meth:`from_session`; consumed by the lifecycle engine to spawn the
    successor's :class:`~autofirm.substrate.session_launcher_protocol.LaunchSpec`
    with the verbatim goal + externalized state injected, so the new session never
    re-infers its purpose.
    """

    model_config = ConfigDict(frozen=True)

    predecessor_session_id: SessionId  # the session this summary hands off FROM
    owning_role_id: RoleId  # the role continuing across the handoff (unchanged)
    credential_reference: ScopedCredentialReference  # secret-free; carried forward
    working_dir: str  # the single-writer worktree, carried to the successor
    goal_verbatim: str  # stored ONCE, re-injected unchanged (anti-drift, A3 src 07)
    application_state: str  # SA: git ref / working-dir markers (where the work is)
    operation_state: str  # SO: saga step + decision reasoning so far
    dependency_state: str  # SD: outstanding deps + compensation metadata
    work_complete: bool  # the authority the fail-closed resume gate consults
    successor_budget: ContextBudgetState  # the FRESH context window for the successor

    @field_validator("goal_verbatim", "working_dir")
    @classmethod
    def _non_empty(cls, value: str) -> str:
        # fail-closed: a handoff with no verbatim goal (or no working dir) cannot
        # re-ground a successor -> refuse it, defending against goal drift (A3).
        if not value or not value.strip():
            raise ValueError("goal_verbatim and working_dir must be non-empty")
        return value

    @classmethod
    def from_session(
        cls, session: ClaudeSession, state: RegroundedSagaState
    ) -> ContextHandoffSummary:
        """Build a handoff summary from ``session`` + the re-grounded ``state``.

        Copies only the secret-free fields off the session (id, role, credential
        reference, working dir) and pairs them with the caller-supplied
        :class:`RegroundedSagaState`. The successor's budget is a FRESH window: the
        same limit + handoff threshold as the predecessor, reset to zero
        consumption (a new context window is exactly what a handoff buys). The
        secret never enters this object.
        """
        predecessor_budget = session.budget
        successor_budget = ContextBudgetState(
            limit_tokens=predecessor_budget.limit_tokens,
            consumed_tokens=0,  # fresh window: the whole point of the handoff
            handoff_threshold=predecessor_budget.handoff_threshold,
        )
        return cls(
            predecessor_session_id=session.session_id,
            owning_role_id=session.owning_role_id,
            credential_reference=session.credential_reference,  # already secret-free
            working_dir=session.working_dir,
            goal_verbatim=state.goal_verbatim,
            application_state=state.application_state,
            operation_state=state.operation_state,
            dependency_state=state.dependency_state,
            work_complete=state.work_complete,
            successor_budget=successor_budget,
        )

    def render_system_prompt(self) -> str:
        """Render the re-grounding system prompt injected into the successor.

        The successor reads its VERBATIM goal and externalized SA/SO/SD here, so
        it continues the work rather than re-inferring it. Contains no secret (the
        credential reference is secret-free), so this prompt is safe to log.
        """
        # The order puts the verbatim goal first so it anchors the successor's
        # context before any (possibly drifted) operational detail (A3 re-ground).
        return (
            f"GOAL (verbatim, do not reinterpret): {self.goal_verbatim}\n"
            f"APPLICATION STATE (where the work is): {self.application_state}\n"
            f"OPERATION STATE (saga step + reasoning): {self.operation_state}\n"
            f"DEPENDENCY STATE (outstanding + compensation): {self.dependency_state}\n"
            f"Continuing role {self.owning_role_id} from session "
            f"{self.predecessor_session_id}."
        )
