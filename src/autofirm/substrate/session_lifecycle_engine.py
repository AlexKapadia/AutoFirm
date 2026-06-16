"""The fail-closed engine that spawns, hands off, and resumes CLI sessions.

What this does
--------------
:class:`SessionLifecycleEngine` is the deterministic orchestration core of the
substrate. It owns the in-process registry of live sessions and performs the
three lifecycle operations, all as pure functions of injected inputs (a
:class:`SessionLauncher`, a :class:`Clock`, an :class:`IdGenerator`):

* :meth:`spawn` — start a brand-new session for a role. Fail-closed: refuses
  without a valid role id, a non-expired credential reference, and a working dir;
  refuses if a live session already owns the same single-writer artifact.
* :meth:`hand_off` — when a RUNNING session's context budget is exhausted, retire
  it (``-> HANDED_OFF``) and launch a fresh successor seeded with the
  re-grounded :class:`ContextHandoffSummary`. Modelled as a saga step
  (A3 SYNTHESIS L1.A3.3): the predecessor is checkpointed, then compensated to a
  retired state, then the successor takes over its single-writer dir.
* :meth:`resume` — relaunch a FAILED session. Fail-closed gate (A3 + CLAUDE.md
  §4.8): resume ONLY if (a) no live session is already running for that artifact
  AND (b) the work is not complete; an ambiguous situation is *refused*, never
  resumed (so resume is idempotent — calling it when a session is already live or
  the work is done changes nothing).

The "single-writer artifact" is the session's working directory: A5 SYNTHESIS
§1 establishes that two processes resuming/owning one writable dir interleave and
corrupt state, so the engine guarantees at most one live session per working dir.

Why it exists / where it sits
-----------------------------
This is the top of the substrate stack; everything else is the data + seams it
operates on. It never imports the production launcher — it depends only on the
:class:`SessionLauncher` Protocol — so unit tests inject the fake launcher and no
real process is ever spawned (CLAUDE.md §5.5).

Security / compliance invariants upheld (CLAUDE.md §3.2, §5.6)
-------------------------------------------------------------
* **No-spawn-without-spec/credential (§5.6):** spawn validates role + working dir
  + a non-expired credential reference before launching anything.
* **Single-writer (A5 §1):** at most one live (PENDING/RUNNING) session per
  working dir; a second spawn/resume for a busy dir is refused.
* **Fail-closed resume (§5.6):** ambiguity (already-live OR work-complete) ->
  refuse; resume is therefore idempotent and never double-runs work.
* **Secret never logged (§5.6):** the engine handles only secret-free references
  and summaries; the secret is the production launcher's concern, at point of use.
* **Determinism (§3.11):** launcher, clock, and id-generator are injected.
"""

from __future__ import annotations

from autofirm.org.org_identifiers import Clock, IdGenerator, RoleId
from autofirm.substrate.claude_session_model import ClaudeSession
from autofirm.substrate.context_budget_state import ContextBudgetState
from autofirm.substrate.context_handoff_summary import ContextHandoffSummary

# Note: ContextBudgetState is part of the spawn() signature (the caller supplies
# the initial window), so the import is load-bearing despite the successor budget
# being derived inside the handoff summary.
from autofirm.substrate.regrounded_saga_state import RegroundedSagaState
from autofirm.substrate.scoped_credential_reference import ScopedCredentialReference
from autofirm.substrate.session_identity import SessionId
from autofirm.substrate.session_launcher_protocol import LaunchSpec, SessionLauncher
from autofirm.substrate.session_status import SessionStatus

__all__ = [
    "ResumeRefused",
    "SessionLifecycleEngine",
    "SingleWriterViolation",
    "SpawnRefused",
]


class SpawnRefused(RuntimeError):
    """Raised when a spawn is fail-closed refused (bad spec or expired credential)."""


class SingleWriterViolation(RuntimeError):
    """Raised when an operation would put two live sessions on one working dir."""


class ResumeRefused(RuntimeError):
    """Raised when a resume is fail-closed refused (already live, or work complete)."""


# Sessions that still "own" their single-writer working dir: anything not terminal.
# A HANDED_OFF/COMPLETED/FAILED session has released the dir (its successor, if
# any, is a distinct live session), so only PENDING/RUNNING count as live owners.
_LIVE_STATES = frozenset({SessionStatus.PENDING, SessionStatus.RUNNING})


class SessionLifecycleEngine:
    """Deterministic, fail-closed manager of the in-process session lifecycle.

    Holds a registry keyed by :class:`SessionId`. All impurity (process spawn,
    time, id allocation) is injected, so the engine's behaviour is a pure function
    of its inputs and fully unit-testable with a fake launcher.
    """

    def __init__(
        self,
        launcher: SessionLauncher,
        clock: Clock,
        id_generator: IdGenerator,
    ) -> None:
        """Wire the engine to an injected launcher, clock, and id-generator."""
        self._launcher = launcher
        self._clock = clock
        self._id_generator = id_generator  # reserved for engine-side id needs
        self._sessions: dict[SessionId, ClaudeSession] = {}

    def sessions(self) -> tuple[ClaudeSession, ...]:
        """Return an immutable snapshot of every registered session."""
        return tuple(self._sessions.values())

    def _live_session_for_dir(self, working_dir: str) -> ClaudeSession | None:
        """Return the live (PENDING/RUNNING) session owning ``working_dir``, if any.

        The single-writer authority: there is at most one such session by
        construction (every mutator below preserves it).
        """
        for session in self._sessions.values():
            if session.working_dir == working_dir and session.status in _LIVE_STATES:
                return session
        return None

    def spawn(
        self,
        *,
        owning_role_id: RoleId,
        system_prompt: str,
        working_dir: str,
        credential_reference: ScopedCredentialReference,
        budget: ContextBudgetState,
    ) -> ClaudeSession:
        """Spawn a new RUNNING session for a role (fail-closed on every precondition).

        Refuses (``SpawnRefused``) without a non-empty role id / working dir or
        with an expired credential reference; refuses (``SingleWriterViolation``)
        if a live session already owns ``working_dir``. On success, launches via
        the injected launcher and registers the session as RUNNING.
        """
        # fail-closed: no-spawn-without-spec -- a missing role or dir under-specifies.
        if not str(owning_role_id).strip() or not working_dir.strip():
            raise SpawnRefused("spawn requires a non-empty role id and working dir")
        # fail-closed: never spawn against an expired credential (no-spawn-without-
        # valid-credential). Checked at the injected clock's now for determinism.
        if not credential_reference.is_valid_at(self._clock.now()):
            raise SpawnRefused("credential reference is expired; refusing to spawn")
        # single-writer: refuse a second live session on the same working dir.
        if self._live_session_for_dir(working_dir) is not None:
            raise SingleWriterViolation(
                f"a live session already owns working dir {working_dir!r}"
            )

        spec = LaunchSpec(
            owning_role_id=owning_role_id,
            system_prompt=system_prompt,
            working_dir=working_dir,
            credential_reference=credential_reference,  # secret-free
            resume_from=None,
        )
        result = self._launcher.launch(spec)
        # Model the confirmed start as PENDING -> RUNNING through the guarded
        # transition, so even the spawn path honours the legal-transition table.
        session = ClaudeSession(
            session_id=result.session_id,
            owning_role_id=owning_role_id,
            credential_reference=credential_reference,
            working_dir=working_dir,
            status=SessionStatus.PENDING,
            budget=budget,
        ).mark_running()
        self._sessions[session.session_id] = session
        return session

    def record_consumption(self, session_id: SessionId, tokens: int) -> ClaudeSession:
        """Record that ``session_id`` consumed ``tokens`` more of its budget."""
        session = self._require_session(session_id)
        updated = session.with_consumed(tokens)
        self._sessions[session_id] = updated
        return updated

    def hand_off(
        self, session_id: SessionId, state: RegroundedSagaState
    ) -> ClaudeSession:
        """Hand a budget-exhausted RUNNING session off to a fresh successor.

        Refuses unless the session actually needs a handoff (RUNNING + exhausted),
        so a handoff can never be forced on a session with budget left or on a
        non-running one. Retires the predecessor (``-> HANDED_OFF``), then launches
        the successor seeded with the re-grounded ``state``, on the SAME working
        dir (the predecessor has released it by going terminal). Returns the
        successor.
        """
        session = self._require_session(session_id)
        # fail-closed: only a RUNNING session whose budget is exhausted may hand off;
        # anything else is a programming error, not a spurious successor spawn.
        if not session.needs_handoff():
            raise SpawnRefused(
                "hand_off requires a RUNNING session with an exhausted budget"
            )

        summary = ContextHandoffSummary.from_session(session, state)
        # Saga step: checkpoint+compensate the predecessor to a retired state FIRST,
        # so the working dir is released before the successor claims it (preserves
        # single-writer: there is no instant where two live sessions share the dir).
        self._sessions[session_id] = session.mark_handed_off()
        return self._launch_successor(summary, resume_from=session_id)

    def resume(
        self, session_id: SessionId, state: RegroundedSagaState
    ) -> ClaudeSession:
        """Fail-closed resume of a FAILED session; idempotent under ambiguity.

        Resumes ONLY if both gates pass: (a) no live session already owns the
        working dir, AND (b) ``state.work_complete`` is False. If either is true
        the resume is *refused* (``ResumeRefused``) — so calling resume when a
        session is already running, or when the work is done, is a safe
        no-op-by-refusal, making resume idempotent and incapable of double-running
        work.
        """
        session = self._require_session(session_id)
        # fail-closed: only a FAILED session is resumable; a terminal-but-not-failed
        # (handed-off/completed) or still-live session must not be "resumed".
        if session.status is not SessionStatus.FAILED:
            raise ResumeRefused(
                f"only a FAILED session may be resumed (was {session.status.value})"
            )
        # fail-closed gate (a): refuse if a live session already owns this dir, so a
        # resume can never create a second concurrent writer (A5 §1 single-writer).
        if self._live_session_for_dir(session.working_dir) is not None:
            raise ResumeRefused("a live session already owns this working dir; refusing")
        # fail-closed gate (b): refuse if the work is already complete, so resume
        # never re-runs finished work (idempotency: completed -> nothing to do).
        if state.work_complete:
            raise ResumeRefused("work is already complete; refusing to resume")

        summary = ContextHandoffSummary.from_session(session, state)
        return self._launch_successor(summary, resume_from=session_id)

    def _launch_successor(
        self, summary: ContextHandoffSummary, *, resume_from: SessionId
    ) -> ClaudeSession:
        """Launch + register the successor session described by ``summary``.

        Shared by handoff and resume: builds a :class:`LaunchSpec` with the
        re-grounding system prompt and ``--resume`` semantics, launches via the
        injected launcher, and registers the successor RUNNING on the working dir.
        A fresh budget is started for the successor (a new context window).
        """
        spec = LaunchSpec(
            owning_role_id=summary.owning_role_id,
            system_prompt=summary.render_system_prompt(),  # re-grounded, secret-free
            working_dir=summary.working_dir,
            credential_reference=summary.credential_reference,  # secret-free
            resume_from=resume_from,
        )
        result = self._launcher.launch(spec)
        successor = ClaudeSession(
            session_id=result.session_id,
            owning_role_id=summary.owning_role_id,
            credential_reference=summary.credential_reference,
            working_dir=summary.working_dir,
            status=SessionStatus.PENDING,
            # fresh context window for the successor: the summary already derived a
            # zero-consumption budget at the predecessor's limit/threshold.
            budget=summary.successor_budget,
        ).mark_running()
        self._sessions[successor.session_id] = successor
        return successor

    def _require_session(self, session_id: SessionId) -> ClaudeSession:
        """Return the registered session or refuse (fail-closed on unknown id)."""
        session = self._sessions.get(session_id)
        if session is None:
            # fail-closed: operating on an unknown session is ambiguous -> refuse.
            raise ResumeRefused(f"unknown session id {session_id!r}")
        return session
