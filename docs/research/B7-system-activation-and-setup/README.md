# B7 — System Activation & Flawless One-Command Setup — Research Library

> **Mandate (user, 2026-06-19).** Platform setup must be **flawlessly simple (one command)** AND must
> **ACTIVATE** the whole system so it runs as **ONE cohesive platform**, not a collection of fragmented
> packages. Today the codebase *feels fragmented*: every package under `src/autofirm/` is a clean,
> dependency-injection-ready building block, but **nothing assembles them** — there is no composition
> root, no CLI entrypoint, and no `[project.scripts]`. B7 researches the full method space for
> "one command sets up AND activates a whole multi-package system", then a separate design
> (`docs/architecture/system-activation-design.md`) turns it into the AutoFirm runtime.

**Builds on, does not duplicate, B3.** `docs/research/B3-resilient-bootstrap/` already owns the
*idempotent / crash-resume / degraded-mode* substrate (Burgess convergence, K8s reconcile, ARIES redo,
Pillai atomic-rename, Nygard/SRE degradation, 12-Factor, Scripts-to-Rule-Them-All). B7 sits **on top**:
it adds the **composition / activation / supervision / readiness / CLI** layer that turns B3's converged
environment into a *running, self-tested, cohesive* platform. Where B3 answers *"is the environment in the
desired state?"*, B7 answers *"is the whole system wired together and actually live?"*. Cross-links are
called out per folder; no source or principle is repeated from B3.

Institution-grade bar; research gates building (CLAUDE.md §2 CRO, §3.3, §4.6). One folder per source.

## Sources (one folder per source — §4.6)

| Folder | Source | One-line takeaway |
|--------|--------|-------------------|
| `01-seemann-composition-root` | Seemann & van Deursen — *Dependency Injection P,P&P* (Manning 2019); ploeh blog "Composition Root" (2011) | **One** location, near the entry point, composes the entire object graph — the cure for fragmentation. |
| `02-flask-application-factory` | Flask docs — *Application Factories* (`create_app`) | A **factory function** builds & wires the app object; deferred `init_app()` lets extensions bind at assembly time, not import time. |
| `03-procfile-foreman-supervision` | Dollar — Foreman / Procfile (2011); honcho (Python); supervisord; 12-Factor IX (disposability) | **Declare process types once**; one supervisor **starts them and keeps them up**; "activate" = processes actually running. |
| `04-kubernetes-readiness-probes` | Kubernetes docs — *Liveness, Readiness, Startup Probes* | **Readiness ≠ started**: a post-activation probe proves each component is *actually able to serve*, not merely constructed. |
| `05-scripts-to-rule-them-all-dx` | GitHub Eng — *Scripts to Rule Them All* (2015); 12-Factor (I, V, X) | A **normalized, idempotent, single command** that works on fresh clone AND re-run is what makes setup *feel flawless*. |
| `06-typer-click-cli-ergonomics` | Typer (Ramírez) docs; Click docs | **One discoverable entrypoint** with typed subcommands (`up`/`status`/`doctor`/`down`) + auto `--help` = ergonomic activation surface. |

## How B7 maps onto AutoFirm
- `01` → the **composition root** module (proposed `src/autofirm/runtime/platform_composition_root.py`) that constructs and wires *every* package once.
- `02` → that root is a **factory** (`build_platform(config) -> Platform`) with deferred binding so a missing key degrades one capability, not the assembly.
- `03` → a tiny **in-process supervisor** starts the long-lived loops (heartbeats, comms bus, operate loop) and keeps them up — no external Procfile runner needed for a Python-only system.
- `04` → a **post-activation self-test** (readiness probe set) proves the wired system is live end-to-end.
- `05` → the single `autofirm up` command, idempotent and OS-portable (Windows AND Linux), is the DX bar.
- `06` → Typer gives the discoverable `up / status / doctor / down` subcommand surface with zero hand-rolled arg parsing.

## Faithfulness status (CRO gate)
Every folder cites the primary/authoritative source (title, author/org, year, link) and reproduces the
source's own wording for load-bearing definitions (Seemann's "single Composition Root", K8s readiness
"ready to accept traffic", Procfile `name: command` grammar). "Best parts to take" notes are AutoFirm-specific
and clearly separated from the faithful summary. No overclaims; cross-links to B3 prevent duplication.
