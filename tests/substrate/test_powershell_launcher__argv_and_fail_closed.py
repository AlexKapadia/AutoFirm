"""Tests for the production launcher: PURE argv build + fail-closed spawn guards.

``build_argument_vector`` is a pure spec->argv function (no I/O), so it is fully
unit-testable: these tests assert the headless ``claude`` argv shape, the
``--resume`` append, and — critically — that NO secret ever appears in the argv.
The ``launch`` path's fail-closed guards (expired ref, missing secret) are
exercised WITHOUT a real process by injecting a fake clock + secret resolver and
monkeypatching ``subprocess.run``. Synthetic only; no real ``claude`` ever runs.
"""

from __future__ import annotations

import json
from datetime import timedelta

import pytest

from autofirm.modelgateway.cli_gateway_env_injection import (
    ANTHROPIC_AUTH_TOKEN_ENV,
    ANTHROPIC_BASE_URL_ENV,
    GATEWAY_MODEL_DISCOVERY_ENV,
)
from autofirm.modelgateway.model_reference import ModelProvider, ModelRef
from autofirm.org.org_identifiers import RoleId
from autofirm.substrate import powershell_claude_launcher as launcher_module
from autofirm.substrate.powershell_claude_launcher import (
    LaunchRefused,
    PowerShellClaudeLauncher,
)
from autofirm.substrate.session_identity import SessionId
from autofirm.substrate.session_launcher_protocol import LaunchSpec
from tests.substrate.synthetic_substrate_fixtures import (
    FIXED_NOW,
    SECRET_SENTINEL,
    FrozenNow,
    make_credential_reference,
)

# A synthetic gateway URL (non-secret config) the launcher is pointed at in tests.
_GATEWAY_URL = "http://localhost:18080/v1"
# A synthetic Anthropic-family model the CLI lane is allowed to pin.
_CLAUDE_MODEL = ModelRef(provider=ModelProvider.ANTHROPIC, model_name="claude-haiku")


def _spec(
    *, resume_from: SessionId | None = None, model: ModelRef | None = None
) -> LaunchSpec:
    return LaunchSpec(
        owning_role_id=RoleId("role-1"),
        system_prompt="you are a worker",
        working_dir="/wt/a",
        credential_reference=make_credential_reference(),
        resume_from=resume_from,
        model=model,
    )


def _launcher(resolver: object, *, clock: FrozenNow | None = None) -> PowerShellClaudeLauncher:
    """Build a launcher with the synthetic gateway URL (new 3-arg signature)."""
    return PowerShellClaudeLauncher(clock or FrozenNow(), resolver, _GATEWAY_URL)  # type: ignore[arg-type]


class _FixedSecretResolver:
    """A fake resolver returning a planted secret (or None to force a refusal)."""

    def __init__(self, secret: str | None) -> None:
        self._secret = secret
        self.calls: list[tuple[str, str, str]] = []

    def resolve_secret(self, component: str, resource: str, tenant_id: str) -> str | None:
        self.calls.append((component, resource, tenant_id))
        return self._secret


@pytest.mark.unit
def test_build_argument_vector_is_headless_and_secret_free() -> None:
    argv = PowerShellClaudeLauncher.build_argument_vector(_spec())
    assert argv[:5] == ["claude", "-p", "--bare", "--output-format", "json"]
    assert "--dangerously-skip-permissions" in argv
    assert argv[argv.index("--add-dir") + 1] == "/wt/a"  # single-writer dir pin
    assert argv[argv.index("--append-system-prompt") + 1] == "you are a worker"
    assert "--resume" not in argv  # no resume on a fresh spec
    # secrets-never-logged: the secret never reaches argv (the spec cannot carry it).
    assert all(SECRET_SENTINEL not in part for part in argv)


@pytest.mark.unit
def test_build_argument_vector_appends_resume_for_relaunch() -> None:
    argv = PowerShellClaudeLauncher.build_argument_vector(
        _spec(resume_from=SessionId("session-prev"))
    )
    assert argv[-2:] == ["--resume", "session-prev"]  # continues the prior transcript


@pytest.mark.unit
@pytest.mark.security
def test_launch_refuses_expired_credential_without_spawning(monkeypatch) -> None:
    resolver = _FixedSecretResolver(SECRET_SENTINEL + "x")
    # Clock is past expiry -> must refuse BEFORE touching the secret or a process.
    launcher = _launcher(resolver, clock=FrozenNow(start=FIXED_NOW + timedelta(hours=2)))

    def _boom(*_a, **_k):  # pragma: no cover - asserts it is never reached
        raise AssertionError("subprocess.run must not be called on a refused launch")

    monkeypatch.setattr(launcher_module.subprocess, "run", _boom)
    with pytest.raises(LaunchRefused, match="expired"):
        launcher.launch(_spec())
    assert resolver.calls == []  # secret never even requested for a dead credential


@pytest.mark.unit
@pytest.mark.security
def test_launch_refuses_when_no_secret_available(monkeypatch) -> None:
    resolver = _FixedSecretResolver(None)  # secret source returns nothing
    launcher = _launcher(resolver)

    def _boom(*_a, **_k):  # pragma: no cover - asserts it is never reached
        raise AssertionError("subprocess.run must not be called on a refused launch")

    monkeypatch.setattr(launcher_module.subprocess, "run", _boom)
    with pytest.raises(LaunchRefused, match="no secret"):  # fail-closed, never blank
        launcher.launch(_spec())


@pytest.mark.unit
@pytest.mark.security
def test_launch_injects_secret_via_env_only_never_argv(monkeypatch) -> None:
    planted = SECRET_SENTINEL + "topsecret"
    resolver = _FixedSecretResolver(planted)
    launcher = _launcher(resolver)
    captured: dict[str, object] = {}

    class _Completed:
        stdout = json.dumps({"session_id": "session-xyz"})

    def _fake_run(argv, **kwargs):  # records argv + env without running anything
        captured["argv"] = argv
        captured["env"] = kwargs["env"]
        return _Completed()

    monkeypatch.setattr(launcher_module.subprocess, "run", _fake_run)
    result = launcher.launch(_spec())
    assert result.session_id == "session-xyz"  # parsed from the JSON envelope
    # secrets-never-logged: secret is in the child ENV, NOT in the argv.
    assert all(planted not in str(part) for part in captured["argv"])  # type: ignore[union-attr]
    assert planted in captured["env"].values()  # type: ignore[union-attr]


@pytest.mark.unit
def test_build_argument_vector_threads_pinned_model_into_argv() -> None:
    # The model NAME (non-secret routing metadata) is safe on argv as `--model <name>`.
    argv = PowerShellClaudeLauncher.build_argument_vector(_spec(model=_CLAUDE_MODEL))
    assert argv[argv.index("--model") + 1] == "claude-haiku"


@pytest.mark.unit
def test_build_argument_vector_omits_model_flag_when_unpinned() -> None:
    assert "--model" not in PowerShellClaudeLauncher.build_argument_vector(_spec())


@pytest.mark.unit
@pytest.mark.security
def test_launch_injects_gateway_env_for_anthropic_model(monkeypatch) -> None:
    # A pinned Anthropic model => the three gateway env vars are injected via the
    # child ENV (never argv), and the auth-token VALUE is the resolved virtual key.
    planted = SECRET_SENTINEL + "virtualkey"
    resolver = _FixedSecretResolver(planted)
    launcher = _launcher(resolver)
    captured: dict[str, object] = {}

    class _Completed:
        stdout = json.dumps({"session_id": "session-g"})

    def _fake_run(argv, **kwargs):
        captured["argv"] = argv
        captured["env"] = kwargs["env"]
        return _Completed()

    monkeypatch.setattr(launcher_module.subprocess, "run", _fake_run)
    launcher.launch(_spec(model=_CLAUDE_MODEL))
    env = captured["env"]  # type: ignore[assignment]
    assert env[ANTHROPIC_BASE_URL_ENV] == _GATEWAY_URL
    assert env[GATEWAY_MODEL_DISCOVERY_ENV] == "1"
    # the per-session virtual key is the auth-token VALUE — and never on argv.
    assert env[ANTHROPIC_AUTH_TOKEN_ENV] == planted
    assert all(planted not in str(part) for part in captured["argv"])  # type: ignore[union-attr]


@pytest.mark.unit
@pytest.mark.security
def test_launch_omits_gateway_env_when_model_unpinned(monkeypatch) -> None:
    # No pinned model => no gateway env injected (the CLI uses its default config).
    resolver = _FixedSecretResolver(SECRET_SENTINEL + "k")
    launcher = _launcher(resolver)
    captured: dict[str, object] = {}

    class _Completed:
        stdout = json.dumps({"session_id": "session-h"})

    monkeypatch.setattr(
        launcher_module.subprocess,
        "run",
        lambda argv, **kw: captured.update(env=kw["env"]) or _Completed(),
    )
    launcher.launch(_spec())
    assert ANTHROPIC_BASE_URL_ENV not in captured["env"]  # type: ignore[operator]


@pytest.mark.unit
@pytest.mark.security
def test_launcher_construction_refuses_empty_gateway_url() -> None:
    # fail-closed: a launcher pointed at no gateway cannot egress — refuse to build it.
    with pytest.raises(ValueError, match="gateway_base_url"):
        PowerShellClaudeLauncher(FrozenNow(), _FixedSecretResolver("k"), "  ")
