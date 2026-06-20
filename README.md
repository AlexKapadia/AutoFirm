<h1 align="center">AutoFirm</h1>

<p align="center">
  <strong>AutoFirm autonomously <em>builds</em> and <em>operates</em> real companies end-to-end —
  as a self-organising company of AI agents.</strong>
</p>

<p align="center">
  You give it an idea. It stands up the org, hires the roles, wires the
  communication, runs the finances, makes the pricing and runway calls, senses the
  market, routes the owner's questions, and produces investor-ready artifacts —
  every decision audited, deterministic, and explainable.
</p>

<p align="center">
  <img alt="tests" src="https://img.shields.io/badge/tests-1%2C331%20passing-111111">
  <img alt="coverage" src="https://img.shields.io/badge/coverage-99.6%25-111111">
  <img alt="e2e" src="https://img.shields.io/badge/e2e-60%2F60%20checks-111111">
  <img alt="license" src="https://img.shields.io/badge/license-MIT-blue">
</p>

---

## Proven, not promised

AutoFirm has been validated end-to-end by **building and then operating four
genuinely different companies** — a B2B SaaS firm, an industrial manufacturer, a
direct-to-consumer retailer, and a renewable-energy utility — entirely from
**public-data-only** figures. For each one the platform exercises **15 distinct
capabilities** and asserts the **real output** of every one. All four companies
came back fully green: **60 / 60 feature checks correct.**

![End-to-end validation — 15 features × 4 public companies](evidence/graphs/e2e_pass_matrix.png)

The numbers behind the badge:

| Evidence | Result |
| --- | --- |
| Automated tests (all passing) | **1,331** |
| Total line coverage (branch mode) | **99.64%** across 18 packages |
| Companies built **and** operated | **4** (SaaS · manufacturing · retail · energy) |
| Feature checks asserted correct | **60 / 60** (15 capabilities × 4 companies) |
| Build+operate reproducibility | **byte-for-byte deterministic** (5 runs → 1 hash) |

Coverage is high **and uniform** — not propped up by any single package:

![Per-package test coverage](evidence/graphs/coverage_by_package.png)

These aren't toy runs. The finance engine articulates three tying statements and a
DCF valuation for each company — real, company-shaped outputs across four very
different business models:

![Operate-phase financials for four public companies](evidence/graphs/company_financials.png)

> Full statistics, the complete per-package table, and the determinism proof live
> in **[`evidence/stats/statistical_evidence.md`](evidence/stats/statistical_evidence.md)**.
> Every figure regenerates from real runs via `python evidence/generators/run_all.py`.

## What AutoFirm does

You give AutoFirm an idea; it does the unglamorous, end-to-end work of turning that
idea into a real, operating company — and it does it as a **company of AI agents**
that behaves like a real org:

- **Builds the company.** Founds the org hierarchy, **detects capability gaps and
  auto-creates + hires** the missing roles, wires an audited inter-agent message
  bus, and files every deliverable into a catalogued document store.
- **Operates the company.** Runs **accurate finance** (three tying statements, DCF
  valuation, zero numerical errors), makes **explainable pricing and runway
  decisions**, senses the market and issues **green-light go/no-go verdicts**,
  **routes the owner's questions** to the right team, and generates
  **investor-ready artifacts** (xlsx / pptx / docx).
- **Self-organises.** A strict, audited hierarchy of agents that can be **hired,
  fired, and re-scoped** as the company's needs change — every manager owns the
  charter of its reports; new niche roles are created when gaps appear.
- **Runs autonomously.** Orchestrated **Claude Code CLI sessions** hand off cleanly
  when context runs out and **auto-resume**, so a company can run for days
  unattended — fully logged, append-only, and traceable.

## How it's built — the architecture

Eighteen platform packages, laid out in flow order: a **deterministic, audited
foundation**, the **agent execution substrate**, the **org + communication
fabric**, the **business-capability engines**, and the **end-to-end validation**
that exercises them all on real companies.

![AutoFirm whole-system architecture](evidence/diagrams/system_architecture.png)

Every company is built and operated inside its **own isolated, deletable
workspace**, then emits a structured, machine-readable result with **every feature
asserted** — the per-company flow:

![Build & operate one company](evidence/diagrams/build_operate_flow.png)

| Layer | Packages | Responsibility |
| --- | --- | --- |
| Foundation | `foundation` · `audit` | exact money/determinism primitives; append-only audit log |
| Execution | `substrate` · `orchestration` | Claude CLI sessions; saga / compensation control loops |
| Fabric | `org` · `comms` · `memory` · `access` | dynamic org; audited bus; versioned recall; least-privilege RBAC |
| Engines | `finance` · `decisions` · `market_intel` · `frontdoor` · `artifacts` · `design_product` · `document_store` · `heartbeat` · `flow` | the business capabilities |
| Validation | `e2e` | build + operate the four public companies, assert every output |

## The human-facing output-review gate

Anything an AI org sends to a human — a board deck, a model, a P&L — is only as
trustworthy as the last check between the agent and the reader. AutoFirm puts an
**independent, fail-closed gate** at that seam: **nothing reaches a human until a
floor of deterministic checks all pass.** Seven mechanical reviewers run on every
artifact — **accounting identity** (assets = liabilities + equity), **spec
round-trip**, **numeric recompute**, **file-opens-clean** (the OOXML actually
opens), **FAST lint** (formula/orphan/consistency), **IBCS** notation, and
**visual integrity** (no truncated axes, overlap, or clipping). Their outcome is a
single `ReviewVerdict` whose `passed` field is **derived** from the findings rather
than set — so a "green but wrong" verdict is structurally unconstructible. A failed
artifact enters a **bounded correction loop**, and **release authority is
load-bearing**: the librarian delivery seam refuses to hand anything to a human
without a passing verdict.

![Why the gate exists](evidence/output_review/graphs/escape_vs_human_baseline.png)

An un-reviewed human spreadsheet carries an error a large fraction of the time; the
independent gate's **measured escape rate is 0**. Against the labelled golden set the
gate scores **100% detection on every must-block defect class** (MECHANICAL /
PURE_LOGIC / OMISSION), **0 / 14 escapes** of planted defects, and **0 / 4 false
positives** on known-good controls. It is **deterministic over 3,600 repeated
reviews** (one unique verdict digest), holds **100% line and branch coverage**, and
is mutation-proven to **0 surviving mutants across 25 modules**.

> Full methodology, statistics, and per-defect outcomes live in
> **[`evidence/output_review/README.md`](evidence/output_review/README.md)**.

## The operator cockpit

The **operator cockpit** ([`src/autofirm/cockpit/`](src/autofirm/cockpit/)) is a
founder-facing, terminal-first, **read-only** control plane for watching a running
AutoFirm org. It is an **add-only consumer**: a single read-only adapter seam binds
the platform's on-main subsystems — front-door activity, the org snapshot, cost-ledger
spend, and the kill-switch epoch — and the cockpit only ever *observes* them, never
mutating on-main state. It is layered low→high (`core` pure decision logic → `eventlog`
append-only NDJSON → `adapters` → `readmodels` → `composition` DI root → `transport`
CLI + auth gate → `tui` Textual widgets), and is import-contract-fenced so the adapters
remain the only seam onto on-main.

Install the cockpit's optional runtime deps (`textual`, `rich` — MIT-licensed, kept out
of the deterministic runtime closure):

```bash
pip install -e ".[cockpit]"
```

There is no console script; the entry point is `python -m autofirm.cockpit <subcommand>`:

```bash
# Print the cockpit version (no auth, leaks nothing).
python -m autofirm.cockpit version

# Auth-gated commands. The EXPECTED secret is read from the environment;
# the operator PRESENTS a token via --token. Use a real secret, not this placeholder.
export AUTOFIRM_COCKPIT_TOKEN=<operator-secret>

# Assemble the cockpit and print a read-only status snapshot.
python -m autofirm.cockpit run     --token <operator-secret>

# Replay the recorded cockpit events from the event log.
python -m autofirm.cockpit replay  --token <operator-secret>

# Launch the read-only Textual TUI (live org / spend / front-door / kill-switch /
# event-log panels, ~2s refresh).
AUTOFIRM_COCKPIT_TOKEN=<operator-secret> python -m autofirm.cockpit tui --token <operator-secret>
```

The auth-gated commands (`run` / `replay` / `tui`) are **fail-closed** (CLAUDE.md §5.6):
a missing/blank configured secret, a missing/blank presented token, or any mismatch all
refuse with a non-zero exit and emit **no** data, using a constant-time comparison; no
token is ever logged. `run`/`replay`/`tui` accept `--event-log <path>` and
`--currency <ISO-4217>` (defaulting to `cockpit-events.ndjson` and `USD`). Every
non-widget cockpit module is mutation-hardened to a **1.0000** score, the TUI is proven
by a live Textual Pilot end-to-end suite, and the whole package is add-only.

## Principles (non-negotiable)

AutoFirm is built under a strict, self-activating engineering contract
([`CLAUDE.md`](CLAUDE.md)):

- **Institution-grade & secure by default.** Fail-closed, least privilege,
  append-only audit log, a maintained [STRIDE threat model](docs/threat-model.md),
  and a global kill-switch.
- **Tests with teeth.** Adversarial, property-based, mutation-tested suites — a
  green suite of easy tests is treated as worthless; the **mutation score**, not the
  pass rate, is the acceptance signal.
- **Deterministic & explainable.** Reproducible to the unit; every decision
  justifies itself (which rule fired, which feature drove the score).
- **General, never overfit.** It must work for *any* company — proven across four
  deliberately different industries, not one demo.
- **Evidence-driven.** Competing approaches run on their own branches; only the
  measured winner lands on an always-clean `main`.
- **Rigorously researched.** Every design decision is grounded in a peer-reviewed
  research library ([`docs/research/`](docs/research/)) — the foundation the build
  stands on.

## Repository layout

```
CLAUDE.md            The binding engineering contract & operating mode
docs/architecture/   Ratified architecture, ADRs & typed data contracts
docs/research/       The deep research library — one folder per source
docs/threat-model.md Maintained STRIDE threat model
docs/roadmap.md      Gated phase plan with live status
src/autofirm/        The 18 platform packages (deterministic core + engines)
tests/               Adversarial / property / mutation test suites (1,331 tests)
evidence/            Self-contained statistical & visual evidence showcase
```

## License

[MIT](LICENSE) © 2026 Alex Kapadia
