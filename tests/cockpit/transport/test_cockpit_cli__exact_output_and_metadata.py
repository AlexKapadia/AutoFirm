"""cockpit_cli: byte-exact output, exact exit codes, and exact argparse metadata.

These tests pin the CLI's observable surface BYTE-FOR-BYTE (full stdout/stderr equality, exact
exit-code integers, exact help/prog/description text). Substring/`in` assertions let a mutmut
string-wrap mutant (``"foo"`` -> ``"XXfooXX"``) survive because the substring is still present;
equality kills every such literal mutant, and asserting the LITERAL exit-code integer (not the
module constant, which a mutant moves on both sides at once) kills the exit-code mutants.
"""

from __future__ import annotations

import argparse
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


def _env(value: str | None = _SECRET) -> Mapping[str, str]:
    return {} if value is None else {OPERATOR_TOKEN_ENV_VAR: value}


# --------------------------- exact exit-code integers --------------------------- #
# Assert the LITERAL 2 (not _EXIT_* — a constant mutant moves the constant AND the return value
# together, so comparing to the constant would not catch it). Real contract: refusal/usage == 2.


def test_auth_refused_exit_code_is_exactly_two(tmp_path: Path) -> None:
    code = main(["run", "--token", "WRONG", "--event-log", str(tmp_path / "e.ndjson")], env=_env())
    assert code == 2  # kills _EXIT_AUTH_REFUSED -> 3


def test_no_subcommand_exit_code_is_exactly_two() -> None:
    assert main([], env=_env()) == 2  # kills _EXIT_USAGE -> 3


# --------------------------- module default constants --------------------------- #


def test_default_event_log_constant_is_exact() -> None:
    # kills both _DEFAULT_EVENT_LOG -> "XX..XX" and -> None (pinned byte-for-byte).
    assert cockpit_cli._DEFAULT_EVENT_LOG == "cockpit-events.ndjson"


def test_default_currency_constant_is_exact() -> None:
    assert cockpit_cli._DEFAULT_CURRENCY == "USD"


# --------------------------- byte-exact `run` stdout --------------------------- #
# The CLI `run` uses the default in-memory cockpit (1 root role, empty trail/ledger, no budget,
# untripped v0 kill-switch), so its output is fully deterministic. Pin EVERY line exactly: this
# kills every f-string literal mutant on lines 98-106 (band "none", labels, totals) at once.


def test_run_stdout_is_byte_exact(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    code = main(
        ["run", "--token", _SECRET, "--event-log", str(tmp_path / "e.ndjson")], env=_env()
    )
    assert code == 0
    expected = (
        f"cockpit ready (version {cockpit_version()})\n"
        "roles: 1\n"
        "front-door entries: 0\n"
        "spend total: 0 USD\n"
        "budget band: none\n"
        "ledger verified: True\n"
        "kill-switch: version=0 tripped=False\n"
    )
    assert capsys.readouterr().out == expected


# --------------------------- byte-exact `replay` stdout --------------------------- #


def _seed_log(path: Path) -> None:
    cfg = CockpitConfig(event_log_path=path, currency="USD")
    app = assemble_cockpit(cfg, clock=FrozenClock(datetime(2026, 6, 19, tzinfo=UTC)))
    app.record_event(CockpitEventKind.ORG_CHANGED, "seed", {"detail": "hired"})


def test_replay_stdout_is_byte_exact(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    log = tmp_path / "events.ndjson"
    _seed_log(log)
    code = main(["replay", "--token", _SECRET, "--event-log", str(log)], env=_env())
    assert code == 0
    # "events: <n>\n" then "<seq> <kind.value> <source>\n" — kills both replay f-string mutants.
    assert capsys.readouterr().out == "events: 1\n0 org_changed seed\n"


# --------------------------- byte-exact stderr (no-leak refusals) --------------------------- #


def test_no_subcommand_stderr_is_byte_exact(capsys: pytest.CaptureFixture[str]) -> None:
    main([], env=_env())
    assert capsys.readouterr().err == "no subcommand given; expected one of: version, run, replay\n"


def test_auth_refused_stderr_is_byte_exact(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    main(["run", "--token", "WRONG", "--event-log", str(tmp_path / "e.ndjson")], env=_env())
    # exact: "authentication refused: " prefix + the gate's exact mismatch message, no token.
    assert capsys.readouterr().err == "authentication refused: operator token did not match\n"


# --------------------------- exact argparse metadata --------------------------- #


def _subparsers_action(parser: argparse.ArgumentParser) -> argparse._SubParsersAction:  # type: ignore[type-arg]
    return next(a for a in parser._actions if isinstance(a, argparse._SubParsersAction))


def test_parser_prog_and_description_are_exact() -> None:
    parser = cockpit_cli._build_parser()
    assert parser.prog == "autofirm-cockpit"
    assert parser.description == "AutoFirm operator cockpit — read-only control surface."


def test_subcommand_help_text_is_exact() -> None:
    sub = _subparsers_action(cockpit_cli._build_parser())
    help_by_command = {c.dest: c.help for c in sub._choices_actions}
    assert help_by_command == {
        "version": "print the cockpit version (no auth required)",
        "run": "assemble and show a status snapshot",
        "replay": "replay the event log",
    }


@pytest.mark.parametrize("command", ["run", "replay"])
def test_auth_gated_argument_help_text_is_exact(command: str) -> None:
    sub = _subparsers_action(cockpit_cli._build_parser()).choices[command]
    help_by_option = {tuple(a.option_strings): a.help for a in sub._actions if a.option_strings}
    assert help_by_option[("--token",)] == "the presented operator token"
    assert help_by_option[("--event-log",)] == "event-log path"
    assert help_by_option[("--currency",)] == "ISO-4217 spend currency (upper-case)"
