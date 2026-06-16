# ADR-001 — Implementation Stack for the AutoFirm Platform Build (Gate-3)

> **Status: ACCEPTED (binding, Gate-3 setup).** Decided by the CTO, grounded strictly in ratified
> architecture (`substrate.md`, `overview.md`, `data-contracts.md`) and Layer-1 research
> (A5, A8, A9, B14). Determinism and fail-closed security are defaults (CLAUDE.md §3.2, §5.6).
> Where research is silent, this ADR says so and reasons from first principles + the substrate
> reality; nothing here is asserted without a cite or an explicit "research-silent" flag.
> Supersedes nothing. Consistent with all Gate-2 rulings — it contradicts neither `substrate.md`
> nor `data-contracts.md`.

---

## Context

The platform core must: shell out to the `claude` CLI in its **bare headless JSON** form
(`substrate.md` §1; A5 src 01), parse the JSON envelope (`session_id`, `total_cost_usd`), manage a
**PostgreSQL/RLS** data layer (`data-contracts.md` §5; A8.2 src 07/08), run **async long-horizon
control loops** with saga checkpoints + `--resume` single-writer leases (`substrate.md` §4;
A3/A5 src 08), and be **mutation-testable to a high bar** (A9.3; B14.2 — mutation score is the
acceptance signal, CLAUDE.md §3.6). The research is **deliberately silent on the implementation
language** (A5 §3 excludes "the Python/TypeScript Agent SDK packages' internal APIs"; A9 §open-items
defers "exact mutation tooling per language stack"). This ADR closes that gap.

---

## 1. Primary implementation language — **Python 3.12+**

**Decision.** The orchestration core and platform glue are written in **Python 3.12+**, with
`mypy --strict` + `ruff` enforced in CI; all stage I/O is **typed JSON validated by `pydantic`
models** that mirror the language-neutral contracts in `data-contracts.md`.

**Rationale vs the main alternative (TypeScript/Node).** Both can shell out to a CLI, parse JSON,
talk to Postgres, and run async loops, so the deciding axis is the binding mutation bar (A9.3,
CLAUDE.md §3.6) and the research/data ecosystem the B-side needs. **Python wins on the acceptance
signal AutoFirm gates on**: A9's open items name `mutmut`/`cosmic-ray` (Python) alongside Stryker,
and CLAUDE.md §3.6 names `mutmut`/`cosmic-ray` first — mature, AST-level mutation operators that
target exactly the deterministic decision/formula paths (`overview.md` §1; `data-contracts.md` §6).
Python's property-based (`Hypothesis`) and fuzzing (`Atheris`) tooling is the strongest in any
ecosystem, which the §3.6 PBT-mandatory rule leans on heavily. The deterministic-core formulae
(EVC, CLV, valuation, accounting identities — `data-contracts.md` §6) demand **exact decimal
arithmetic**; Python's stdlib `decimal.Decimal` gives exact-to-the-cent results natively, whereas
JS `number` is IEEE-754 float (an own-goal against CLAUDE.md §3.11 "zero numerical errors").
`asyncio` covers the long-horizon control loops; `psycopg3` gives first-class RLS session control
(`SET LOCAL app.current_tenant` per-txn — A8.2 src 07). TypeScript's edge (one language across the
B13 client UIs) is **irrelevant to the platform core**: AutoFirm is headless (memory: headless),
and per-client UIs are a separate B13 concern that may independently choose TS. Net: Python is the
lower-risk choice for the mutation/PBT/exactness bar that actually gates merges.

---

## 2. Test stack

| Concern | Tool | Bar it enforces |
|---|---|---|
| Unit framework | **`pytest`** (+ `pytest-asyncio` for the async control loops) | one runner, marker-driven layering |
| Property-based | **`Hypothesis`** (high `max_examples`; stateful `RuleBasedStateMachine` for the saga/resume FSM) | PBT mandatory for every parser/validator/classifier/engine (A9; B14.2 src 04; §3.6) |
| Fuzzing | **`Atheris`** (coverage-guided, libFuzzer-backed) at every external-input boundary — CLI-JSON parser, envelope deserializer, untrusted-doc ingester | coverage-guided fuzz at every untrusted boundary (B14.2 src 05; A8.1) |
| Mutation testing | **`mutmut`** as the primary gate (incremental, diff-based per PR); **`cosmic-ray`** as the deeper cross-check at release | **mutation score = killed/non-equivalent is the acceptance signal**; covered-survivors == 0 on security-/correctness-critical modules; equivalent mutants excluded + audited (A9.3 src 07/09; B14.2; §3.6) |
| Coverage | **`coverage.py`** (via `pytest-cov`), branch mode on | gate **line ≥ 90% / branch ≥ 85%** — **necessary, not sufficient** (CLAUDE.md §5.5; A9.3 src 02/09) |

**Confirmation of the gates.** `pytest --cov --cov-branch` fails the build below **90% line / 85%
branch**; `mutmut run` then `mutmut results` produces the **mutation score**, and the gate is
**zero surviving covered, productive mutants on critical modules** (deterministic formulae, RLS
predicates, audit hash-chain, injection-defense interpreter). Survivors auto-spawn a harder
adversarial test task and re-run — the iterate-to-perfection loop (§3.7; A9.3 src 09; B14.2). Both
`mutmut` and `cosmic-ray` are named in A9's open items and CLAUDE.md §3.6, so neither is fabricated.

**Rationale vs alternatives.** `unittest` (stdlib) lacks the fixture/marker ergonomics the layered
strategy needs; `nose2` is effectively unmaintained. For mutation, `mutmut` is chosen primary over
`cosmic-ray` only for its faster incremental/diff-based runs (the cost blocker B14.2 src 12 flags),
with `cosmic-ray` run at the release gate for breadth — not either/or, matching the §3.5
"and-not-or" default.

---

## 3. `make test` — one-command entry point

`make test` is the single command (CLAUDE.md §5.5) and runs **fail-fast, gates in order** so a cheap
gate never hides behind an expensive one:

```
make test:
  1. lint-and-types   ruff check  &&  mypy --strict        # self-doc-name + type gate (§5.7)
  2. schema-audit     RLS invariant audit: every tenant table has
                      ENABLE+FORCE + USING + WITH CHECK + non-owner role  # fail build if absent (A8.2)
  3. unit+property    pytest -m "unit or property" --cov --cov-branch     # behaviour + PBT
  4. fuzz-smoke       atheris corpora, bounded time budget (full fuzz = nightly/CI-matrix)
  5. coverage-gate    fail if line < 90% OR branch < 85%                   # necessary-not-sufficient
  6. mutation-gate    mutmut run (diff-based) ; fail if covered productive survivors > 0
                      on critical modules ; emit mutation score to evidence/   # ACCEPTANCE SIGNAL
```

Gate order is **cheapest-and-most-likely-to-fail first** (lint → schema → tests → coverage →
mutation). Any red gate halts forward progress (CLAUDE.md §5.5). The schema-audit at step 2 is a
**structural** RLS check; the **behavioural** cross-tenant IDOR matrix (A8.2 src 11) lives in the
`security`-marked integration tests run in step 3's superset on CI. The mutation gate is the final,
load-bearing gate — coverage being green is explicitly **not** sufficient to pass.

---

## 4. CI approach — defense-in-depth, fail-closed on high/critical

No single scanner is trusted (B14.2 src 11: single-SAST FN 47–80%). The pipeline layers tools and
**fails the build on any confirmed high/critical** finding (CLAUDE.md §5.6; B14.3 NIST SSDF "PW"
mandates review+SAST+DAST+fuzz; OWASP SAMM/DSOMM):

| Stage | Tool(s) | Fail condition |
|---|---|---|
| Dependency / SCA | **`pip-audit`** (OSV/PyPI advisories) + SBOM via **CycloneDX** | any high/critical CVE; SBOM archived for provenance (SSDF "PS") |
| SAST | **`Bandit`** (Python-specific) **+ `Semgrep`** (rulesets) — two engines, deduped | confirmed high/critical after triage (single-tool rejected, src 11) |
| DAST | **OWASP ZAP** (baseline + active) against the API-gateway PEP (A8.1) in an ephemeral env | confirmed high/critical |
| Secret-scanning | **`gitleaks`** (pre-commit + CI) **+ `TruffleHog`** (verified-secrets) | any committed secret — secrets via env/secret-manager only (§5.6) |

All four are mandatory; the build is **fail-closed** — a scanner that cannot run is a failed gate,
not a skipped one (CLAUDE.md §5.6). DAST runs against the gateway because A8 makes it the only
egress PEP. Findings, the technique-coverage matrix, and the SSDF task-ID manifest are emitted to
`evidence/` (B14 §2.7/§3).

---

## 5. Runtime vs analysis-only dependency split (§3.10)

Dependencies are split across **separate manifests** so plotting/diagram/eval libraries can **never**
enter the runtime closure:

```
pyproject.toml
  [project].dependencies            # RUNTIME ONLY: pydantic, psycopg3, anyio/asyncio stdlib, httpx
  [project.optional-dependencies]
    test    = pytest, hypothesis, atheris, mutmut, cosmic-ray, coverage, pytest-cov
    dev     = ruff, mypy, bandit, semgrep, pip-audit, gitleaks
    analysis = matplotlib, plotly, graphviz, cairosvg, scipy, statsmodels   # evidence/ ONLY
```

**Mechanism + enforcement.** Runtime deps live in `[project].dependencies`; **plotting/diagram/eval
libs (matplotlib/plotly/graphviz/cairosvg + scipy/statsmodels for the A9 stats) live only in the
`analysis` extra** and are imported **only** under `evidence/` (CLAUDE.md §3.10). A CI guard test
fails the build if any non-`evidence/` module imports an `analysis`-extra package (an import-linter
contract), so the boundary is **enforced, not conventional** — the same fail-closed posture A8.2
applies to RLS. The production container installs the base project **without extras**.

---

## 6. Repo layout — public codebase vs gitignored sensitive workspace

The PUBLIC/PRIVATE boundary is the A6.4 4-gate secret/PII scanner made physical (memory:
repo-organization-and-data-separation; CLAUDE.md §3.12). Self-documenting names, ≤300-line files
(§5.7):

```
autofirm/                      # PUBLIC — platform code; committed; deployable
  orchestration/               #   control loops, claude-CLI runner, JSON-envelope parser
  bus/                         #   typed signed-envelope message bus (A2)
  audit/                       #   hash-chained append-only log (A6)
  data_layer/                  #   psycopg3 + RLS session mgmt, schema-audit (A8.2)
  credentials/                 #   SPIFFE identity + short-TTL secrets broker (A8.3)
  business/                    #   deterministic formulae as typed fns (data-contracts §6)
tests/                         # PUBLIC — mirrors autofirm/; test_<module>__<behaviour>.py (§5.7)
evidence/                      # PUBLIC — showcase; analysis-extra deps only (§3.10)
docs/                          # PUBLIC — architecture + research library
.claude/agents/*.md            # PUBLIC — roles-as-data agent files (A5 §2)

workspace/                     # PRIVATE — GITIGNORED, NEVER committed/deployed (A6.4, §3.12)
  <company>/<tenant>/...       #   per-company finance models, client artifacts, real data
```

`workspace/` is **git-ignored at the repo root and re-asserted by the A6.4 fail-closed scanner**:
client data, finance models (memory: finance-accounting-suite, real-data-decision-modeling), and
any PII live **only** there and never reach GitHub or a deploy. Public corporate data used for the
§3.12 public-data validation is **not** client data and may live in a clearly-labelled public
fixtures area; everything sensitive stays in `workspace/` and stays synthetic-or-public per §3.12.

---

## 7. Genuine forks to escalate

**One genuine fork — the async concurrency runtime for the long-horizon control loops.** Plain
`asyncio` vs **`AnyIO` structured-concurrency** vs a **`Trio`** core are close enough on the
saga/`--resume`/single-writer-lease control loop (`substrate.md` §4) that taste should not decide it
(CLAUDE.md §3.4). Structured concurrency's cancellation-scope guarantees may materially harden the
**compensator/idempotent-replay invariants** (`data-contracts.md` §4: "every forward action has a
registered compensator; replay never double-applies") against orphaned tasks on cancellation — a
correctness, not style, question. **Escalate to `experiment/concurrency-runtime`**, measured on the
saga-resume idempotency + cancellation-safety golden set (`substrate.md` §7 hooks) under the A9
procedure; winner merges, loser deleted (no graveyard, §3.8).

Everything else in §1–§6 is a **decree, not a fork**: the research and substrate reality make them
clear (Python for the mutation/PBT/exactness bar; the named test/CI tools; the manifest split; the
PUBLIC/PRIVATE layout). The container-vs-VM isolation choice and agent-teams-vs-`--resume` remain
**already-logged deferred substrate decisions** (`substrate.md` §8; A5 §4) — out of scope here.

---

## Consequences

- The build proceeds on Python 3.12+ with the gates above wired into `make test` and CI before any
  feature code lands (Gate-0/Gate-1 contract).
- The mutation gate — not coverage, not pass rate — is the merge signal (A9.3; §3.6).
- Sensitive data is structurally unable to reach the public repo (`workspace/` gitignored + A6.4).
- The single open fork (concurrency runtime) is registered as an experiment, not pre-judged.
- **Native-Windows caveat (A5):** the Claude Code OS sandbox is unavailable on native Windows, so CI
  and the per-tenant isolation boundary run on **Linux containers** (consistent with A5 §3 / the
  deferred container choice in `substrate.md` §8) — flagged for the build environment, not decided here.
```
