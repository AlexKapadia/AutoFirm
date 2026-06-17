# Gate 1 — Blocking Required-Changes Checklist

> **Status:** OPEN (all six items unresolved).
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

**Status: OPEN**

_Resolution:_ _(to be filled at Gate 1)_

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

**Status: OPEN**

_Resolution:_ _(to be filled at Gate 1)_

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

**Status: OPEN**

_Resolution:_ _(to be filled at Gate 1)_

---

## 4. Cost-ledger mutation gate wired into CI

Decide and wire the cost-ledger mutation gate into `.github/workflows/ci.yml`. CI currently runs mutation on `audit/`
only; the W5 cost-critical modules (`exact_cost_computation.py`, `append_only_cost_ledger.py`,
`provider_billing_reconciliation.py`) and the W4/W1 mutation-critical modules must be added to the CI mutation plane
(plan §F, §G item 7).

- Acceptance: a written decision on which modules join the CI mutation pass and the target score (≈100% on
  security-/correctness-critical modules), plus the concrete `ci.yml` change described and agreed (to be applied in
  Phase 4).

**Status: OPEN**

_Resolution:_ _(to be filled at Gate 1)_

---

## 5. Price-catalog ownership + acceptable staleness window

Define price-catalog ownership and the acceptable staleness window so the W5 "100% accurate" claim is concrete (plan
§B/W5, §G item 5):
- **who** updates prices and **how** (manual edit, automated pull from an open catalog, etc.);
- the **accepted drift / staleness window** (how stale a `price_catalog_version` may be before it is a stop-and-fix).

- Acceptance: a written ownership + update procedure and a numeric staleness tolerance, tied to `price_catalog_version`
  stamping on every `UsageCostRecord`.

**Status: OPEN**

_Resolution:_ _(to be filled at Gate 1)_

---

## 6. Cost-reconciliation SLA + runbook

Specify the cost-reconciliation SLA and runbook (plan §B/W5):
- **cadence** of `provider_billing_reconciliation.py` runs;
- exactly what **"stop-and-fix" means** when drift is non-zero — choose among: alert only / CI gate / automatic
  price-map version bump / manual correction (and when each applies).

- Acceptance: a written SLA (cadence + drift threshold) and a runbook mapping each drift condition to a concrete
  action.

**Status: OPEN**

_Resolution:_ _(to be filled at Gate 1)_

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
