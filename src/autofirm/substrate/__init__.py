"""Claude-CLI session substrate: the runtime that runs each role as a CLI session.

What this package does
----------------------
This is AutoFirm's **substrate runtime** — the layer that runs each AutoFirm
role/team as an orchestrated ``claude`` Code CLI session, with deterministic
context-handoff and fail-closed auto-resume. It is built on the documented CLI
capabilities (``docs/research/A5-claude-code-substrate/SYNTHESIS.md``) and the
long-horizon autonomy model (``docs/research/A3-long-horizon-autonomy/SYNTHESIS.md``).

The single impure act — actually spawning a ``claude`` process — is abstracted
behind the :class:`SessionLauncher` Protocol, so every lifecycle decision
(spawn / handoff / resume) is pure, deterministic, and unit-testable WITHOUT ever
starting a real process. Production wires :class:`PowerShellClaudeLauncher`;
tests wire :class:`FakeSessionLauncher`.

Layering (low -> high)
----------------------
* :mod:`~autofirm.substrate.session_identity` — typed ``SessionId`` + injected
  ``Clock`` / ``IdGenerator`` determinism seams (reused from ``autofirm.org``).
* :mod:`~autofirm.substrate.scoped_credential_reference` — a secret-free pointer
  to the credential a session holds (the secret never lives on a session).
* :mod:`~autofirm.substrate.context_budget_state` — context-window accounting +
  the fail-closed handoff threshold.
* :mod:`~autofirm.substrate.session_status` — the status enum + legal transitions.
* :mod:`~autofirm.substrate.claude_session_model` — the typed ``ClaudeSession``.
* :mod:`~autofirm.substrate.session_launcher_protocol` — the spawn boundary + fake.
* :mod:`~autofirm.substrate.powershell_claude_launcher` — the production launcher.
* :mod:`~autofirm.substrate.context_handoff_summary` — the re-grounded handoff
  state (goal verbatim + SA/SO/SD) carried to a successor session.
* :mod:`~autofirm.substrate.session_lifecycle_engine` — the fail-closed engine
  that spawns, hands off, and resumes sessions.

Security / compliance invariants upheld (CLAUDE.md §3.2, §5.6)
-------------------------------------------------------------
* **Fail closed everywhere:** no spawn without a role spec + valid scoped
  credential; ambiguous resume is refused; illegal status transitions are refused.
* **Secrets never logged / never stored on a session:** sessions carry only a
  secret-free credential reference; the secret is resolved at the point of process
  start and injected via the child env, never argv / prompt / transcript.
* **Single-writer:** at most one live (PENDING/RUNNING) session per owned
  single-writer artifact, enforced by the engine.
* **Deterministic:** time, identity, and the launcher are injected, so a run is a
  pure function of (state, clock, id-generator, launcher, operations).
"""

from __future__ import annotations

from autofirm.substrate.claude_session_model import (
    ClaudeSession,
    SessionTransitionError,
)
from autofirm.substrate.context_budget_state import ContextBudgetState
from autofirm.substrate.context_handoff_summary import ContextHandoffSummary
from autofirm.substrate.powershell_claude_launcher import (
    LaunchRefused,
    PowerShellClaudeLauncher,
    SecretResolver,
)
from autofirm.substrate.regrounded_saga_state import RegroundedSagaState
from autofirm.substrate.scoped_credential_reference import ScopedCredentialReference
from autofirm.substrate.session_identity import SessionId
from autofirm.substrate.session_launcher_protocol import (
    FakeSessionLauncher,
    LaunchResult,
    LaunchSpec,
    SessionLauncher,
)
from autofirm.substrate.session_lifecycle_engine import (
    ResumeRefused,
    SessionLifecycleEngine,
    SingleWriterViolation,
    SpawnRefused,
)
from autofirm.substrate.session_status import SessionStatus

__all__ = [
    "ClaudeSession",
    "ContextBudgetState",
    "ContextHandoffSummary",
    "FakeSessionLauncher",
    "LaunchRefused",
    "LaunchResult",
    "LaunchSpec",
    "PowerShellClaudeLauncher",
    "RegroundedSagaState",
    "ResumeRefused",
    "ScopedCredentialReference",
    "SecretResolver",
    "SessionId",
    "SessionLauncher",
    "SessionLifecycleEngine",
    "SessionStatus",
    "SessionTransitionError",
    "SingleWriterViolation",
    "SpawnRefused",
]
