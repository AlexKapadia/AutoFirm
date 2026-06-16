"""Production launcher that builds + runs the real ``claude`` CLI invocation.

What this does
--------------
Implements the :class:`~autofirm.substrate.session_launcher_protocol.SessionLauncher`
Protocol against the real Claude Code CLI. It builds the argument vector for a
headless, host-independent invocation —

    claude -p --bare --output-format json --dangerously-skip-permissions \
        --add-dir <working_dir> --append-system-prompt <role prompt> \
        [--resume <prior session id>]

per A5 SYNTHESIS §3(1) (``-p --bare --output-format json`` as the execution
unit) — resolves the credential's secret *at the point of start* from an injected
secret source, injects it into the child process ENVIRONMENT (never an argv flag,
never a log line, never the system prompt), spawns the process, and parses the
JSON envelope to capture the ``session_id``.

Why the build is split from the spawn
-------------------------------------
:meth:`build_argument_vector` is a PURE function (spec -> argv list) with no I/O,
so it is fully unit-testable on its own. The actual spawn lives in
:meth:`launch`, which is the only method that touches the process/secret layer
and is therefore exercised by integration wiring, NOT by unit tests — unit tests
assert the argv shape and never start a process (CLAUDE.md §5.5 no-network /
no-real-process).

Security / compliance invariants upheld (CLAUDE.md §5.6)
-------------------------------------------------------
* **Secret never in argv / logs / prompt (§5.6):** the secret is read from the
  injected secret source only inside :meth:`launch` and passed via an environment
  variable to the child; :meth:`build_argument_vector` never receives or emits
  it, so no constructed command line can contain it.
* **Fail-closed (§5.6):** ``launch`` refuses to start if the credential reference
  is expired at the injected clock's now, or if the secret source returns no
  secret for the referenced credential — an ambiguous/missing secret is a refusal,
  never a launch with a blank credential.
* **Single-writer working dir:** the session is pinned to one ``--add-dir`` so two
  sessions never share a writable worktree.
"""

from __future__ import annotations

import json
import subprocess  # nosec B404 - spawning the claude CLI is this module's whole job
from typing import Protocol

from autofirm.substrate.session_identity import Clock, SessionId
from autofirm.substrate.session_launcher_protocol import LaunchResult, LaunchSpec

__all__ = ["LaunchRefused", "PowerShellClaudeLauncher", "SecretResolver"]

# The environment variable the secret is injected into for the child process.
# Using the env (not an argv flag) keeps the secret off the visible command line
# and out of any process-list or shell-history exposure.
# nosec B105 - this is the NAME of the env var, never a secret value itself.
_SECRET_ENV_VAR = "AUTOFIRM_SESSION_CREDENTIAL"  # nosec B105


class LaunchRefused(RuntimeError):
    """Raised when a launch is fail-closed refused (expired/missing credential)."""


class SecretResolver(Protocol):
    """Resolves a credential reference to its secret AT THE POINT OF USE only.

    The substrate never stores secrets; the production launcher asks a resolver
    (backed by the access layer's credential broker / secret source) for the
    secret for a given component+resource the instant before it spawns, then drops
    it into the child env. Returning ``None`` means "no secret available" and the
    launcher fails closed.
    """

    def resolve_secret(self, component: str, resource: str, tenant_id: str) -> str | None:
        """Return the raw secret for this credential, or ``None`` if unavailable."""
        ...


class PowerShellClaudeLauncher:
    """A production :class:`SessionLauncher` that spawns the real ``claude`` CLI.

    Named for the Windows/PowerShell host AutoFirm runs on, but the argv it builds
    is host-independent (``--bare``). It is NEVER instantiated or invoked by unit
    tests; only :meth:`build_argument_vector` (pure) is unit-tested.
    """

    def __init__(self, clock: Clock, secret_resolver: SecretResolver) -> None:
        """Create a launcher using ``clock`` for expiry checks + ``secret_resolver``."""
        self._clock = clock
        self._secret_resolver = secret_resolver

    @staticmethod
    def build_argument_vector(spec: LaunchSpec) -> list[str]:
        """Return the secret-free ``claude`` argv for ``spec`` (PURE, no I/O).

        The system prompt and working dir come straight from the spec; NO secret
        appears here by construction (the spec cannot carry one). When
        ``spec.resume_from`` is set, ``--resume <id>`` is appended so a relaunch
        continues the prior session's transcript (A5 §3(8)).
        """
        argv = [
            "claude",
            "-p",
            "--bare",
            "--output-format",
            "json",
            # documented headless, non-interactive authority mode (A5 §3(1));
            # the HARD authority boundary is the managed permission/sandbox layer,
            # not this flag (A5 §1, L1.A5.3) -- this only suppresses prompts.
            "--dangerously-skip-permissions",
            "--add-dir",
            spec.working_dir,  # single-writer worktree pin
            "--append-system-prompt",
            spec.system_prompt,  # role-scoped prompt; secret-free by validation
        ]
        if spec.resume_from is not None:
            argv += ["--resume", str(spec.resume_from)]
        return argv

    def launch(self, spec: LaunchSpec) -> LaunchResult:
        """Resolve the secret, spawn the CLI, and parse the session id from JSON.

        Fail-closed: refuses if the credential reference is expired now or if the
        secret source has no secret for it. The secret is injected via the child
        ENV only and never logged or placed on the command line.
        """
        ref = spec.credential_reference
        # fail-closed: never spawn against an expired credential reference.
        if not ref.is_valid_at(self._clock.now()):
            raise LaunchRefused("credential reference is expired; refusing to launch")
        # secret resolved at point of use only; never stored on the session/spec.
        secret = self._secret_resolver.resolve_secret(
            ref.component, ref.resource, ref.tenant_id
        )
        # fail-closed: a missing/ambiguous secret is a refusal, not a blank launch.
        if not secret:
            raise LaunchRefused("no secret available for credential; refusing to launch")

        argv = self.build_argument_vector(spec)
        # secrets-never-logged: the secret goes into the child ENV, not argv; argv
        # (which may be logged/inspected) is structurally secret-free.
        child_env = {_SECRET_ENV_VAR: secret}
        completed = subprocess.run(  # nosec B603 - argv is built from validated, secret-free fields
            argv,
            cwd=spec.working_dir,
            env=child_env,
            capture_output=True,
            text=True,
            check=True,
        )
        envelope = json.loads(completed.stdout)
        return LaunchResult(session_id=SessionId(str(envelope["session_id"])))
