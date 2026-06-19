"""CLI tests via Typer's CliRunner: up/status/doctor/down exit codes, no network, no real loops.

The Typer ``app`` is imported LAZILY through a fixture (never at module import) so that a
mutant which breaks ``cli_entrypoint`` import — e.g. ``app = None`` (the ``@app.command()``
decorators then raise) or the ``__name__ == "__main__"`` guard flipping so ``app()`` runs at
import — fails INSIDE a test (pytest reports an error, process exit 1 = killed) rather than at
collection (exit 2/3, which mutmut would misread as "survived"). See CLAUDE.md §3.6 / §7.2.
"""

from __future__ import annotations

import runpy
import sys
from typing import TYPE_CHECKING

import pytest
from typer.testing import CliRunner

if TYPE_CHECKING:
    import typer

_runner = CliRunner()


@pytest.fixture
def app() -> typer.Typer:
    """Import the Typer app at TEST time (not collection time) — see the module docstring."""
    from autofirm.runtime.cli_entrypoint import app as _app

    return _app


@pytest.fixture
def _keyed_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Set a synthetic provider key so the gateway capability binds live (no real network)."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-synthetic-test")


@pytest.fixture
def _keyless_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Remove any provider key so the gateway degrades (the never-hard-block path)."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)


def test_cli_up__healthy_env_exits_zero_and_reports_green(
    app: typer.Typer, _keyed_env: None
) -> None:
    """`autofirm up` on a healthy synthetic config exits 0 with a GREEN readiness summary."""
    result = _runner.invoke(app, ["up"])
    assert result.exit_code == 0
    assert "readiness=green" in result.stdout


def test_cli_up__missing_optional_key_still_exits_zero_degraded(
    app: typer.Typer, _keyless_env: None
) -> None:
    """`autofirm up` with a missing OPTIONAL key still succeeds (degraded) — never hard-blocks."""
    result = _runner.invoke(app, ["up"])
    assert result.exit_code == 0  # NEVER a whole-platform hard block on a missing optional dep
    assert "readiness=degraded" in result.stdout


def test_cli_status__exits_zero_and_lists_capabilities(
    app: typer.Typer, _keyed_env: None
) -> None:
    """`autofirm status` re-runs the probes and exits 0, reporting the capability count."""
    result = _runner.invoke(app, ["status"])
    assert result.exit_code == 0
    assert "capabilities=8" in result.stdout


def test_cli_doctor__empty_probe_reports_missing_and_exits_nonzero(app: typer.Typer) -> None:
    """`autofirm doctor` reports missing required steps from a bare probe and exits non-zero."""
    result = _runner.invoke(app, ["doctor"])
    assert result.exit_code == 1  # required steps missing -> fail-closed non-zero exit
    assert "missing=" in result.stdout


def test_cli_down__exits_zero_on_clean_drain(app: typer.Typer, _keyed_env: None) -> None:
    """`autofirm down` cooperatively drains the loops and exits 0."""
    result = _runner.invoke(app, ["down"])
    assert result.exit_code == 0
    assert "drained loops=" in result.stdout


def test_cli__no_args_shows_help_not_a_crash(app: typer.Typer) -> None:
    """Bare `autofirm` shows help (no_args_is_help) rather than erroring — discoverable DX."""
    result = _runner.invoke(app, [])
    # Typer maps no-args-is-help to a non-zero "usage shown" exit; the key property is it does
    # not crash and surfaces the four verbs.
    assert "up" in result.stdout
    assert "status" in result.stdout
    assert "doctor" in result.stdout
    assert "down" in result.stdout


# ---------------------------------------------------------------------------
# Mutation-hardening (CLAUDE.md §3.6): pin the app help/completion config and
# prove the module imports cleanly (no ``app()`` at import) and is wired as a Typer app.
# ---------------------------------------------------------------------------


def test_cli_app__is_a_wired_typer_app(app: typer.Typer) -> None:
    """The module exposes a real, wired Typer app (kills the ``app = None`` mutant).

    The lazy ``app`` fixture imports ``cli_entrypoint`` at test time; a mutant collapsing the
    ``typer.Typer(...)`` construction to ``None`` makes the ``@app.command()`` decorators raise
    on import — surfacing here as a test error (exit 1 = killed) rather than a collection error.
    """
    import typer as _typer

    assert isinstance(app, _typer.Typer)
    command_names = {cmd.callback.__name__ for cmd in app.registered_commands}
    assert command_names == {"up", "status", "doctor", "down"}


def test_cli_app__help_text_is_the_exact_one_line_pitch(app: typer.Typer) -> None:
    """The app's help is the exact self-documenting one-liner (kills the string-wrap mutant).

    A wrapping mutant would prefix the help with sentinels, so anchoring on the real start/end
    (rather than a loose substring) catches it.
    """
    assert app.info.help is not None
    assert app.info.help.startswith("AutoFirm ")
    assert app.info.help.endswith("activate the whole platform with one command.")


def test_cli_app__shell_completion_is_enabled(app: typer.Typer) -> None:
    """Shell completion is wired on the app (kills the ``add_completion=False`` mutant).

    Asserted on the app's own config rather than via ``--show-completion`` (whose exit code is
    shell-environment dependent and therefore non-deterministic under a CI subprocess).
    """
    assert app._add_completion is True


def test_cli__importing_module_does_not_invoke_the_app(app: typer.Typer) -> None:
    """Importing the module must NOT run ``app()`` (kills the ``__name__`` guard mutants).

    The ``app`` fixture imports ``cli_entrypoint`` at test time. A mutant flipping the guard to
    ``__name__ != "__main__"`` (or wrapping the ``"__main__"`` literal) would call ``app()`` on
    that import, raising ``SystemExit`` during fixture setup (exit 1 = killed). Reaching this
    assertion proves the import was side-effect-free and the guard is intact.
    """
    assert app.info.help is not None  # import completed without the app() entry point firing


def test_cli__module_run_as_main_invokes_the_app(monkeypatch: pytest.MonkeyPatch) -> None:
    """Executing the module as ``__main__`` runs the Typer app (kills the entry-guard mutants).

    Run with no subcommand, ``no_args_is_help`` makes the app exit via ``SystemExit``. A mutant
    flipping the guard to ``!=`` or wrapping the ``"__main__"`` literal would NOT invoke ``app()``
    when run as ``__main__`` — so no ``SystemExit`` is raised and this test fails (exit 1 = killed).
    """
    monkeypatch.setattr(sys, "argv", ["autofirm"])
    with pytest.raises(SystemExit):
        runpy.run_module("autofirm.runtime.cli_entrypoint", run_name="__main__")
