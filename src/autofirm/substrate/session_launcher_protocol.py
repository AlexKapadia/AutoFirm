"""The process-spawn boundary: a launcher Protocol + a deterministic fake.

What this does
--------------
Abstracts the one impure act in the substrate — actually starting a ``claude``
CLI process — behind a narrow :class:`SessionLauncher` Protocol, so all the
lifecycle LOGIC (spawn/handoff/resume) is deterministic and unit-testable
without ever launching a real process.

* :class:`LaunchSpec` — the secret-free, validated description of *what* to
  launch (role id, system prompt, working dir, credential reference, optional
  resume-from session id). This is what the engine hands the launcher.
* :class:`LaunchResult` — what a launcher returns: the allocated/observed
  :class:`SessionId`. (Cost/turn metadata from the JSON envelope can be added
  later behind the same contract; it is intentionally minimal now.)
* :class:`SessionLauncher` — the Protocol the engine depends on. Production wires
  :class:`~autofirm.substrate.powershell_claude_launcher.PowerShellClaudeLauncher`;
  tests wire :class:`FakeSessionLauncher`.
* :class:`FakeSessionLauncher` — a deterministic test double that records every
  :class:`LaunchSpec` it was asked to launch and returns ids from an injected
  :class:`IdGenerator`. It NEVER spawns a process or touches the network, and it
  asserts (by recording specs) that no secret is ever passed to it.

Why it exists / where it sits
-----------------------------
A5 SYNTHESIS §1/§3: the per-agent execution unit is a ``claude -p`` process; the
substrate must be built on documented capability yet remain testable. The
classic seam for "impure I/O at the edge, pure logic in the middle" is to make
the spawn a Protocol the core depends on (dependency inversion). The engine never
imports the production launcher; it takes a :class:`SessionLauncher`, so a test
injects the fake and the production process is never invoked under test.

Security / compliance invariants upheld (CLAUDE.md §5.6)
-------------------------------------------------------
* **Secret never passed to the launcher (§5.6):** :class:`LaunchSpec` carries
  only a secret-free :class:`ScopedCredentialReference`; the raw secret is
  resolved by the production launcher at the point of process start, never put on
  the spec, so the fake (and any log of a spec) can never see it.
* **Validate at boundary (§5.6):** a spec with an empty role id / system prompt /
  working dir is refused at construction (no-spawn-without-spec).
* **Determinism (§3.11):** the fake's ids come from an injected generator, so a
  test predicts every spawned id.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, field_validator

from autofirm.modelgateway.cli_gateway_env_injection import (
    NonAnthropicModelRefused,
    is_anthropic_eligible,
)
from autofirm.modelgateway.model_reference import ModelRef
from autofirm.org.org_identifiers import IdGenerator, RoleId
from autofirm.substrate.scoped_credential_reference import ScopedCredentialReference
from autofirm.substrate.session_identity import SessionId, session_id_prefix

__all__ = [
    "FakeSessionLauncher",
    "LaunchResult",
    "LaunchSpec",
    "SessionLauncher",
]


class LaunchSpec(BaseModel):
    """A secret-free, validated description of a session to launch.

    Holds everything a launcher needs to start (or resume) a session EXCEPT the
    secret: the production launcher resolves the secret from the access layer at
    the point of process start using ``credential_reference``. ``resume_from`` is
    set only when relaunching after a failure (``claude --resume <id>`` semantics,
    A5 §3(8)); ``None`` for a fresh spawn.
    """

    model_config = ConfigDict(frozen=True)

    owning_role_id: RoleId  # the role this session serves
    system_prompt: str  # the role-scoped caller/system prompt (no secrets)
    working_dir: str  # the single-writer worktree/dir to run in
    credential_reference: ScopedCredentialReference  # secret-free; never the secret
    resume_from: SessionId | None = None  # prior session id to resume, or None
    model: ModelRef | None = None  # optional pinned model; Anthropic-eligible only (ADR-003)

    @field_validator("model")
    @classmethod
    def _model_anthropic_eligible(cls, value: ModelRef | None) -> ModelRef | None:
        # ADR-003 linchpin (fail-closed): a CLI session may pin ONLY an Anthropic-
        # family model -- a non-Anthropic model on the CLI lane is uncertified and is
        # refused here (that traffic must use the programmatic gateway lane).
        if value is not None and not is_anthropic_eligible(value):
            raise NonAnthropicModelRefused(
                f"LaunchSpec.model must be Anthropic-eligible for the CLI lane; "
                f"{value.provider.value}:{value.model_name} is refused"
            )
        return value

    @field_validator("system_prompt", "working_dir")
    @classmethod
    def _non_empty(cls, value: str) -> str:
        # fail-closed: an empty system prompt or working dir under-specifies the
        # launch -> refuse, so no session is ever spawned from a vague spec.
        if not value or not value.strip():
            raise ValueError("system_prompt and working_dir must be non-empty")
        return value

    @field_validator("owning_role_id")
    @classmethod
    def _non_empty_role(cls, value: RoleId) -> RoleId:
        # fail-closed: a session must belong to a real role (no orphan session).
        if not str(value).strip():
            raise ValueError("owning_role_id must be non-empty")
        return value


class LaunchResult(BaseModel):
    """What a launcher returns after (modelling) a session start: its session id."""

    model_config = ConfigDict(frozen=True)

    session_id: SessionId  # the allocated/observed CLI session id


@runtime_checkable
class SessionLauncher(Protocol):
    """The narrow boundary the engine depends on to start a session.

    The single impure seam: implementations may spawn a real process
    (production) or model it deterministically (tests). The engine never knows
    which, so its logic is the same under test and in production.
    """

    def launch(self, spec: LaunchSpec) -> LaunchResult:
        """Start (or resume) the session described by ``spec`` and return its id."""
        ...


class FakeSessionLauncher:
    """A deterministic, process-free :class:`SessionLauncher` for tests.

    Allocates session ids from an injected :class:`IdGenerator` (so a test
    predicts each id) and records every :class:`LaunchSpec` it received, which
    lets tests assert what *would* have been launched — and, crucially, that no
    secret was ever passed (a :class:`LaunchSpec` structurally cannot carry one).
    It never spawns a process and never touches the network.
    """

    def __init__(self, id_generator: IdGenerator) -> None:
        """Create a fake launcher drawing session ids from ``id_generator``."""
        self._id_generator = id_generator
        self._launched: list[LaunchSpec] = []

    def launch(self, spec: LaunchSpec) -> LaunchResult:
        """Record ``spec`` and return a deterministic id; NO real process starts."""
        self._launched.append(spec)
        session_id = SessionId(self._id_generator.next_id(session_id_prefix))
        return LaunchResult(session_id=session_id)

    def launched_specs(self) -> tuple[LaunchSpec, ...]:
        """Return every spec this fake was asked to launch (immutable snapshot)."""
        return tuple(self._launched)
