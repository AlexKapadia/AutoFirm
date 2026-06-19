"""CLI tests via Typer's CliRunner: up/status/doctor/down exit codes, no network, no real loops."""

from __future__ import annotations

import pytest
from typer.testing import CliRunner

from autofirm.runtime.cli_entrypoint import app

_runner = CliRunner()


@pytest.fixture
def _keyed_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Set a synthetic provider key so the gateway capability binds live (no real network)."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-synthetic-test")


@pytest.fixture
def _keyless_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Remove any provider key so the gateway degrades (the never-hard-block path)."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)


def test_cli_up__healthy_env_exits_zero_and_reports_green(_keyed_env: None) -> None:
    """`autofirm up` on a healthy synthetic config exits 0 with a GREEN readiness summary."""
    result = _runner.invoke(app, ["up"])
    assert result.exit_code == 0
    assert "readiness=green" in result.stdout


def test_cli_up__missing_optional_key_still_exits_zero_degraded(_keyless_env: None) -> None:
    """`autofirm up` with a missing OPTIONAL key still succeeds (degraded) — never hard-blocks."""
    result = _runner.invoke(app, ["up"])
    assert result.exit_code == 0  # NEVER a whole-platform hard block on a missing optional dep
    assert "readiness=degraded" in result.stdout


def test_cli_status__exits_zero_and_lists_capabilities(_keyed_env: None) -> None:
    """`autofirm status` re-runs the probes and exits 0, reporting the capability count."""
    result = _runner.invoke(app, ["status"])
    assert result.exit_code == 0
    assert "capabilities=8" in result.stdout


def test_cli_doctor__empty_probe_reports_missing_and_exits_nonzero() -> None:
    """`autofirm doctor` reports missing required steps from a bare probe and exits non-zero."""
    result = _runner.invoke(app, ["doctor"])
    assert result.exit_code == 1  # required steps missing -> fail-closed non-zero exit
    assert "missing=" in result.stdout


def test_cli_down__exits_zero_on_clean_drain(_keyed_env: None) -> None:
    """`autofirm down` cooperatively drains the loops and exits 0."""
    result = _runner.invoke(app, ["down"])
    assert result.exit_code == 0
    assert "drained loops=" in result.stdout


def test_cli__no_args_shows_help_not_a_crash() -> None:
    """Bare `autofirm` shows help (no_args_is_help) rather than erroring — discoverable DX."""
    result = _runner.invoke(app, [])
    # Typer maps no-args-is-help to a non-zero "usage shown" exit; the key property is it does
    # not crash and surfaces the four verbs.
    assert "up" in result.stdout
    assert "status" in result.stdout
    assert "doctor" in result.stdout
    assert "down" in result.stdout
