# Operator Cockpit — screenshots

Real, populated PNG captures of the AutoFirm operator cockpit (`python -m autofirm.cockpit`)
running with genuine, real-shaped data. Nothing here is a hand-drawn mockup: every frame is
produced by driving the actual `CockpitApp` Textual TUI / real CLI through the on-main
composition root, seeded through the genuine domain contracts.

## Shots

| File | Surface | State shown |
| --- | --- | --- |
| `01-cockpit-operating-healthy.png` | TUI (2×2 panel grid) | Healthy operating run — 8-role org tree, $413.00 spend across 5 models, budget band `WARN_80`, verified ledger, 5 front-door requests (incl. a `dead_lettered` incident kept visible), 4 recorded audit events. |
| `02-cockpit-budget-breach-crit.png` | TUI (2×2 panel grid) | Budget-breach run — extra spend pushes the total to $494.05 of the $500 budget, classifying the band as `CRIT_95`. Same org / front-door / audit context. |
| `03-cockpit-cli-replay-and-auth.png` | CLI (real stdout/stderr) | `version`, authenticated `run` snapshot (kill-switch line, spend, budget band, ledger-verify), `replay` of the real append-only event log, and a **fail-closed** `run --token 'wrong'` that is refused. |

## How the data was sourced (exact mechanism)

`scripts/capture_cockpit_screenshots.py` assembles the **real** `CockpitApplication` via
`autofirm.cockpit.composition.cockpit_composer.assemble_cockpit(...)`, injecting a
`CockpitSources` bundle built from the genuine on-main domain objects through their real
contracts:

- **Org tree** — `DynamicOrg.found(...)` then `.hire(...)` (the real lifecycle engine), an
  8-role CEO→C-suite→leads hierarchy.
- **Spend** — `AppendOnlyCostLedger.seal_new(...)` + `.append(...)`, a real hash-chained
  cost ledger across Anthropic / OpenAI / Google models; the budget band is classified by the
  real spend adapter against a `$500` `CockpitConfig.budget`.
- **Front door** — `InMemoryFrontDoorProvenanceTrail.record(FrontDoorProvenanceEntry(...))`,
  real routing outcomes and delivery statuses (including a dead-lettered failure).
- **Kill-switch** — a real `KillSwitchEpoch` via `InMemoryKillSwitchSource`.
- **Audit events** — recorded through the real append-only `record_event(...)` writer.

All inputs are **synthetic, public-data-only** values flowing through the *same* contracts the
live platform uses (CLAUDE.md §3.12). The in-memory sources are the documented C4 swap seam:
when a live platform process is wired in, the same `CockpitSources` bundle is replaced behind
the identical interface, so these captures reflect the real rendering path.

## Capture mechanism

- **TUI** — the app is driven headlessly via Textual's `App.run_test()` Pilot, then
  `App.export_screenshot()` produces an SVG of the live screen, rasterised to PNG with
  `cairosvg` (the analysis-only extra). The rasteriser is re-pointed at the `Consolas`
  monospace font so box-drawing glyphs render cleanly.
- **CLI** — the real `autofirm.cockpit.transport.cockpit_cli.main(...)` is invoked and its
  true stdout/stderr captured, then rendered to PNG via Rich's SVG export.

> Note: Textual's *headless* SVG export does not paint docked-header content (a known
> limitation for `width:auto` children in a docked `Horizontal`), so the prominent
> kill-switch ARMED/TRIPPED badge that the running terminal shows in the header is instead
> evidenced via the CLI `run` snapshot's `kill-switch:` line in shot 03.

## Regenerate

```bash
PYTHONUTF8=1 PYTHONIOENCODING=utf-8 PYTHONPATH=src \
  python scripts/capture_cockpit_screenshots.py
```
