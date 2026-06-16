# ADR-002 — Repo Layout & the Public-Code / Sensitive-Data Boundary

> **Status: ACCEPTED (Gate-3 bootstrap).** Implements the layout decreed in
> ADR-001 §5–§6 and the data-separation memory note. Determinism and fail-closed
> security are defaults (CLAUDE.md §3.2, §5.6, §5.7). This ADR documents the
> boundary the Gate-3 skeleton physically implements; it adds no new decisions.

## Context

AutoFirm is a meta-platform that builds and operates real companies, so the repo
holds two fundamentally different kinds of thing: **public platform code** (safe to
commit and deploy) and **per-company finance/operational/sensitive data** (must
NEVER reach GitHub or a deploy — CLAUDE.md §3.12/§5.6; ADR-001 §6). The boundary
must be **structural and fail-closed**, not a convention an agent can forget.

## Decision — top-level layout

```
AutoFirm/
  pyproject.toml          # PUBLIC — runtime + dev/test/analysis dep manifests (ADR-001 §5)
  .importlinter           # PUBLIC — runtime-must-not-import-analysis contract (ADR-001 §5)
  Makefile                # PUBLIC — `make test` gated pipeline (ADR-001 §3)
  src/autofirm/           # PUBLIC — platform code; committed; deployable
    foundation/           #   primitive, dependency-free building blocks
      money/              #     exact, cent-conserving monetary arithmetic (seed module)
  tests/                  # PUBLIC — mirrors src/autofirm/; test_<module>__<behaviour>.py (§5.7)
  evidence/               # PUBLIC — showcase; analysis-extra deps ONLY (§3.10)
  docs/                   # PUBLIC — architecture + research library
  .claude/                # PUBLIC — agent/role files (roles-as-data)

  .autofirm/              # PRIVATE — GITIGNORED ROOT, never committed / deployed
    workspace/            #   per-company operational scratch & client artifacts
    finance/              #   finance models, accounting, real company financials
    companies/            #   <company>/<tenant>/... per-company sensitive data
    secrets/              #   secret material (also matched by secrets/ rules)
    state/  runtime/      #   machine-local saga/runtime state, resume leases
```

Source files obey the §5.7 rules: **self-documenting names** (the seed module is
`exact_money_arithmetic.py`, not `utils.py`), **one responsibility per file**, and
the **≤300-line hard limit**. Directories read top-to-bottom in pipeline/flow
order.

## The public/private data boundary (binding, fail-closed)

- The **entire `.autofirm/` data root is gitignored** at the repo root. Per-company
  finance models, client artifacts, PII, real financials, and machine-local
  saga/runtime state live **only** there and are structurally unable to reach
  GitHub or a deploy (ADR-001 §6; data-separation memory note).
- Secret material is excluded by **multiple** overlapping rules so a single
  mis-edit cannot leak it: `.env*` (except `.env.example`), `*.key`, `*.pem`,
  `secrets/`, `.autofirm/secrets/`, and `logs/` / `*.log`. Secrets come from the
  environment or a secret manager only — never committed (CLAUDE.md §5.6).
- The production container installs the base project **without extras**, so
  analysis libraries never enter the deployable image (ADR-001 §5).
- This is the A6.4 4-gate secret/PII scanner made physical; the CI secret-scan
  gate (`make test` → `secretscan`) re-asserts it fail-closed.

## Consequences

- A newcomer can tell public from private at a glance: if it is outside
  `.autofirm/` (and not a secret pattern) it is public; if inside, it never ships.
- The skeleton commits only public scaffolding; `.autofirm/`, venvs, caches, and
  secrets are excluded by `.gitignore` and verified before commit.
- Future per-company work writes exclusively under `.autofirm/`, keeping `main`
  free of sensitive data by construction.
