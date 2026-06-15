# AutoFirm — System Architecture Overview (Gate-2 v1, ratified)

> **Status: RATIFIED at Gate 2.** Synthesizes the 26 Layer-1 research branches (all GREEN) per
> `docs/research/_program/LAYER1-SIGNOFF.md`. Every major decision cites the branch that proves it.
> Determinism and fail-closed security are defaults, not options (CLAUDE.md §3.2, §5.6).
> This file is the map; companion files hold the contracts (`data-contracts.md`), the org engine
> (`org-model.md`), the execution substrate (`substrate.md`), the seam rulings
> (`tension-resolutions.md`), and the bake-offs (`experiments.md`).

---

## 0. One-paragraph picture

AutoFirm is an **autonomous agent company**: a COO/CTO-style orchestrator runs a *dynamic, modular
org of scoped Claude Code CLI sessions* (the substrate, A5) that coordinate over an *audited,
typed message bus* (A2) on a *deterministic-DAG-by-default workflow* (A2/A3), backed by a
*tiered memory/learning layer* (A4), governed by a *fail-closed governance + tamper-evident audit
plane* (A6/A6.4/A7) and reached through an *integration/data layer* that enforces tenant isolation
and least-privilege credentials in the engine, never by convention (A8). On top of this platform
sits the **business-building layer**: a single industry-invariant `PlaybookSpine` parameterized by
an `IndustryProfile` (B12) that drives every business function (B1–B11) and emits client artifacts
(B15) and UIs (B13) to the same institution-grade bar.

---

## 1. The deterministic-core / optional-ML-layer split (CLAUDE.md §3.5)

AutoFirm is a **hybrid by construction**: a deterministic, regulator-defensible core wraps a
stochastic LLM layer that may only *refine within* the core's hard rules — and only where evidence
earns it a place (CLAUDE.md §3.4/§3.5).

| Layer | What lives here | Why deterministic / why ML | Cite |
|---|---|---|---|
| **Deterministic core** | routing predicates, DAG flow, governance VETO, audit hash-chain, tenant RLS, credential scoping, all business *formulae* (EVC, CLV, ODI, Graicunas, Little's Law, dilution, SLA, accounting identities), `derive_playbook()`, artifact integrity gates | must-never-fail, must be exact-to-the-unit, must be auditable | A1, A6, A8, B-fin, B5, B9, B11, B12, B15 |
| **Stochastic LLM layer** | natural-language reasoning, drafting, exploratory routing, soft legal/pricing explanation, design ideation, reflection-based learning | LLMs are non-deterministic (≈80 unique completions / 1000 identical prompts, A5 src 10); statistically validated, never trusted for hard decisions | A5, A4, A7, B10 |

**Invariant:** an LLM never makes a hard decision (a binding contract, a pricing floor, a money
number, an audit record, a tenant boundary). The LLM proposes; the deterministic core disposes and
records. (CLAUDE.md §3.5, §3.11; A7 trusted-plan/untrusted-data separation.)

---

## 2. The seven planes and how they fit

```
                         ┌──────────────────────────────────────────────┐
                         │   ORCHESTRATOR (COO/CTO executive agent)      │
                         │   plans · dispatches · gates · integrates     │
                         └───────────────┬──────────────────────────────┘
                                         │ roles-as-data, hire/fire/re-scope (A1.5)
            ┌────────────────────────────┼─────────────────────────────┐
            ▼                            ▼                             ▼
   ┌─────────────────┐        ┌────────────────────┐        ┌────────────────────┐
   │  DYNAMIC ORG    │        │   WORK-FLOW BUS     │        │  MEMORY / LEARNING │
   │  (A1, A1.5, B1) │◀──────▶│   (A2, A3)          │◀──────▶│  (A4)              │
   │  orchestrator-  │ typed  │  signed envelope    │ PV     │  CoALA 4-store ×   │
   │  worker spine,  │ stage  │  · deterministic    │lineage │  maturity tiers,   │
   │  roles-as-data  │ output │    DAG + Contract-  │        │  external RAG,     │
   │                 │        │    Net · saga       │        │  reflect+verify    │
   └────────┬────────┘        │    checkpoints      │        └─────────┬──────────┘
            │                 └─────────┬──────────┘                   │
            │                           │ every action                 │ every write
            ▼                           ▼                              ▼
   ┌──────────────────────────────────────────────────────────────────────────────┐
   │  GOVERNANCE / AUDIT + SAFETY / CONTROL plane (A6, A6.4, A7)                    │
   │  PROV-DM+FHIR records · history-tree/RFC-6962 Merkle log + STH · fail-closed   │
   │  VETO · read-only auditor · graduated containment + out-of-band kill-switch    │
   └──────────────────────────────────┬───────────────────────────────────────────┘
                                       │ mediates ALL external effects
                                       ▼
   ┌──────────────────────────────────────────────────────────────────────────────┐
   │  INTEGRATION / DATA LAYER (A8, A6.4)                                           │
   │  API gateway (PEP) · dual-LLM/CaMeL untrusted-input · RLS tenant isolation ·   │
   │  SPIFFE identity + short-TTL secrets broker · sender-constrained tokens        │
   └──────────────────────────────────┬───────────────────────────────────────────┘
                                       ▼
   ┌──────────────────────────────────────────────────────────────────────────────┐
   │  SUBSTRATE: orchestrated Claude Code CLI sessions (A5)                         │
   │  claude -p --bare --output-format json · subagents as roles · deny-first ·     │
   │  two-layer sandbox · --resume single-writer lease · --fork-session parallel    │
   └──────────────────────────────────────────────────────────────────────────────┘

   ════════════ BUSINESS-BUILDING LAYER (rides on all of the above) ═══════════════
   B12 IndustryProfile → derive_playbook() → PlaybookSpine (APQC 13 categories)
   drives B1 org · B2 function automation · B3 validation · B-fin · B5 pricing ·
   B6 fundraising · B7 marketing · B8 sales · B9 support/success · B10 legal ·
   B11 operations → emits B15 artifacts + B13 UIs.   EVAL: A9 + B14 prove it all.
```

### 2.1 Dynamic org (A1, A1.5, B1)
A **hierarchical orchestrator-worker spine, 3 tiers** (plan → dynamic role-design → scoped
execution), chosen because centralized coordination amplifies error 4.4× vs 17.2× for peer mesh
(A1, Google Research *blog* — Low–Moderate tier, **directional only**; experiment **E1** is the
acceptance bar, not the blog figure). Fan-out is capped at **~3–4 agents per cluster** (A1 saturation point) and
gated by a routing predicate (multi-agent IFF breadth-first ∧ low-dependency ∧ exceeds one context
window ∧ quality gain clears ~15× cost — A1). Roles are **data, not code** (A1.5, see `org-model.md`),
hired/fired/re-scoped on a heartbeat by a 5-stage lifecycle. Org *shape* per client follows
Galbraith OIPT + Graicunas span curve (B1).

### 2.2 Work-flow bus (A2, A3)
Agents speak a **typed, signed, intent-bearing envelope** (FIPA-ACL-derived + A2A Agent-Card + JWS +
Anthropic 4-part delegation contract — A2). The default flow is a **deterministic, declared,
inspectable DAG** (zero-token routing, auditable); **Contract-Net** (announce→bid→award) handles
dynamic allocation; **LLM-mediated routing is confined to exploratory work only** (A2 rejects it for
structured flows; see T5). Long-horizon work is a **saga of checkpointed phases** with semantic
compensators and idempotent replay logs, re-grounded on resume from a verbatim-stored goal (A3).

### 2.3 Memory / learning (A4)
A **CoALA four-store × maturity-tier** memory (working/episodic/semantic/procedural × Storage→
Reflection→Experience), stored as linked notes (A-Mem), OS-tier-paged (MemGPT), served by **external
Advanced/Modular RAG** (hybrid dense+lexical, query-rewrite→retrieve→re-rank→compress, edge-placed to
beat lost-in-the-middle). Learning is **gradient-free**: a reflection loop writes insights only
**after a separate judge verifies** them (verify-before-write). Five governance primitives
(WA/PV/PS/RB/VF) make every write authenticated, provenance-tracked, tenant-scoped, rollback-able,
and exactly erasable (A4).

### 2.4 Governance / audit + safety / control (A6, A6.4, A7)
A **fail-closed plane** that mediates every consequential action. Provenance is **PROV-DM + FHIR**
(why-record + security-record); the audit log is **append-only, tamper-evident** (history-tree +
RFC-6962 Merkle log with Signed Tree Heads at gates) and the data layer **refuses UPDATE/DELETE**
(A6). Safety adds trusted-plan/untrusted-data separation (CaMeL), a read-only drift-detecting
auditor, graduated containment (warn→throttle→isolate→kill), and an **out-of-band kill-switch the
agent can never hold** (A7). The PUBLIC/PRIVATE workspace boundary (A6.4) is a hard, 4-gate
secret/PII scanner that fails closed.

### 2.5 Integration / data layer (A8)
The **only path to the outside world**: an API gateway PEP (TLS, OWASP-API validation, throttling,
audit), **dual-LLM + CaMeL** so untrusted input can never trigger consequential actions,
**PostgreSQL RLS** (ENABLE+FORCE+USING+WITH CHECK, non-owner role) for tenant isolation in the
engine, and **SPIFFE identity + a short-TTL secrets broker** minting per-session least-privilege,
sender-constrained credentials (A8). No standing god-keys; no app-layer-only tenant filtering.

### 2.6 Substrate (A5)
Every agent is a **headless Claude Code CLI session** (`claude -p --bare --output-format json`),
roles are `.claude/agents/*.md` files, authority is **deny-first in MANAGED scope**, isolation is a
**two-layer sandbox** mirrored by permission deny-rules, and continuity is `--resume` under a
**single-writer lease** (parallel branches via `--fork-session`). Detail in `substrate.md`.
**Critical ruling (T2):** Claude Code hooks are **fail-OPEN** — they are a logging/iterate-gate
plane only, **never the security boundary**; permission-rules + sandbox + the A8 gateway are the
true enforcement boundary.

### 2.7 Business-building layer (B-side)
B12's `derive_playbook(IndustryProfile)` is a **design-time** configuration of an industry-invariant
`PlaybookSpine` (APQC 13 categories) by **variation points** — fail-closed on unlawful variants.
This single engine drives all business functions; their hard logic is deterministic formulae
(see `data-contracts.md` §6) and their soft logic is the governed LLM layer. Artifacts (B15) and
UIs (B13) are emitted to the institution-grade bar and written **only to the PRIVATE workspace**
when they carry client data (A6.4, CLAUDE.md §3.12).

---

## 3. Evaluation & evidence spine (A9, B14)
Nothing merges to `main` on taste. Stochastic comparisons use the **pass@k unbiased estimator** and
**McNemar/Wilcoxon/Friedman+Nemenyi** with effect size + CI (A9); the acceptance signal is the
**mutation score**, not coverage or pass rate (A9, B14). Platform and client code both ride
trunk-based dev with DORA Four-Keys telemetry (B14). Each experiment (`experiments.md`) runs on its
own pushed branch; winner merges, losers are deleted (no graveyard — CLAUDE.md §3.8).

---

## 4. Strong convergences that de-risk the build (LAYER1-SIGNOFF §2)
- **Orchestrator-worker spine** independently chosen by A1 and A2.
- **Tenant isolation via RLS / per-tenant store** agreed by A4 (PS), A5, A6.4, A8.2.
- **Fail-closed governance VETO** of A6/A7 binds over A3 resume and A4 writes.
- **No-graveyard / escalate-not-delete** shared by A6, A6.4, A1.5.
- **Mutation-score-as-acceptance** shared by A9 (platform) and B14 (client code).
- **Compliance authority centralized in B10**; B5/B7/B8 defer to it.

The seven cross-branch seams (T1–T7) are resolved in `tension-resolutions.md`.
