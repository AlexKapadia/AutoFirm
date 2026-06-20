"""cockpit_cli `tui`: auth-gated launch, build/run separation, no app on a refused command."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path

import pytest

from autofirm.cockpit.composition.cockpit_application import CockpitApplication
from autofirm.cockpit.composition.cockpit_composer import assemble_cockpit
from autofirm.cockpit.composition.cockpit_config import CockpitConfig
from autofirm.cockpit.transport.cockpit_cli import build_tui_app, main
from autofirm.cockpit.transport.operator_auth_gate import OPERATOR_TOKEN_ENV_VAR
from autofirm.cockpit.tui.cockpit_app import CockpitApp
from autofirm.org.org_identifiers import FrozenClock

_SECRET = "operator-secret-token"
_OK = 0
_NONZERO_FLOOR = 1


def _env(value: str | None = _SECRET) -> Mapping[str, str]:
    return {} if value is None else {OPERATOR_TOKEN_ENV_VAR: value}


def test_tui_listed_in_top_level_help(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["--help"]) == _OK
    assert "tui" in capsys.readouterr().out


def test_tui_subcommand_help_lists_token(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["tui", "--help"]) == _OK
    assert "--token" in capsys.readouterr().out


def test_tui_with_correct_token_builds_and_runs_app(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    launched: list[CockpitApp] = []
    # Replace the blocking .run() (needs a real terminal) with a recorder.
    monkeypatch.setattr(CockpitApp, "run", lambda self, *a, **k: launched.append(self))
    code = main(
        ["tui", "--token", _SECRET, "--event-log", str(tmp_path / "e.ndjson")], env=_env()
    )
    assert code == _OK
    assert len(launched) == 1
    assert isinstance(launched[0], CockpitApp)


def test_tui_launches_app_holding_a_real_assembled_cockpit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The launched TUI must hold the ASSEMBLED cockpit, not a ``None`` read model.

    Kills the `app = assemble_cockpit(...)` -> `app = None` mutant in ``_tui``: with
    ``app=None`` the handler still builds a ``CockpitApp(None)`` and runs it, so an
    ``isinstance(..., CockpitApp)`` check alone passes. Asserting the launched app's
    ``_read_model`` is a real :class:`CockpitApplication` makes the mutation fail.
    """
    launched: list[CockpitApp] = []
    monkeypatch.setattr(CockpitApp, "run", lambda self, *a, **k: launched.append(self))
    code = main(
        ["tui", "--token", _SECRET, "--event-log", str(tmp_path / "e.ndjson")], env=_env()
    )
    assert code == _OK
    assert len(launched) == 1
    # boundary-exact: the read model is the assembled cockpit, never ``None``.
    assert launched[0]._read_model is not None
    assert isinstance(launched[0]._read_model, CockpitApplication)


def test_tui_with_wrong_token_refuses_and_never_launches(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def _must_not_run(self: CockpitApp, *args: object, **kwargs: object) -> None:
        raise AssertionError("the TUI must not launch on a refused command")

    monkeypatch.setattr(CockpitApp, "run", _must_not_run)
    code = main(
        ["tui", "--token", "WRONG", "--event-log", str(tmp_path / "e.ndjson")], env=_env()
    )
    assert code >= _NONZERO_FLOOR
    captured = capsys.readouterr()
    assert captured.out == ""  # no cockpit data on a refused command
    assert "WRONG" not in captured.err  # token never echoed


def test_tui_without_secret_configured_refuses_and_never_launches(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def _must_not_run(self: CockpitApp, *args: object, **kwargs: object) -> None:
        raise AssertionError("the TUI must not launch when no secret is configured")

    monkeypatch.setattr(CockpitApp, "run", _must_not_run)
    code = main(
        ["tui", "--token", _SECRET, "--event-log", str(tmp_path / "e.ndjson")], env=_env(None)
    )
    assert code >= _NONZERO_FLOOR


def test_build_tui_app_wires_the_read_model(tmp_path: Path) -> None:
    cfg = CockpitConfig(event_log_path=tmp_path / "e.ndjson", currency="USD")
    app_model = assemble_cockpit(cfg, clock=FrozenClock(datetime(2026, 6, 19, tzinfo=UTC)))
    tui_app = build_tui_app(app_model)
    assert isinstance(tui_app, CockpitApp)
    assert tui_app._read_model is app_model  # the injected read model is the assembled cockpit


async def test_build_tui_app_drives_real_composition_under_pilot(tmp_path: Path) -> None:
    cfg = CockpitConfig(event_log_path=tmp_path / "e.ndjson", currency="USD")
    app_model = assemble_cockpit(cfg, clock=FrozenClock(datetime(2026, 6, 19, tzinfo=UTC)))
    tui_app = build_tui_app(app_model)
    async with tui_app.run_test() as pilot:
        await pilot.pause()
        # The real in-memory composition has a single founded root role -> org panel populated.
        from autofirm.cockpit.tui.org_snapshot_panel import OrgSnapshotPanel

        assert tui_app.query_one(OrgSnapshotPanel).state == "populated"
