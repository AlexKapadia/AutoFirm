"""The cockpit command-line entry surface: ``version`` / ``run`` / ``replay`` / ``tui``.

What this does
--------------
Defines :func:`main`, the argparse-driven CLI behind ``python -m autofirm.cockpit``. Four
subcommands: ``version`` prints the cockpit version and exits 0 with NO auth (it leaks nothing);
``run`` authenticates the operator, assembles the cockpit, and prints a read-only status
snapshot; ``replay`` authenticates and prints the recorded event log (read through composition,
never the event-log module directly); ``tui`` authenticates and launches the read-only Textual
cockpit (assembled identically to ``run``). The presented operator token arrives via ``--token``
and is compared against the configured secret by the fail-closed
:mod:`~autofirm.cockpit.transport.operator_auth_gate`. An unknown or missing subcommand, or a
failed authentication, returns a NON-ZERO exit and emits no cockpit data (deny by default).

Why it exists / where it sits
-----------------------------
This is the cockpit's launch path. It wires the user's intent to the composition root and the
auth gate, and it is the only transport module that turns an :class:`AuthError` into a process
exit code. Sits in the transport layer — it imports only the composition root, the pure version
helper, and the auth gate (never an adapter, the event log, or an on-main domain package).

Security / compliance invariants upheld
---------------------------------------
* **Deny by default (CLAUDE.md §5.6):** missing/unknown subcommands and every auth failure
  return non-zero; ``run``/``replay`` emit cockpit data ONLY after authentication succeeds.
* **No secret in output (§5.6):** the auth gate never carries a token in its error, and the CLI
  prints only a generic refusal to stderr — a token is never echoed.
* **Read-only commands:** ``run`` and ``replay`` only read snapshots / replay the log; neither
  mutates on-main state.
"""

from __future__ import annotations

import argparse
import os
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path

from autofirm.cockpit.composition.cockpit_composer import assemble_cockpit
from autofirm.cockpit.composition.cockpit_config import CockpitConfig
from autofirm.cockpit.core.cockpit_version import cockpit_version
from autofirm.cockpit.transport.operator_auth_gate import AuthError, authenticate_operator
from autofirm.cockpit.tui.cockpit_app import CockpitApp
from autofirm.cockpit.tui.cockpit_read_model_protocol import CockpitReadModel

__all__ = ["build_tui_app", "main"]

# Process exit codes. 0 is success; every refusal/usage error is a distinct non-zero so a
# caller (or test) can assert exactly which deny-by-default path fired.
_EXIT_OK = 0
_EXIT_AUTH_REFUSED = 2
_EXIT_USAGE = 2

_DEFAULT_EVENT_LOG = "cockpit-events.ndjson"
_DEFAULT_CURRENCY = "USD"


def main(argv: Sequence[str] | None = None, *, env: Mapping[str, str] | None = None) -> int:
    """Run the cockpit CLI and return a process exit code (0 ok, non-zero on refusal/usage).

    Args:
        argv: The argument vector (without the program name); ``None`` uses ``sys.argv[1:]``.
        env: The environment to authenticate against; ``None`` reads the live ``os.environ``
            (the auth gate itself never reads the environment directly).

    Returns:
        ``0`` on success; a non-zero code on a usage error, an unknown/missing subcommand, or
        a failed authentication.
    """
    _force_utf8_stdout()  # Windows cp1252 safety: printing must never be the thing that fails
    resolved_env = _resolve_env(env)
    parser = _build_parser()
    try:
        args = parser.parse_args(None if argv is None else list(argv))
    except SystemExit as exc:  # argparse exits on bad args / -h; convert to a return code
        return _exit_code_of(exc)

    if args.command == "version":
        print(cockpit_version())
        return _EXIT_OK
    if args.command == "run":
        return _run(args.token, event_log=args.event_log, currency=args.currency, env=resolved_env)
    if args.command == "replay":
        return _replay(
            args.token, event_log=args.event_log, currency=args.currency, env=resolved_env
        )
    if args.command == "tui":
        return _tui(args.token, event_log=args.event_log, currency=args.currency, env=resolved_env)
    # deny by default: no subcommand given (argparse rejects unknown ones before this).
    print("no subcommand given; expected one of: version, run, replay, tui", file=sys.stderr)
    return _EXIT_USAGE


def _run(token: str | None, *, event_log: str, currency: str, env: Mapping[str, str]) -> int:
    """Authenticate, assemble the cockpit, and print a read-only status snapshot."""
    if (refusal := _authenticate(token, env=env)) is not None:
        return refusal
    app = assemble_cockpit(_config(event_log, currency))
    org = app.org_snapshot()
    spend = app.spend_snapshot()
    epoch = app.kill_switch_epoch()
    activity = app.front_door_activity()
    band_name = "none" if spend.band is None else spend.band.name
    print(f"cockpit ready (version {cockpit_version()})")
    print(f"roles: {org.total_role_count}")
    print(f"front-door entries: {len(activity.entries)}")
    print(f"spend total: {spend.grand_total.amount} {spend.grand_total.currency}")
    print(f"budget band: {band_name}")
    print(f"ledger verified: {spend.ledger_verified}")
    print(f"kill-switch: version={epoch.version} tripped={epoch.tripped}")
    return _EXIT_OK


def _replay(token: str | None, *, event_log: str, currency: str, env: Mapping[str, str]) -> int:
    """Authenticate, then print every recorded cockpit event (replayed via composition)."""
    if (refusal := _authenticate(token, env=env)) is not None:
        return refusal
    app = assemble_cockpit(_config(event_log, currency))
    events = app.recorded_events()
    print(f"events: {len(events)}")
    for event in events:
        print(f"{event.seq} {event.kind.value} {event.source}")
    return _EXIT_OK


def _tui(token: str | None, *, event_log: str, currency: str, env: Mapping[str, str]) -> int:
    """Authenticate, assemble the cockpit, and launch the read-only Textual TUI.

    The cockpit is assembled identically to ``run`` (same auth gate, same composition root);
    only the presentation differs. Construction is kept separate from the blocking ``.run()``
    (via :func:`build_tui_app`) so a test can verify the wiring without a real terminal.
    """
    if (refusal := _authenticate(token, env=env)) is not None:
        return refusal
    app = assemble_cockpit(_config(event_log, currency))
    tui_app = build_tui_app(app)
    tui_app.run()  # pragma: no cover, pragma: no mutate - blocking; needs a real terminal
    return _EXIT_OK


def build_tui_app(read_model: CockpitReadModel) -> CockpitApp:
    """Construct the cockpit TUI app around an assembled read model (no ``.run()`` here).

    Separated from :func:`_tui` so a Pilot test can build the app and drive it headlessly,
    while the blocking ``.run()`` (which requires a real terminal) stays out of the test path.

    Args:
        read_model: The assembled, read-only :class:`CockpitApplication` (or any value of the
            same read shape) the TUI panels render.

    Returns:
        A constructed :class:`CockpitApp`, not yet running.
    """
    return CockpitApp(read_model)


def _authenticate(token: str | None, *, env: Mapping[str, str]) -> int | None:
    """Return ``None`` if authenticated, else the auth-refused exit code (emitting no data).

    The refusal message is generic — the auth gate never carries a token, so nothing secret
    can reach stderr here (fail-closed, §5.6).
    """
    try:
        authenticate_operator(token, env=env)
    except AuthError as exc:
        print(f"authentication refused: {exc}", file=sys.stderr)
        return _EXIT_AUTH_REFUSED
    return None


def _config(event_log: str, currency: str) -> CockpitConfig:
    """Build the cockpit config from the CLI's event-log path and currency."""
    return CockpitConfig(event_log_path=Path(event_log), currency=currency)


def _build_parser() -> argparse.ArgumentParser:
    """Build the argparse parser with the ``version`` / ``run`` / ``replay`` subcommands."""
    parser = argparse.ArgumentParser(
        prog="autofirm-cockpit",
        description="AutoFirm operator cockpit — read-only control surface.",
    )
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("version", help="print the cockpit version (no auth required)")
    _auth_gated = (
        ("run", "assemble and show a status snapshot"),
        ("replay", "replay the event log"),
        ("tui", "launch the read-only Textual cockpit"),
    )
    for name, summary in _auth_gated:
        command = sub.add_parser(name, help=summary)
        command.add_argument("--token", default=None, help="the presented operator token")
        command.add_argument(
            "--event-log", dest="event_log", default=_DEFAULT_EVENT_LOG, help="event-log path"
        )
        command.add_argument(
            "--currency", default=_DEFAULT_CURRENCY, help="ISO-4217 spend currency (upper-case)"
        )
    return parser


def _resolve_env(env: Mapping[str, str] | None) -> Mapping[str, str]:
    """Resolve the environment to authenticate against (the live process env when ``None``)."""
    return os.environ if env is None else env


def _exit_code_of(exc: SystemExit) -> int:
    """Map an argparse :class:`SystemExit` to an int return code (0 for help, else usage)."""
    code = exc.code
    if code is None:
        return _EXIT_OK
    return code if isinstance(code, int) else _EXIT_USAGE


def _force_utf8_stdout() -> None:
    """Reconfigure stdout to UTF-8 so a status line never crashes a cp1252 Windows console."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
