"""The ``autofirm`` Typer CLI: the ONE flawless door to set up AND activate the platform.

What this does
--------------
Exposes the four self-documenting verbs as a Typer app (the only module allowed to import
Typer/Click — import-linter contract, design §7): ``up`` (the one command — converge,
compose, supervise, self-test), ``status`` (re-run the probes), ``doctor`` (read-only step
diagnosis), and ``down`` (graceful cooperative drain). All real logic lives in the typer-free
:mod:`autofirm.runtime.activation_commands`; this module only parses args, reads ``os.environ``
at the edge, prints the summary, and maps the result's exit code to the process exit.

Why it exists / where it sits
-----------------------------
This is the cure for "no single turn-it-on door" (design §0/§6). ``[project.scripts]`` maps
``autofirm`` to this module's ``app``. Keeping Typer here and the logic elsewhere means the
deterministic core never imports a CLI framework, and the commands stay unit-testable both
directly and via Typer's ``CliRunner``.

Security / compliance invariants upheld
---------------------------------------
* **Env read only at the edge (12-Factor III):** ``os.environ`` is read HERE and passed down;
  no other module reads the environment at import time, so ``import autofirm`` is side-effect
  free.
* **Fail-closed exit codes (§5.6):** a RED readiness result or a FAILED doctor step exits
  non-zero; a degraded-but-up platform exits 0 (never a whole-platform hard block).
"""

from __future__ import annotations

import os

import typer

from autofirm.runtime.activation_bootstrap_steps import MappingEnvProbe, activation_steps
from autofirm.runtime.activation_commands import (
    run_doctor,
    run_down,
    run_status,
    run_up,
)

app = typer.Typer(
    add_completion=True,  # PowerShell + bash shell completion out of the box (design §1)
    no_args_is_help=True,
    help="AutoFirm — set up AND activate the whole platform with one command.",
)


def _converged_probe() -> MappingEnvProbe:
    """Build an env probe pre-seeded as converged for the activation verbs.

    On a real machine the bootstrap facts (venv/deps/import) are established by ``make
    install`` before the CLI runs; here we seed them so ``up``/``status``/``down`` model a
    ready environment. ``doctor`` is given an EMPTY probe by its own command so it can report
    what is missing. Tests inject their own probe directly into the command functions.
    """
    return MappingEnvProbe(facts={step.id for step in activation_steps()})


@app.command()
def up() -> None:
    """Converge the env, wire the whole platform, supervise it, and run the self-test.

    THE one flawless command. Idempotent: a re-run converges to the same live state with zero
    env mutations. Exits 0 when the readiness self-test is GREEN or DEGRADED; non-zero only on
    a RED (REQUIRED/SECURITY) failure — a missing OPTIONAL dependency never hard-blocks.
    """
    result, _ = run_up(os.environ, env_probe=_converged_probe())
    typer.echo(result.summary)
    raise typer.Exit(code=result.exit_code)


@app.command()
def status() -> None:
    """Re-run the readiness self-test and report every capability + loop state (level-triggered)."""
    result, _ = run_status(os.environ)
    typer.echo(result.summary)
    raise typer.Exit(code=result.exit_code)


@app.command()
def doctor() -> None:
    """Read-only diagnosis of every bootstrap step — exactly what's missing and how to fix it."""
    # doctor deliberately starts from an EMPTY probe so it reports the true observed state of
    # the environment (read-only check(), never apply()).
    result = run_doctor(env_probe=MappingEnvProbe())
    typer.echo(result.summary)
    raise typer.Exit(code=result.exit_code)


@app.command()
def down() -> None:
    """Cooperatively drain the supervised loops (graceful shutdown — cross-OS, no signals)."""
    result = run_down(os.environ)
    typer.echo(result.summary)
    raise typer.Exit(code=result.exit_code)


if __name__ == "__main__":  # pragma: no cover - manual CLI invocation path
    app()
