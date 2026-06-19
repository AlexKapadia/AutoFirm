# CLI Ergonomics for a Single Entrypoint — Typer & Click

## Citation (exact)
- Typer (Sebastian Ramirez / FastAPI org), documentation & repo.
  https://typer.tiangolo.com/  ·  https://github.com/fastapi/typer
  Subcommands: https://typer.tiangolo.com/tutorial/subcommands/
- Click (Pallets Projects), documentation. https://click.palletsprojects.com/
  (Typer is built on Click.)

## Faithful summary
Typer is a library for building command-line interfaces from Python type hints, created by Sebastian Ramirez
(author of FastAPI), built on top of Click.

Faithful points:
- Type-hint driven, minimal boilerplate. Function parameters + type hints become CLI arguments/options; the
  parser, validation, and help text are generated automatically. "Easy to code. Based on Python type hints."
- Subcommands / command groups. Typer supports subcommands (command groups, including nested), so one
  program exposes multiple discoverable verbs under a single entrypoint (e.g. app up, app status). This is
  the multi-command structure Click provides via @click.group / @click.command.
- Automatic --help and shell completion. Users get automatic --help for the app and every subcommand, plus
  auto-completion in Bash, Zsh, Fish, and PowerShell. Discoverability is built in, not hand-written.
- Editor support. Because commands are typed Python functions, editors give completion and type-checks; the
  CLI definition is statically checkable (works with mypy --strict).

Click (the foundation) provides: command/group composition, parameter parsing, prompts, context objects for
sharing state between a group and its subcommands, and clean error/exit-code handling.

## Best parts to take -> AutoFirm
- One discoverable entrypoint with typed subcommands — exactly the up / status / doctor / down surface the
  mandate wants. Define a single Typer app exposed via pyproject [project.scripts] as `autofirm = ...`, with:
    autofirm up      — converge (B3) + build (composition root) + supervise + self-test; the one command.
    autofirm status  — re-run readiness probes (folder 04) + show each capability/loop state (live/degraded/open).
    autofirm doctor  — B3 read-only check() of every bootstrap step; no apply(); exit non-zero on FAILED.
    autofirm down    — graceful cooperative shutdown of all supervised loops (12-Factor IX disposability).
- Auto --help + completion = ergonomics for free. Satisfies "flawlessly simple": a newcomer runs
  `autofirm --help`, sees four self-documenting verbs, and needs no README to start. PowerShell completion
  matters because the substrate is Windows-first.
- mypy --strict friendliness. AutoFirm enforces mypy --strict (Makefile gate types). Typer/Click command
  functions are ordinary typed functions, so the CLI lives inside the existing type gate with no exceptions.
- Pick Typer over argparse/hand-rolled. argparse would re-introduce boilerplate and weaker discoverability;
  Typer/Click give grouped subcommands, context-passing (share the built Platform between subcommands), and
  consistent exit codes (needed for the up/doctor exit-code contract) with the least code. Click is the only
  new runtime-adjacent dep; it is a CLI-edge dependency, not engine code, so it does not violate the
  deterministic-core minimalism (it lives only in the runtime/cli entry module).

## Cross-link (no duplication)
This is the user-facing surface for the machinery in 01-05 and B3. It introduces no new mechanics; it only
makes the single entrypoint discoverable and typed. The exit-code semantics reuse B3 doctor contract and
folder-04 readiness criticality.
