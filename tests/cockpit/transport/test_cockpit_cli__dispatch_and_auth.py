"""cockpit_cli: subcommand dispatch, deny-by-default auth, exact exit codes, no-data-on-refusal."""

from __future__ import annotations

import sys
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path

import pytest

from autofirm.cockpit.composition.cockpit_composer import assemble_cockpit
from autofirm.cockpit.composition.cockpit_config import CockpitConfig
from autofirm.cockpit.core.cockpit_version import cockpit_version
from autofirm.cockpit.eventlog.cockpit_event_contract import CockpitEventKind
from autofirm.cockpit.transport import cockpit_cli
from autofirm.cockpit.transport.cockpit_cli import main
from autofirm.cockpit.transport.operator_auth_gate import OPERATOR_TOKEN_ENV_VAR
from autofirm.org.org_identifiers import FrozenClock

_SECRET = "operator-secret-token"
_OK = 0
_NONZERO_FLOOR = 1


def _env(value: str | None = _SECRET) -> Mapping[str, str]:
    return {} if value is None else {OPERATOR_TOKEN_ENV_VAR: value}


# --------------------------- version (no auth) --------------------------- #


def test_version_needs_no_auth_and_prints_version(capsys: pytest.CaptureFixture[str]) -> None:
    code = main(["version"], env=_env(None))  # empty env: still succeeds (version leaks nothing)
    assert code == _OK
    out = capsys.readouterr().out
    assert cockpit_version() in out


def test_version_with_default_env_none(capsys: pytest.CaptureFixture[str]) -> None:
    # env=None exercises the live-os.environ resolution path; version needs no secret.
    assert main(["version"]) == _OK
    assert cockpit_version() in capsys.readouterr().out


# --------------------------- run (auth-gated) --------------------------- #


def test_run_with_correct_token_prints_snapshot(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code = main(
        ["run", "--token", _SECRET, "--event-log", str(tmp_path / "e.ndjson")], env=_env()
    )
    assert code == _OK
    out = capsys.readouterr().out
    assert "cockpit ready" in out
    assert "roles:" in out
    assert "kill-switch:" in out


def test_run_with_wrong_token_refuses_and_emits_no_data(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code = main(
        ["run", "--token", "WRONG", "--event-log", str(tmp_path / "e.ndjson")], env=_env()
    )
    assert code >= _NONZERO_FLOOR
    captured = capsys.readouterr()
    assert captured.out == ""  # NO cockpit data on a refused command
    assert "authentication refused" in captured.err
    assert "WRONG" not in captured.err  # token never echoed


def test_run_without_token_refuses(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    code = main(["run", "--event-log", str(tmp_path / "e.ndjson")], env=_env())
    assert code >= _NONZERO_FLOOR
    assert capsys.readouterr().out == ""


def test_run_refuses_when_no_secret_configured(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code = main(
        ["run", "--token", _SECRET, "--event-log", str(tmp_path / "e.ndjson")], env=_env(None)
    )
    assert code >= _NONZERO_FLOOR
    assert capsys.readouterr().out == ""


# --------------------------- replay (auth-gated) --------------------------- #


def _seed_log(path: Path) -> None:
    """Record one event into ``path`` so replay has something to print."""
    cfg = CockpitConfig(event_log_path=path, currency="USD")
    app = assemble_cockpit(cfg, clock=FrozenClock(datetime(2026, 6, 19, tzinfo=UTC)))
    app.record_event(CockpitEventKind.ORG_CHANGED, "seed", {"detail": "hired"})


def test_replay_with_correct_token_prints_events(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    log = tmp_path / "events.ndjson"
    _seed_log(log)
    code = main(["replay", "--token", _SECRET, "--event-log", str(log)], env=_env())
    assert code == _OK
    out = capsys.readouterr().out
    assert "events: 1" in out
    assert "org_changed seed" in out  # "<seq> <kind> <source>"


def test_replay_with_wrong_token_refuses_and_emits_no_data(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    log = tmp_path / "events.ndjson"
    _seed_log(log)
    code = main(["replay", "--token", "NOPE", "--event-log", str(log)], env=_env())
    assert code >= _NONZERO_FLOOR
    captured = capsys.readouterr()
    assert captured.out == ""  # the log is NOT replayed for an unauthenticated caller
    assert "NOPE" not in captured.err


# --------------------------- deny-by-default dispatch --------------------------- #


def test_unknown_subcommand_is_nonzero() -> None:
    assert main(["bogus-subcommand"], env=_env()) >= _NONZERO_FLOOR


def test_no_subcommand_is_nonzero(capsys: pytest.CaptureFixture[str]) -> None:
    code = main([], env=_env())
    assert code >= _NONZERO_FLOOR
    assert "no subcommand" in capsys.readouterr().err


# --------------------------- helper coverage --------------------------- #


def test_exit_code_of_none_is_ok() -> None:
    assert cockpit_cli._exit_code_of(SystemExit()) == _OK


def test_exit_code_of_int_is_passed_through() -> None:
    assert cockpit_cli._exit_code_of(SystemExit(2)) == 2


def test_exit_code_of_string_is_usage_error() -> None:
    assert cockpit_cli._exit_code_of(SystemExit("bad usage")) >= _NONZERO_FLOOR


class _StdoutWithReconfigure:
    def __init__(self) -> None:
        self.encoding_set: str | None = None

    def reconfigure(self, *, encoding: str) -> None:
        self.encoding_set = encoding


class _StdoutWithoutReconfigure:
    """A stdout-like object that deliberately lacks reconfigure (the cp1252 fallback path)."""


def test_force_utf8_reconfigures_when_supported(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = _StdoutWithReconfigure()
    monkeypatch.setattr(sys, "stdout", fake)
    cockpit_cli._force_utf8_stdout()
    assert fake.encoding_set == "utf-8"


def test_force_utf8_is_noop_when_unsupported(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "stdout", _StdoutWithoutReconfigure())
    cockpit_cli._force_utf8_stdout()  # must not raise on a stream without reconfigure
