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


def _spec(*, resume_from: SessionId | None = None) -> LaunchSpec:
    return LaunchSpec(
        owning_role_id=RoleId("role-1"),
        system_prompt="you are a worker",
        working_dir="/wt/a",
        credential_reference=make_credential_reference(),
        resume_from=resume_from,
    )


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
    launcher = PowerShellClaudeLauncher(
        FrozenNow(start=FIXED_NOW + timedelta(hours=2)), resolver
    )

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
    launcher = PowerShellClaudeLauncher(FrozenNow(), resolver)

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
    launcher = PowerShellClaudeLauncher(FrozenNow(), resolver)
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
