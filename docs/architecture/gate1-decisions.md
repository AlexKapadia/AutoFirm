# Gate 1 — Blocking Required-Changes Checklist

> **Status:** RESOLVED — 2026-06-17 (all six items resolved; contracts + threat-model deltas ratified). Gate 1 GREEN.
> **Date opened:** 2026-06-17.
> **Source:** Peer review of [`evolution-plan.md`](evolution-plan.md), verdict
> **APPROVE-WITH-REQUIRED-CHANGES**. These six items are the blocking conditions that **must be resolved in writing**
> before any Phase-2 building begins. Gate 1 is green only when all six are RESOLVED (each with a written resolution
> recorded below) and the contracts + threat-model deltas (Parts A.3 / E of the plan) are ratified.

Resolve each item below by replacing `Status: OPEN` with `Status: RESOLVED — <date>` and filling in the resolution.
Do not close an item without a concrete, testable answer — a vague answer keeps it OPEN.

---

## 1. Claude Code gateway-env honouring (the linchpin — live test required)

Verify that Claude Code honours `ANTHROPIC_BASE_URL`, `ANTHROPIC_AUTH_TOKEN`, and gateway model discovery for
`claude -p --bare`. This is the linchpin of the entire CLI-substrate reconciliation (plan §A.1); if it does not hold,
the keystone decision (single egress plane) must be reconsidered. **Must be proven by a live test**, not by docs alone.

- Acceptance: a recorded live `claude -p --bare --model <name>` run egresses through a local OpenAI-compatible proxy
  using the injected `ANTHROPIC_BASE_URL`/`ANTHROPIC_AUTH_TOKEN`, and `/model` discovery (or `--model`) selects a
  non-default model successfully.

**Status: RESOLVED — 2026-06-17**

_Resolution:_ **Verified live and resolved as in [ADR-003](ADR-003-model-egress-gateway.md).** Claude Code honours
`ANTHROPIC_BASE_URL`, `ANTHROPIC_AUTH_TOKEN`, and `CLAUDE_CODE_ENABLE_GATEWAY_MODEL_DISCOVERY` (gateway model
discovery, v2.1.129+): a `claude -p --bare --model <name>` run egresses through a local OpenAI-compatible proxy via
the injected base-URL/token and selects a non-default model. The linchpin **holds**, so the single-egress keystone
stands. **Caveat (load-bearing):** routing the CLI to **non-Anthropic** models through that channel is
**uncertified** — tool-use, extended-thinking, prompt-caching, and `--bare` fidelity degrade. **Ratified split:**
**CLI-substrate agents → gateway → Anthropic-family models ONLY** (full fidelity, still per-use-case selection
*across Claude variants*); **programmatic / non-CLI agents → gateway → ANY provider** (GPT / Gemini / Llama /
local) — this is where "any model / hundreds of models / many-per-use-case" lives. The uncertified cross-provider
CLI path is never exposed as a configuration.

---

## 2. Gateway → direct-to-Anthropic degraded-mode fallback (define concretely)

Define the gateway→direct-to-Anthropic degraded-mode fallback concretely (plan §B/W3, §G item 2):
- the **trigger** (what condition flips to degraded mode);
- the **audited downgrade event** (what is logged, with what fields);
- a **kill-switch to stop a hijacked gateway** routing to a third party (out-of-band, agent-cannot-disable);
- **fully automatic** behaviour for unattended runs (no human in the loop).

- Acceptance: a written state machine (normal → degraded → recovered) with the audited event schema, the kill-switch
  semantics, and the automatic recovery condition; testable by killing the gateway mid-run and asserting the platform
  stays up with a loud audited downgrade.

**Status: RESOLVED — 2026-06-17**

_Resolution:_ **Automatic, unattended-safe, capability-scoped degraded mode (threat-model C5′ D-row).** State
machine **normal → degraded → recovered**:
- **Trigger (→ degraded):** the gateway is unreachable / unhealthy per the **out-of-band** health signal (not an
  agent-assertable flag), or its OTP-style supervisor hits the **MaxR-in-MaxT restart-intensity cap**.
- **CLI/Anthropic traffic → fail-static:** automatically routes **direct-to-Anthropic** (no human in the loop) and
  emits a loud, audited **`egress.downgrade`** event — fields: `event="egress.downgrade"`, `correlation_id`,
  `from="gateway"`, `to="direct_anthropic"`, `trigger`, `restart_count`, `actor` (SPIFFE id), `occurred_at`, written
  on the **fail-closed C3 path** (never a fail-open hook).
- **Programmatic any-model traffic → fail that capability CLOSED:** any call needing the gateway's routing / IFC /
  policy refuses while degraded (no silent CaMeL-bypassing direct call). **Never a whole-platform block.**
- **Kill-switch:** out-of-band and **agent-cannot-disable**; the gateway **never holds a credential that would let a
  hijacked gateway silently re-route** to a third party — virtual keys are **per-session minted** and audience-bound,
  and the kill credential is held off the agent plane. A restart-cap breach escalates to the kill-switch / overseer.
- **Recovery (→ recovered):** the out-of-band health signal reports the supervised gateway healthy again; traffic
  re-homes to the gateway and a `egress.recovered` event is written. Fully automatic; no operator intervention.
- **Testable:** kill the gateway mid-run → assert the platform stays up, CLI traffic continues via direct-to-Anthropic
  with the audited downgrade, and a programmatic any-model call fails closed (not the platform).

---

## 3. Frontdoor router cutover — audit + test before retiring W4 static tuples

Audit and test the frontdoor router cutover before retiring the W4 static tuples. `role_capability_index.py` is
consumed by `front_desk_request_router.py`; retiring the static tuples without proving the live-registry path still
routes correctly is a regression risk (plan §B/W4).

- Prove a **multi-hire scenario** still routes correctly via the live registry (a request that should reach a
  newly-hired role does).
- Cover **keyword-matching edge cases** (overlapping keywords, no-match → fail-closed/clarify, ties, casing,
  multi-capability roles).

- Acceptance: a written test plan + passing tests demonstrating the router resolves requests identically (or better)
  through the live registry vs the retired static tuples, including the edge cases above.

**Status: RESOLVED — 2026-06-17**

_Resolution:_ **Cutover is gated on a passing live-registry routing test (Phase-2a), before any static tuple is
retired.** Required before retiring the `role_capability_index.py` static tuples:
- A test proving a **multi-hire scenario** routes correctly **via the live registry** through
  `front_desk_request_router.py` — a request that should reach a **newly-hired** role does reach it through
  `capabilities/live_capability_registry.py`, not a frozen tuple.
- **Keyword-matching edge cases** covered: overlapping keywords, **no-match → fail-closed / clarify** (never a wrong
  silent route), ties, casing, and multi-capability roles.
- **Acceptance:** the router resolves requests **identically or better** through the live registry vs the retired
  static tuples across the above edge cases; the static tuples are deleted **in the same change** that proves the
  live path (no graveyard, CLAUDE.md §3.8). Until that test is green, the static path stays.

---

## 4. Cost-ledger mutation gate wired into CI

Decide and wire the cost-ledger mutation gate into `.github/workflows/ci.yml`. CI currently runs mutation on `audit/`
only; the W5 cost-critical modules (`exact_cost_computation.py`, `append_only_cost_ledger.py`,
`provider_billing_reconciliation.py`) and the W4/W1 mutation-critical modules must be added to the CI mutation plane
(plan §F, §G item 7).

- Acceptance: a written decision on which modules join the CI mutation pass and the target score (≈100% on
  security-/correctness-critical modules), plus the concrete `ci.yml` change described and agreed (to be applied in
  Phase 4).

**Status: RESOLVED — 2026-06-17**

_Resolution:_ **YES — wire the cost-critical modules into the CI mutation plane in Phase 4.** The three W5
mutation-critical modules — `exact_cost_computation.py`, `append_only_cost_ledger.py`,
`provider_billing_reconciliation.py` — join the mutation gate at the **same bar as `audit/`: zero surviving
productive mutants (≈100% on these security-/correctness-critical modules)**.
- **Mechanism:** `pyproject.toml` already sets `paths_to_mutate = "src/autofirm/"`, so once
  `src/autofirm/costledger/` exists it is in-scope, and `scripts/run_mutation_gate.py` already **fails closed on any
  survivor** across all mutated modules. No change to the gate logic is needed.
- **Exact `ci.yml` edit (Phase 4):** the `mutation-gate` job currently runs only on `schedule` (nightly) /
  `workflow_dispatch` / the `mutation` concurrency group. Add a **path-filtered PR trigger** so any PR touching
  `src/autofirm/costledger/**` (alongside `src/autofirm/audit/**`) runs the full `mutation-gate` job pre-merge — e.g.
  add to the `mutation-gate` job a `if:` guard or a `pull_request: paths: ["src/autofirm/costledger/**",
  "src/autofirm/audit/**"]` filter, keeping the existing nightly/dispatch backstop. The job already `needs: [gates]`
  and runs on Linux (signal-based per-test timeout), which the cost modules require.

---

## 5. Price-catalog ownership + acceptable staleness window

Define price-catalog ownership and the acceptable staleness window so the W5 "100% accurate" claim is concrete (plan
§B/W5, §G item 5):
- **who** updates prices and **how** (manual edit, automated pull from an open catalog, etc.);
- the **accepted drift / staleness window** (how stale a `price_catalog_version` may be before it is a stop-and-fix).

- Acceptance: a written ownership + update procedure and a numeric staleness tolerance, tied to `price_catalog_version`
  stamping on every `UsageCostRecord`.

**Status: RESOLVED — 2026-06-17**

_Resolution:_ **Pinned, snapshot-frozen, SemVer-versioned in-repo; provider-reported cost preferred.**
- **Ownership / update procedure:** the upstream LiteLLM `model_prices_and_context_window.json` is **pinned by
  commit SHA** and snapshot-frozen into the repo as a `PriceCatalog` (data-contracts §8) with a **SemVer `version`**
  and `source_pin_sha`. Updates are a **deliberate, version-bumped, reconciled change** (a PR that bumps the SemVer,
  re-pins the SHA, and re-runs reconciliation) — **never an in-place edit**.
- **Preference order:** prefer **provider-reported cost** (`cost_source = "provider_reported"`) wherever the
  provider returns it, so the price map only drives the **fallback** path (`price_map_computed`); a stale map
  therefore affects only fallback rows, not provider-reported rows. A lookup miss is **fail-closed (refuse, never
  $0)**, stamped with `price_catalog_version` on every `UsageCostRecord`.
- **Accepted staleness window:** **until the next reconciliation cycle** (item 6 cadence). Within that window a
  stale fallback price is tolerated; at the cycle, reconciliation against the provider meter catches any drift and
  forces a version bump if needed. Beyond an unreconciled cycle, a stale map is a stop-and-fix (item 6).

---

## 6. Cost-reconciliation SLA + runbook

Specify the cost-reconciliation SLA and runbook (plan §B/W5):
- **cadence** of `provider_billing_reconciliation.py` runs;
- exactly what **"stop-and-fix" means** when drift is non-zero — choose among: alert only / CI gate / automatic
  price-map version bump / manual correction (and when each applies).

- Acceptance: a written SLA (cadence + drift threshold) and a runbook mapping each drift condition to a concrete
  action.

**Status: RESOLVED — 2026-06-17**

_Resolution:_ **Cadence + drift-driven stop-and-fix, corrections by reversing entries.**
- **Cadence:** `provider_billing_reconciliation.py` runs **per closed billing period** (the authoritative
  gross-vs-gross reconciliation against the provider's official billing export) **plus a nightly aggregate** check
  against the provider usage meter for early drift detection.
- **"Stop-and-fix" (non-zero drift):** any non-zero drift raises an **audited alert** and **blocks the next
  spend-affecting gate** until the drift is explained. Corrections are made via **reversing entries** (append-only),
  **never edits** to a recorded `UsageCostRecord` — the ledger is immutable and hash-chained.
- **In-window safety:** during the reconciliation window, the cap-enforcer uses the **conservative (higher) of
  provisional vs reconciled** cost (threat-model C9 D-row), so spend never silently overshoots a cap.
- **Honest accuracy bar (three layers):**
  - **Layer A — exact computation:** `(usage, price_vector) -> Money` exact-to-the-cent in `Decimal`
    (`exact_money_arithmetic.py`); zero numerical error (§3.11).
  - **Layer B — reconciliation:** zero-drift on **closed periods, gross-vs-gross, with credits itemized** (free-tier
    credits reconciled, never assumed-zero).
  - **Layer C — ground truth:** the **provider usage/billing meter is trusted as source of truth**; token counts come
    from provider-returned `usage`, never local tokenizers.

---

## Honest W5 accuracy bar (recorded for ratification)

The W5 "100% accurate cross-model spend tracking" bar is, concretely:
**provider-returned-usage-primary with price-map reconciliation.** Token counts come from provider-returned `usage`
(never local tokenizers); cost is provider-reported where available (`cost_source = "provider_reported"`) and
price-map-computed only as a fallback (`cost_source = "price_map_computed"`); `provider_billing_reconciliation.py`
periodically reconciles ledger totals against the provider's official billing export, and any non-zero drift is a
stop-and-fix per item 6.

**Quirks the design must explicitly handle** (none may be silently dropped):
- **Cache tokens** — prompt-cache read vs write priced separately (`cache_read_tokens` / `cache_write_tokens` fields).
- **Reasoning tokens** — reasoning-model output accounted separately (`reasoning_tokens` field).
- **Rounding** — exact `Decimal` throughout (`exact_money_arithmetic.py`); never `float`.
- **Currency** — the price snapshot and `Money` carry an explicit currency; cross-currency totals are not silently
  summed.
- **Free-tier credits** — provider credits/free tiers must not corrupt the reconciliation (the ledger records gross
  cost; credits are reconciled, not assumed-zero).
