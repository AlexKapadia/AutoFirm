# AutoFirm Evolution Roadmap — Phase/Gate Checklist

> **Resume from git + this roadmap + the harness task list.** This file is the authoritative execution checklist for
> the five-workstream evolution (W1–W5). The narrative rationale is in [`evolution-plan.md`](evolution-plan.md); the
> six blocking Gate-1 required-changes are in [`gate1-decisions.md`](gate1-decisions.md).
>
> **Status:** Plan RATIFIED (peer-reviewed, APPROVE-WITH-REQUIRED-CHANGES). Date: 2026-06-17.
> A gate is green **only when its objective criteria below pass** — "looks done" is not a gate. Commit + push at every
> gate. North Star/CCO review runs on the ~30-min heartbeat or at each gate; any RED is stop-and-fix.

---

## Gate 0 — Research (CRO-owned) [SEQUENTIAL — blocks all building]

Deep research into `docs/research/`, one folder per paper, covering the full method space (plan Part D).

**Green when:**
- [ ] Every workstream's method space (W1–W5 + cross-cutting threat) is covered by peer-reviewed / primary /
      professional sources, one folder per paper, each with a faithful SUMMARY + BEST-PARTS + exact citation.
- [ ] The golden sets + metrics for W1, W2, and W5 are written and ratified.
- [ ] CRO sign-off recorded.
- [ ] `docs/research/...` committed and pushed.

---

## Gate 1 — Contracts + Threat-Model + ADR (CTO-owned) [SEQUENTIAL — blocks build]

Ratify the Pydantic contracts (plan §A.3) in `docs/architecture/data-contracts.md`; write the STRIDE deltas (plan
Part E) into `docs/threat-model.md` + `threat-model-stride-components.md`; add the egress-gateway ADR; resolve all six
blocking required-changes.

**Green when:**
- [ ] Contracts compile as frozen Pydantic v2 models with fail-closed validators + property tests on the validators.
- [ ] Threat-model updated with the new component rows (C5′ gateway-as-single-egress, C4′ multi-provider secrets,
      C8′ dynamic-capability supply-chain, C9 cost-data integrity), each with a cited fail-closed control.
- [ ] Egress-gateway ADR (ADR-00X) merged.
- [ ] All **six** required-changes in [`gate1-decisions.md`](gate1-decisions.md) marked RESOLVED in writing
      (#1 live gateway-env test; #2 degraded-mode fallback; #3 router cutover audit+test; #4 CI mutation wiring;
      #5 price-catalog ownership + staleness; #6 reconciliation SLA + runbook).
- [ ] Committed and pushed.

---

## Phase 2 — Build [PARALLEL after Gate 1; 2e's gate trails 2c]

Five build tracks across distinct packages. Each track runs on its own `feature/*` or `experiment/*` branch; winners
merge to `main` only when green; losing `experiment/*` branches are deleted in the same change (no graveyard).

### Gate 2a — W4 Capability Registry (do first / loudest)

Build `capabilities/`; re-point `frontdoor/role_capability_index.py` to the live registry; retire the static scenario
tuples.

**Green when:**
- [ ] Live registry derives capabilities from a synthetic multi-hire org.
- [ ] Growth log is append-only, RFC-6962 hash-chained, gapless monotonic `seq`.
- [ ] Mutation score ≈100% on `org_event_to_capability_projection.py` + `capability_growth_log.py`.
- [ ] The four public scenarios pass **through the registry** (not the static list).
- [ ] Static tuples deleted in the same change (no graveyard); router cutover verified per Gate-1 item #3.

### Gate 2b — W5 Cost Ledger

Build `costledger/` against `FakeModelGatewayClient`.

**Green when:**
- [ ] Exact-cost path passes zero-numerical-error property tests (incl. cache/reasoning tokens, boundary-exact caps).
- [ ] Hash-chain tamper tests pass.
- [ ] Rollups (`spend_rollup_views.py`) are deterministic pure folds.
- [ ] Reconciliation drift == 0 on a synthetic multi-provider billing export.

### Gate 2c — W1 Gateway Boundary

Build `modelgateway/` + the two `experiment/gateway-litellm` and `experiment/gateway-openrouter` branches.

**Green when:**
- [ ] Both branches pass the W1 golden set under the same conditions; winner chosen on the pre-agreed metric
      (correctness ≥ CLI baseline, failover correctness, cost-attribution exactness, lowest p95 added latency, at the
      institution-grade security bar).
- [ ] Loser branch deleted in the merging change.
- [ ] CLI env-injection unit-tested; `build_argument_vector` stays pure/secret-free.
- [ ] `FakeModelGatewayClient` keeps all unit tests network-free.

### Gate 2d — W2 Knowledge Layer

Build `knowledge/` + the two `experiment/knowledge-temporal-graph` and `experiment/knowledge-vector-plus-graph`
branches on top of the existing memory layer.

**Green when:**
- [ ] Golden-set retrieval metrics measured (precision/recall@k, temporal-correctness, cross-provider fidelity, p95
      latency); winner chosen.
- [ ] Loser branch deleted in the merging change.
- [ ] Determinism holds across repeats.

### Gate 2e — W3 Bootstrap [gate depends on 2c]

Build `bootstrap/`. May start in parallel, but its gate probes the chosen gateway so it trails 2c.

**Green when:**
- [ ] Clean clone → green `make test` on Windows **and** Linux CI in **one** command.
- [ ] Idempotent re-run is a proven no-op (asserted).
- [ ] Degraded-mode never hard-blocks (kill a key mid-run → platform stays up, that capability fails closed).
- [ ] Crash-resume correctness (crash mid-step → converges on resume).

---

## Gate 3 — Integrate [SEQUENTIAL — needs 2a–2e]

Point the CLI substrate at the chosen gateway (env-injection live); route programmatic agents through
`ModelGatewayClient`; wire `costledger` to the gateway's usage emission; wire `org_event_to_capability_projection` to
the live `OrgAuditTrail`; wire `cross_model_context_assembler` into agent prompts.

**Green when:**
- [ ] An end-to-end run (extend `end_to_end_validation_harness.py`) drives one CLI agent + one programmatic agent
      through the gateway.
- [ ] Both agents are billed into the cost ledger; both read the shared knowledge layer.
- [ ] The capability registry grows on each hire during the run.
- [ ] All scenarios are public-data-only.
- [ ] Kill-switch trip halts all egress.
- [ ] Full `make test` green.

---

## Gate 4 — Harden + Evidence + Real-World Validation + Deploy [SEQUENTIAL — ship]

Mutation gate to ≈100% on the security-/correctness-critical modules; build the `evidence/` showcase (plan Part F);
run the real-world public-data validation as the final gate (extend the 4-industry corpus to **demonstrate growth**,
not enumerate fixed features).

**Green when:**
- [ ] `make test` fully green (lint, types, unit, mutation, sast, contract, secretscan).
- [ ] Mutation ≈100% on cost computation, capability projection, selection policy, env-injection, reconciliation
      (CI mutation plane extended per Gate-1 item #4).
- [ ] `evidence/` regenerates from one command (W1 selection/failover; W2 knowledge view + retrieval CIs;
      W3 bootstrap timing + idempotency proof; W4 capability-growth timeline + live role→capability graph +
      org-evolution replay; W5 zero-drift reconciliation; updated whole-system B&W architecture diagram).
- [ ] Real-world public-data validation passes (growth demonstrated across diverse real companies).
- [ ] Threat-model has no open RED.
- [ ] CI green on Linux.
- [ ] North Star review GREEN across all six areas (security/compliance, structure, test rigour, git hygiene,
      evidence-backing, production-readiness).
- [ ] Final commit + push.

---

### Parallel vs sequential summary

Phases 0, 1, 3, 4 are sequential gates. Phase 2 fans out into 2a–2e in parallel (2e's gate trails 2c). Within
W1/W2/W5 the competing `experiment/*` branches run in parallel and fan back in at their sub-gate.
