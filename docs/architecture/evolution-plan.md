# AutoFirm Evolution Plan — Any-Model, Shared-Knowledge, Dynamic Capabilities, Exact Cost, One-Command Setup

> **Status:** RATIFIED (peer-reviewed, APPROVE-WITH-REQUIRED-CHANGES).
> **Date:** 2026-06-17.
> **Authors:** CTO/COO architecture agent (read-only); peer-reviewed and ratified by management + QA review.
> **Scope:** The five-goal evolution of AutoFirm delivered as five workstreams (W1–W5) reconciled by one
> architectural spine. No code is written by this document — it is the resume anchor for the autonomous build.
> The six blocking required-changes from peer review are tracked in [`gate1-decisions.md`](gate1-decisions.md);
> the phase/gate execution checklist is in [`roadmap.md`](roadmap.md).

This plan complies with `CLAUDE.md` to the letter: orchestrate-don't-IC, deep peer-reviewed research first
(`docs/research/`, one folder per paper), branch-per-experiment with a clean `main` and no graveyard, adversarial +
mutation-tested suites with teeth, an `evidence/` showcase (PNG + interactive HTML + B&W flow diagrams), fail-closed
security with a maintained STRIDE threat model, self-documenting `<=300`-line files, and zero numerical errors on
deterministic paths. Every design decision routes through the deterministic-core / optional-learned-layer split
(§3.5) and "propose-then-dispose" (the existing threat-model invariant: an LLM never makes a hard decision).

The five goals are delivered as five workstreams (W1–W5), reconciled by one architectural spine (Part A).

---

## Part A — The Reconciling Architecture

### A.0 The single most important decision

AutoFirm today hardwires model invocation to one binary: `claude` via `PowerShellClaudeLauncher`, behind a clean
Protocol (`SessionLauncher` in `session_launcher_protocol.py`). That Protocol seam is the asset we build on — **we do
not rip out the CLI substrate**. The decision is:

> **Introduce a single, self-hostable, OpenAI-compatible egress gateway (the "Model Egress Plane") as the one audited
> boundary through which ALL model traffic flows — both the Claude-Code-CLI agents and new programmatic agents — and
> place a new typed provider-abstraction boundary, `src/autofirm/modelgateway/`, in front of it. The CLI substrate is
> reconciled by pointing Claude Code at the same gateway via `ANTHROPIC_BASE_URL`, so the CLI becomes just one client
> of the gateway, not a parallel uncontrolled egress.**

This is the keystone because it makes W1 (any/many models), W5 (exact cost), and the threat-model's existing C5
"Integration/API gateway (PEP)" row collapse into **one** enforcement point. One audited egress = one place for spend
accounting, one place for kill-switch, one place for least-privilege virtual keys, one place for prompt-injection
egress control. It also means the CLI agents' spend becomes visible without re-instrumenting the CLI.

### A.1 How CLI-substrate agents and any-model/many-model use coexist

There are two kinds of agent in AutoFirm, and they must both egress through the gateway:

1. **CLI-substrate agents** (existing): spawned by `PowerShellClaudeLauncher` as `claude -p --bare ...`.
   Reconciliation: the launcher's child environment (today only injects `AUTOFIRM_SESSION_CREDENTIAL`) gains three
   more **non-secret-but-scoped** env vars resolved at point-of-use exactly like the existing secret:
   - `ANTHROPIC_BASE_URL` → the gateway's URL (local proxy by default).
   - `ANTHROPIC_AUTH_TOKEN` → a **per-session virtual key** minted by the gateway via the existing `CredentialBroker`
     (least-privilege, short-TTL — reuses C4 machinery).
   - `CLAUDE_CODE_ENABLE_GATEWAY_MODEL_DISCOVERY=1` → populates the `/model` picker from `GET /v1/models`, so a CLI
     agent can be launched with `--model <name>` against any provider the gateway exposes.

   This is a **surgical** change (§5.3): `build_argument_vector` stays pure and secret-free; the env-injection path in
   `launch()` already exists and already fails closed on a missing secret. We extend the env dict, not the argv. A new
   `--model` field is added to `LaunchSpec` (optional, validated), threaded into the argv.

   > **Gate-1 blocker (required-change #1):** that Claude Code honours `ANTHROPIC_BASE_URL` / `ANTHROPIC_AUTH_TOKEN` /
   > gateway model discovery for `claude -p --bare` is the linchpin of this whole reconciliation and **must be proven
   > by a live test** before building. See [`gate1-decisions.md`](gate1-decisions.md).

2. **Programmatic agents** (new): non-CLI workers (e.g. a finance summariser, a market-intel sensemaker, a
   capability-router scorer) that call models directly. These never touch the CLI; they call the new
   `ModelGatewayClient` (Part A.3), which talks to the same gateway over the same OpenAI-compatible API with the same
   virtual-key minting.

**Both paths converge on one gateway, so both are audited and costed identically.** The gateway choice itself is a W1
bake-off (Part B/W1), but the *boundary* (`modelgateway/`) is provider-agnostic and lands first.

### A.2 Where the new provider-abstraction boundary sits

```
                          (existing, untouched logic)
  org / frontdoor / finance / decisions / market_intel / artifacts
                          |
        +-----------------+------------------+
        |                                    |
  substrate/  (CLI agents)            modelgateway/  (programmatic agents)   <-- NEW BOUNDARY
  PowerShellClaudeLauncher  --env-->        ModelGatewayClient (Protocol)
        |                                    |
        +------------------+-----------------+
                           |
                  ONE EGRESS PLANE  (self-hosted gateway proxy; OpenAI-compatible)
                  - virtual keys (per-session, least-privilege)  [reuses access/]
                  - provider routing + failover                  [W1]
                  - usage/cost emission                           [W5]
                  - kill-switch + spend caps + injection egress   [threat-model C5/C7]
                           |
              Anthropic | OpenAI | Google | open-weights | local ...
```

The new package `src/autofirm/modelgateway/` is **pure logic + one Protocol seam**, mirroring the proven substrate
pattern ("impure I/O at the edge, pure logic in the middle", `session_launcher_protocol.py`). The actual HTTP call is
the single impure act behind a Protocol; everything else (request shaping, model selection policy, response/usage
parsing, cost computation) is deterministic and unit-testable with no network (§5.5).

### A.3 Typed data contracts (Pydantic v2, frozen, fail-closed)

All new contracts follow the house style: `model_config = ConfigDict(frozen=True)`, field validators that **refuse**
(never default) on missing/ambiguous input, self-documenting names, `<=300` lines per file, module + field
docstrings, and inline `# fail-closed:` / `# least-privilege:` comments on every security-relevant line. Drafts (to be
ratified at Gate 1 in `docs/architecture/data-contracts.md`):

**(1) Model-invocation request/response** — `modelgateway/model_invocation_contract.py`

```
ModelInvocationRequest {
  correlation_id   : Uuid          # REQUIRED  joins audit (A6 trace_id) + cost ledger
  requesting_role_id : RoleId      # REQUIRED  who is spending (W5 attribution; fail-closed)
  use_case         : UseCaseId     # REQUIRED  closed-set-extensible key (W1 routing policy input)
  model_selector   : ModelSelector # REQUIRED  see (1b): a policy, not a hardcoded model string
  messages         : tuple[Message,...]  # REQUIRED  validated, injection-tagged (trusted/untrusted)
  max_output_tokens: PositiveInt   # REQUIRED  bounded work (no unbounded spend)
  temperature      : Decimal       # OPTIONAL  default deterministic 0
  credential_ref   : ScopedCredentialReference  # REQUIRED secret-free; virtual key resolved at use
  kill_switch_token: KillSwitchEpoch  # REQUIRED  refuse if epoch tripped (threat-model C7)
}
ModelSelector {                    # (1b) a SELECTION POLICY — the core of "many models per use-case"
  strategy   : Literal["pinned","preferred_with_failover","ensemble_quorum"]  # REQUIRED
  candidates : tuple[ModelRef,...] # REQUIRED  ordered; >=1; each (provider, model_name)
  quorum     : PositiveInt?        # REQUIRED iff strategy==ensemble_quorum
}
ModelInvocationResponse {
  correlation_id   : Uuid          # REQUIRED  echoes request
  served_by        : ModelRef      # REQUIRED  which model/provider actually answered (failover-aware)
  output           : Message       # REQUIRED
  usage            : TokenUsage    # REQUIRED  see (2) — provider-returned, never locally guessed
  finish_reason    : FinishReason  # REQUIRED  closed set
  served_at        : Timestamp     # REQUIRED  injected clock
}
```

**(2) Usage/cost record** — `costledger/usage_cost_record.py`

```
TokenUsage {                        # provider-returned counts ONLY (trust usage over local tokenizers)
  input_tokens          : NonNegInt  # REQUIRED
  output_tokens         : NonNegInt  # REQUIRED
  cache_read_tokens     : NonNegInt  # REQUIRED (default 0)  prompt-cache accounting
  cache_write_tokens    : NonNegInt  # REQUIRED (default 0)
  reasoning_tokens      : NonNegInt  # REQUIRED (default 0)  reasoning-model accounting
}
UsageCostRecord {                   # ONE immutable ledger row per invocation (append-only)
  correlation_id : Uuid            # REQUIRED  joins invocation + audit
  requesting_role_id : RoleId      # REQUIRED  attribution (per-role/team/company rollups)
  use_case       : UseCaseId       # REQUIRED  per-use-case rollups
  served_by      : ModelRef        # REQUIRED
  usage          : TokenUsage      # REQUIRED
  unit_prices    : PriceVector     # REQUIRED  the EXACT per-token prices applied (Decimal, frozen snapshot)
  cost           : Money           # REQUIRED  EXACT Decimal via exact_money_arithmetic (zero rounding error)
  cost_source    : Literal["provider_reported","price_map_computed"]  # REQUIRED  provenance of the number
  price_catalog_version : SemVer   # REQUIRED  which price snapshot was used (reconcilable)
  recorded_at    : Timestamp       # REQUIRED  injected clock
  prev_hash      : Hash            # REQUIRED  RFC-6962 chain link (reuses audit/ machinery)
  record_hash    : Hash            # REQUIRED  tamper-evidence (cost-data integrity, threat-model new row)
}
```

Cost is computed in `foundation/money/exact_money_arithmetic.py` (already exists, exact `Decimal`) — **never
`float`**. Token counts are integers; prices are `Decimal`; cost is `Decimal`. This is what makes W5
exact-to-the-unit and is the deterministic-path "zero numerical errors" guarantee (§3.11).

**(3) Capability descriptor** — `capabilities/capability_descriptor.py`

```
CapabilityDescriptor {              # ONE advertised capability of the live org (replaces the locked list)
  capability_id  : CapabilityId    # REQUIRED  stable identity
  name           : str             # REQUIRED  self-documenting ("own paid acquisition")
  keywords       : frozenset[str]  # REQUIRED  routing surface (derived OR explicitly declared)
  owning_role_id : RoleId          # REQUIRED  which role provides it (single-writer link)
  required_clearance : str         # REQUIRED  least-privilege (deny-by-default sentinel if unset)
  provenance     : CapabilityProvenance  # REQUIRED  WHY it exists (hire/promote/auto-create + gap ref)
  maturity       : Literal["proposed","active","deprecated"]  # REQUIRED  lifecycle
}
```

**(4) Registry entry (append-only, audited growth event)** — `capabilities/capability_registry_event.py`

```
CapabilityRegistryEvent {           # append-only growth log — this is HOW growth is recorded + SHOWN
  seq            : u64             # REQUIRED  monotonic, gapless (like the audit trail)
  kind           : Literal["CAPABILITY_ADDED","CAPABILITY_PROMOTED","CAPABILITY_DEPRECATED","CAPABILITY_RESCOPED"]
  descriptor     : CapabilityDescriptor  # REQUIRED  the post-event state of the capability
  triggered_by   : RoleId          # REQUIRED  the managing role whose lifecycle action caused growth
  org_event_ref  : OrgEventId      # REQUIRED  link back to the org-lifecycle event (hire/auto_create)
  rationale      : str             # REQUIRED  PII-free 'why' (audited)
  occurred_at    : Timestamp       # REQUIRED  injected clock
  prev_hash/record_hash : Hash     # REQUIRED  tamper-evident chain (reuses RFC-6962)
}
```

### A.4 New packages / files (flow-ordered, self-documenting, `<=300` lines each)

`src/autofirm/modelgateway/` (W1 — the egress boundary):
- `model_invocation_contract.py` — the request/response/selector/usage contracts (3 above).
- `model_reference.py` — `ModelRef`, `UseCaseId`, `CapabilityId`, closed enums.
- `model_egress_client_protocol.py` — `ModelGatewayClient` Protocol + `FakeModelGatewayClient` deterministic double
  (mirrors `FakeSessionLauncher`). The single impure seam.
- `openai_compatible_gateway_client.py` — production client (the only file touching HTTP); resolves virtual key at
  point-of-use; fail-closed on missing key/kill-switch.
- `model_selection_policy.py` — pure: turns a `ModelSelector` + live availability into the ordered call plan (pinned /
  preferred-with-failover / ensemble-quorum).
- `ensemble_quorum_reconciler.py` — pure: reconciles N model answers into one (majority/agreement), for "many models
  interoperating" use-cases.
- `cli_gateway_env_injection.py` — pure builder of the `ANTHROPIC_BASE_URL` / `ANTHROPIC_AUTH_TOKEN` / discovery env
  map for the CLI substrate (consumed by the launcher).

`src/autofirm/costledger/` (W5 — exact spend):
- `usage_cost_record.py` — `TokenUsage`, `UsageCostRecord`, `PriceVector` (2 above).
- `price_catalog_contract.py` — versioned, frozen per-token price snapshot + `price_catalog_version`.
- `exact_cost_computation.py` — pure: `(usage, price_vector) -> Money` via `exact_money_arithmetic`; zero float.
- `append_only_cost_ledger.py` — RFC-6962-chained, append-only ledger (reuses `audit/rfc6962_hashing.py`).
- `spend_rollup_views.py` — pure deterministic rollups (per-role, per-team, per-use-case, per-model, whole-company).
- `provider_billing_reconciliation.py` — pure: compares ledger totals vs a provider billing export, emits a labelled
  drift report.

`src/autofirm/capabilities/` (W4 — dynamic, evolving capability registry):
- `capability_descriptor.py`, `capability_registry_event.py` (3, 4 above).
- `capability_growth_log.py` — append-only, audited, gapless growth log (the source of truth for "show the
  evolution").
- `live_capability_registry.py` — derives the *current* capability set from the growth log + live `OrgState`;
  replaces the static enumeration that `role_capability_index.py` and `operate_platform_checks.py` hardcode.
- `org_event_to_capability_projection.py` — pure: maps an `OrgEventKind` (HIRED / AUTO_CREATED / RESCOPED / FIRED)
  into the corresponding `CapabilityRegistryEvent`. This is the bridge that makes the registry **grow automatically**
  as the org hires/promotes/evolves.

`src/autofirm/knowledge/` (W2 — shared cross-model knowledge):
- `shared_knowledge_contract.py` — typed shared-context block (model-agnostic).
- `knowledge_graph_backend_protocol.py` — Protocol seam over the chosen store (temporal-graph vs vector+graph — W2
  bake-off), plus a deterministic in-memory fake.
- `cross_model_context_assembler.py` — pure: assembles the minimal shared context block a heterogeneous model needs
  (links to existing `agent_memory_layer.py`).
- `obsidian_vault_export_view.py` — read-model that renders the shared knowledge as an Obsidian-compatible
  markdown+links view ("Obsidian-or-better" deliverable; export only, never the source of truth).

`src/autofirm/bootstrap/` (W3 — one-command, idempotent, self-healing setup):
- `bootstrap_step_contract.py` — typed idempotent step (`check() -> applied?` + `apply()`); each step must be safe to
  re-run.
- `idempotent_environment_bootstrapper.py` — the orchestrated, self-healing setup flow (venv, deps, gateway
  reachability, key presence, migrations).
- `degraded_mode_policy.py` — pure: decides graceful degradation when an optional dependency (e.g. a provider key) is
  absent — fail-closed for that capability, never a hard platform block (W3/G).
- `bootstrap_doctor_report.py` — read-only diagnosis report ("what is missing and exactly how to fix it").

> All of the above are new packages — no existing file is rewritten. `role_capability_index.py` and
> `operate_platform_checks.py`/`public_company_scenarios.py` are **re-pointed** to read from
> `capabilities/live_capability_registry.py` instead of static tuples (the minimal surgical edit that retires the
> locked-in list without a graveyard).

---

## Part B — Per-Workstream Design

Each workstream states the chosen approach, the 1–2 credible alternatives that earn a competing `experiment/<approach>`
branch, the pre-agreed golden set + metric to pick the winner, and where a hybrid is the right call.

### W1 — Any model, many models per use-case, reconciled with the CLI substrate

**Chosen approach:** Self-hosted OpenAI-compatible **gateway proxy** as the egress plane, with the new `modelgateway/`
provider-abstraction in front. Selection is a **deterministic policy core** (`model_selection_policy.py`) — `pinned`,
`preferred_with_failover`, `ensemble_quorum` — driven by typed `ModelSelector`. "Many models per use-case
interoperating" is realised by `ensemble_quorum_reconciler.py` (deterministic reconciliation of N answers). The CLI
substrate is reconciled by env-injection (A.1).

**Hybrid call (deterministic core + optional learned layer):** The *routing decision* (which candidate model for a
use-case) is **deterministic by default** (ordered candidate list + availability + cost cap). An **optional learned
router** (bandit/quality-cost predictor) may *propose* a reordering, but the deterministic core *disposes* — it can
only pick within the allowed candidate set and never violates a cost cap or a kill-switch. This is exactly the existing
"LLM never makes a hard decision" invariant.

**Competing branches:**
- `experiment/gateway-litellm` — LiteLLM self-hosted proxy (open price catalog
  `model_prices_and_context_window.json`, virtual keys, per-key spend, failover, OpenAI-compatible). **Wins if** it
  gives accurate provider-passthrough cost + reliable `/v1/models` discovery for the CLI picker, fully self-hostable,
  no markup, with the lowest p95 added latency.
- `experiment/gateway-openrouter` — OpenRouter (cloud, widest catalog, returns **actual per-request cost**). **Wins
  if** provider-returned exact cost materially beats price-map accuracy AND the cloud-egress threat-model delta is
  acceptable (it adds a third-party data-flow row — likely disqualifying for the institution-grade bar, but it must be
  measured, not assumed).
- (scoped-out unless W1 stalls) Vercel AI Gateway / Portkey noted in `docs/research/` for completeness of the method
  space (§3.4 full-space rule), not branched unless the two above both fail a gate.

**Golden set + metric (pre-agreed, Gate-1 ratified):** a frozen set of ~40 deterministic prompts spanning the four
`public_company_scenarios.py` industries × {summarise, extract, classify, route} use-cases, each with a known-good
expected output. Metrics: (a) **functional correctness** vs expected (must be ≥ the CLI-only baseline), (b) **failover
correctness** (kill one candidate provider → traffic moves with no lost request), (c) **cost-attribution exactness**
(ledger total == sum of per-call provider-reported cost, to the unit — gates into W5), (d) **p95 added latency** vs
direct CLI. Winner = the gateway that passes (a)+(b)+(c) with the lowest (d) at the institution-grade security bar.
**Loser branch is deleted in the same change (no graveyard).**

### W2 — Shared knowledge / coordination ("Obsidian-or-better")

**Chosen approach:** A model-agnostic **shared knowledge layer** (`knowledge/`) behind a Protocol seam, composed with
the *already-pluggable* `memory/agent_memory_layer.py` (which already does versioned, provenance-tracked,
principal-scoped, rollback-able external memory — we extend it, not replace it). Heterogeneous models share context via
`cross_model_context_assembler.py`, which emits a **typed, minimal shared-context block** (not a raw vault dump —
honouring the memory layer's "no context-stuffing / Lost-in-the-Middle" research). "Obsidian-or-better" is delivered as
a **read-only export view** (`obsidian_vault_export_view.py`): the graph store is the source of truth; the
Obsidian-compatible markdown+backlinks view is a rendered projection for human navigability and for the `evidence/`
showcase.

**Hybrid call:** deterministic provenance/versioning/scoping core (the existing memory store, untouched) + optional
learned retrieval ranking on top (the existing `retrieval_ranking_score.py` is already injected/tunable — no magic
constants). The *graph relationships* (who-knows-what, capability links) are deterministic; the *ranking* may be
learned.

**Competing branches:**
- `experiment/knowledge-temporal-graph` — temporal knowledge-graph (Graphiti/Zep-style: bi-temporal, edge-validity
  intervals). **Wins if** it reconstructs "what did the org know at time T" exactly (audit-grade temporal queries) and
  out-performs on multi-hop coordination questions in the golden set.
- `experiment/knowledge-vector-plus-graph` — vector + graph hybrid (Mem0-style). **Wins if** it matches temporal-graph
  on coordination recall at materially lower retrieval latency and simpler ops (fewer moving parts = better for
  unattended operation, W3/G).

**Golden set + metric:** a frozen set of cross-model coordination tasks (model A writes a fact; model B from a
*different provider* must retrieve and act on it correctly) plus multi-hop questions ("which role owns the capability
that produced artifact X?"). Metrics: **retrieval precision/recall@k vs ground truth**, **temporal-correctness**
(answers respect as-of-time), **cross-provider fidelity** (B's answer matches A's intended fact), **p95 retrieval
latency**, **determinism** across repeats. Winner merges; loser deleted.

### W3 — Effortless, idempotent, self-healing one-command setup

**Chosen approach:** A typed **idempotent bootstrap pipeline** (`bootstrap/`) wrapping the existing `make install`.
Each step implements `bootstrap_step_contract.py` with a `check()` that makes re-running a no-op ("do nothing if
already applied") — the same idempotency discipline `CLAUDE.md §4.8` mandates for the resilience watchdog. Steps: venv
→ deps (runtime+dev+test+analysis+artifacts extras) → gateway reachability probe → provider-key presence probe →
DB/migration (if any) → smoke check. A **doctor report** (`bootstrap_doctor_report.py`) tells the operator exactly
what is missing and how to fix it. **Self-healing** = each step detects-and-repairs (e.g. missing venv → create; stale
lock → rebuild) and is safe under crash-resume (resume from filesystem + git state, never a half-applied step). This
composes with `CLAUDE.md §4.8(b)` OS-level scheduler resilience for the unattended autonomous build.

**Degraded-mode (the "never hits blockers" core):** `degraded_mode_policy.py` is pure and decides, per missing
dependency, whether the platform **fails that capability closed but stays up** (e.g. no OpenAI key → OpenAI candidates
are pruned from selectors, Anthropic/local still serve; gateway unreachable → CLI agents still run direct to Anthropic
via a documented fallback, with a loud audited downgrade). A missing API key is **fail-closed for that provider, never
a hard platform block** (G).

> **Gate-1 blocker (required-change #2):** the gateway→direct-to-Anthropic degraded-mode fallback must be defined
> concretely (trigger, audited downgrade event, kill-switch to stop a hijacked gateway routing to a third party, fully
> automatic for unattended runs) before this is built. See [`gate1-decisions.md`](gate1-decisions.md).

**Competing branches** (small, fast bake-off): `experiment/setup-make-driven` (extend the existing Makefile + a thin
Python orchestrator — minimal new surface) vs `experiment/setup-python-orchestrated` (a single `python -m
autofirm.bootstrap` entry that subsumes make). **Metric:** clean-clone-to-green-`make test` on a fresh Windows box AND
fresh Linux CI, **number of manual steps (target: 1)**, **idempotent re-run is a no-op (asserted)**, **crash-resume
correctness**, and **degraded-mode never hard-blocks** (kill a key mid-run, platform stays up). Winner = fewest manual
steps + provably idempotent + green on both OSes.

### W4 — Dynamic, evolving capability registry (replacing the locked-in list)

**The problem, precisely (verified):** capabilities are derived deterministically from
`RoleCharter.responsibilities` via `extract_capability_keywords()` in `role_capability_index.py` — that part is
already good and general. The lock-in is that the **source org is fed from static tuples**:
`public_company_scenarios.py` hardcodes 4 scenarios with fixed `gap_role_responsibilities`, and
`operate_platform_checks.py` enumerates ~60 fixed feature checks. `RoleCharter` already accepts arbitrary
responsibilities (verified) — it just isn't fed from a live, growable registry.

**Chosen approach (no bake-off needed — this is an architecture fix, not a method choice):** Introduce `capabilities/`
with an **append-only, audited capability growth log** that is the single source of truth for "what the org can do",
and a `live_capability_registry.py` that derives the *current* capability set from that log + live `OrgState`. The
bridge `org_event_to_capability_projection.py` subscribes to the existing `OrgAuditTrail`/`OrgEventKind` stream: every
`ROLE_HIRED` / `ROLE_AUTO_CREATED` / `ROLE_RESCOPED` / `ROLE_FIRED` event **automatically** emits a
`CapabilityRegistryEvent`, so the capability surface **grows/shrinks exactly as the org evolves** — up to thousands of
capabilities at maturity, with no hardcoded ceiling. `role_capability_index.py` is re-pointed to read from the live
registry; the static scenario tuples are retired (deleted in the same change — no graveyard).

> **Gate-1 blocker (required-change #3):** the frontdoor router cutover must be audited + tested before retiring the
> W4 static tuples (`role_capability_index.py` is consumed by `front_desk_request_router.py`) — prove a multi-hire
> scenario still routes correctly via the live registry and cover keyword-matching edge cases. See
> [`gate1-decisions.md`](gate1-decisions.md).

**How growth is RECORDED (append-only, audited):** the `capability_growth_log.py` is RFC-6962 hash-chained (reuses
`audit/rfc6962_hashing.py`), gapless, monotonic `seq` — identical discipline to `OrgAuditTrail` and the cost ledger.
Each event links back to the org-lifecycle event (`org_event_ref`) and carries a PII-free rationale. The capability
set at any time T is a pure replay of the log → fully reconstructable and auditable.

**How growth is SHOWN (the evidence/visualization angle):** this is the headline showcase deliverable.
- **A capability-growth timeline** (PNG + interactive HTML): capabilities-over-time as the org hires/promotes,
  annotated with the triggering org event — proving the org *evolves* and the system *visibly grows*.
- **A live capability/org graph** (B&W flow diagram, HTML+PNG): roles → owned capabilities, with provenance edges,
  regenerated from the registry (not hand-drawn) so it can't drift.
- **A capability inventory table** rendered from the registry, sortable by role/maturity/clearance.
- An **"org-evolution replay"** that takes a scenario from genesis through N hires and renders the growing capability
  surface frame-by-frame.

**Generality guard (§3.9):** because the registry is derived from arbitrary charter responsibilities through the
existing pure keyword extractor, there are **no magic constants and no per-scenario special-casing** — feed any
company, any role set, any number of roles, and the capability surface grows correctly. The four public scenarios
become *seeds that demonstrate growth*, not the *definition* of capability.

### W5 — 100%-accurate cross-model spend tracking

**Chosen approach:** The `costledger/` package (A.3 contract 2). Cost is computed on a **deterministic, exact path**:
`cost = exact_cost_computation(usage, price_vector)` using `foundation/money/exact_money_arithmetic.py` (`Decimal`,
zero float) against a **versioned, frozen price snapshot** (`price_catalog_contract.py`). Each invocation writes
exactly one immutable, hash-chained `UsageCostRecord`. **Token counts come from provider-returned `usage`** (never
local tokenizers), and explicitly account for **prompt-cache read/write and reasoning tokens** (separate fields →
separate prices). `cost_source` records whether the number was **provider-reported** (preferred, exact) or
**price-map-computed** (fallback when a provider doesn't return cost), so every figure is provenance-tagged.

**Honest accuracy bar (peer-review correction):** the W5 "100% accurate" bar is concretely
**provider-returned-usage-primary with price-map reconciliation**. The design must handle the known quirks: cache
tokens, reasoning tokens, rounding, currency, and free-tier credits. See required-changes #5 and #6 in
[`gate1-decisions.md`](gate1-decisions.md).

**Reconciliation (what makes it "100% accurate, 1 or 100s of models"):** `provider_billing_reconciliation.py`
periodically compares the ledger's per-provider totals against the provider's official billing export and emits a
labelled drift report; any non-zero drift is a stop-and-fix (and a clue that the price snapshot needs versioning
forward). This is the institution-grade "exact to the unit AND reconcilable" bar.

> **Gate-1 blockers (required-changes #4–#6):** wire the cost-ledger mutation gate into `.github/workflows/ci.yml`
> (currently mutation runs on `audit/` only); define price-catalog ownership + acceptable staleness window; specify the
> cost-reconciliation SLA + runbook (cadence, and what "stop-and-fix" means: alert vs CI gate vs auto price-map bump vs
> manual correction). See [`gate1-decisions.md`](gate1-decisions.md).

**Determinism (the exactness test):** for a fixed `(usage, price_vector)`, `cost` is bit-identical every run; rollups
(`spend_rollup_views.py`) are pure folds. This is directly testable to zero numerical error (§3.11) — and is the
mutation-critical module of W5.

**Competing branch (narrow):** `experiment/cost-provider-reported` (trust provider-returned cost as primary, price-map
only as fallback) vs `experiment/cost-pricemap-primary` (always compute from the price map, use provider-reported only
to reconcile). **Metric:** end-to-end exactness vs a known provider billing export across a multi-provider run — **zero
drift wins**; if both hit zero, the simpler/more-reconcilable design wins. (Likely winner: provider-reported-primary
with price-map reconciliation, but it must be measured.)

---

## Part C — Phased, Gated Roadmap

> The authoritative execution checklist is [`roadmap.md`](roadmap.md). This part is the narrative rationale.

Each phase ends in a **hard, objective verification gate** (green = advance). Dependency order is explicit; parallelism
is marked. Commit+push at every gate (§3.13). North Star/CCO read-only review runs on the ~30-min heartbeat or at each
gate (§4.7); any RED is stop-and-fix.

**Phase 0 — Research gate (CRO-owned). [SEQUENTIAL, blocks all building]**
Deep research into `docs/research/`, one folder per paper, full method space (Part D).
**Gate 0 green:** CRO signs off that every workstream's method space is covered by peer-reviewed/primary/professional
sources with faithful summaries + "best parts" notes + exact citations; the golden sets + metrics for W1, W2, W5 are
written and ratified. Commit `docs/research/...`, push.

**Phase 1 — Contracts & threat-model deltas (CTO-owned). [SEQUENTIAL, blocks build]**
Ratify the Pydantic contracts (A.3) in `docs/architecture/data-contracts.md`; write STRIDE deltas (Part E) into
`docs/threat-model.md` + `threat-model-stride-components.md`; add ADR-00X for the egress-gateway decision; resolve all
six blocking required-changes in [`gate1-decisions.md`](gate1-decisions.md). No behaviour yet.
**Gate 1 green:** contracts compile as frozen Pydantic models with fail-closed validators + property tests on the
validators; threat-model updated with new component rows (gateway-as-single-egress, multi-provider secrets,
dynamic-capability supply-chain, cost-data integrity) each with a cited fail-closed control; ADR merged; six
required-changes RESOLVED in writing. Commit+push.

**Phase 2 — Build, fan-out across workstreams. [PARALLEL after Gate 1]**
Four independent build tracks (genuinely independent — different packages):
- **2a W4 capability registry** (lowest external risk, highest user value — do first/loudest): build `capabilities/`,
  re-point `role_capability_index.py`, retire static tuples. **Gate 2a:** live registry derives capabilities from a
  synthetic multi-hire org; growth log is append-only/hash-chained/gapless; mutation score ≈100% on the projection +
  growth-log modules; the four public scenarios pass *through the registry* (not the static list); no graveyard.
- **2b W5 cost ledger:** build `costledger/` against the `FakeModelGatewayClient`. **Gate 2b:** exact-cost path
  zero-error property tests; hash-chain tamper tests; rollups deterministic; reconciliation drift = 0 on a synthetic
  billing export.
- **2c W1 gateway boundary:** build `modelgateway/` + the two `experiment/gateway-*` branches. **Gate 2c:** both
  branches pass the W1 golden set under the same conditions; winner chosen on the metric; loser deleted; CLI
  env-injection unit-tested (argv stays pure/secret-free); `FakeModelGatewayClient` keeps unit tests network-free.
- **2d W2 knowledge layer:** build `knowledge/` + the two `experiment/knowledge-*` branches on top of the existing
  memory layer. **Gate 2d:** golden-set retrieval metrics; winner chosen; loser deleted; determinism holds.
- **2e W3 bootstrap** can start in parallel but **its gate depends on 2c** (it probes the gateway). **Gate 2e:**
  clean-clone → green `make test` on Windows + Linux in 1 command; idempotent re-run is a no-op; degraded-mode never
  hard-blocks; crash-resume correct.

Each track commits+pushes on its own `feature/*` or `experiment/*` branch; winners merge to `main` only when green.

**Phase 3 — Integrate & wire the egress plane. [SEQUENTIAL, needs 2a–2e]**
Point the CLI substrate at the chosen gateway (env-injection live); route programmatic agents through
`ModelGatewayClient`; wire `costledger` to the gateway's usage emission; wire `org_event_to_capability_projection` to
the live `OrgAuditTrail`; wire `cross_model_context_assembler` into agent prompts.
**Gate 3 green:** an end-to-end run (extend `end_to_end_validation_harness.py`) drives one CLI agent + one programmatic
agent through the gateway, both billed into the ledger, both reading the shared knowledge layer, with the capability
registry growing on each hire — all on public-data-only scenarios; kill-switch trips halt all egress; full `make test`
green.

**Phase 4 — Harden, mutation, evidence, real-world validation. [SEQUENTIAL]**
Mutation gate to ≈100% on the security-/correctness-critical modules (cost computation, capability projection,
selection policy, env-injection, reconciliation). Build the `evidence/` showcase (Part F). Run the real-world
public-data validation as the final gate (extend the existing 4-industry corpus to *demonstrate growth*, not enumerate
fixed features).
**Gate 4 green (ship):** `make test` fully green (lint, types, unit, mutation, sast, contract, secretscan); `evidence/`
regenerates from one command; threat-model has no open RED; CI green on Linux; North Star review GREEN across all six
areas. Commit+push final.

> **Parallel vs sequential summary:** Phases 0,1,3,4 are sequential gates. Phase 2 fans out into 2a–2e in parallel
> (2e's gate trails 2c). Within W1/W2/W5 the competing `experiment/*` branches run in parallel and fan back in at their
> sub-gate.

---

## Part D — Deep-Research Question List (seeds the Phase-0 gate)

Grouped by workstream; each must be answerable from peer-reviewed / primary / professional sources, covering the full
method space (not one convenient family), filed one-folder-per-paper under `docs/research/`.

**W1 — Multi-model gateway & routing (new folder `B1-multi-model-egress/`)**
1. Comparative architecture of self-hostable OpenAI-compatible gateways (LiteLLM, vLLM router, others): routing,
   failover, virtual keys, spend — primary docs + any peer-reviewed eval.
2. Cloud gateways returning exact per-request cost (OpenRouter) — accuracy claims, data-flow/privacy posture (feeds
   threat model).
3. Claude Code → non-Anthropic via `ANTHROPIC_BASE_URL` / `ANTHROPIC_AUTH_TOKEN` / gateway model discovery — primary
   documentation; what is guaranteed vs undocumented.
4. Model-routing/selection literature: cost-aware routing, cascades, LLM-router bandits, ensemble/quorum reconciliation
   across heterogeneous models — the full method space (deterministic policy → learned router → ensemble).
5. Failover/circuit-breaker patterns for provider outages (no lost request).

**W2 — Shared knowledge / coordination (new folder `B2-shared-knowledge-graph/`)**
6. Temporal knowledge graphs for agent memory (Graphiti/Zep bi-temporal) — primary papers/docs; as-of-time query
   semantics.
7. Vector+graph hybrid memory (Mem0 and peer-reviewed RAG-graph work) — recall vs latency vs ops complexity.
8. MCP memory-server / shared-memory-block patterns for heterogeneous agents — interop guarantees.
9. Context minimisation vs context-stuffing (Lost-in-the-Middle, RULER — already in A4) applied to cross-model
   sharing.
10. How a graph store is rendered to a human-navigable view (Obsidian-style backlinks) without becoming the source of
    truth.

**W3 — Idempotent self-healing setup (extend `A3-long-horizon-autonomy/` or new `B3-resilient-bootstrap/`)**
11. Idempotency / convergent-configuration theory (declarative desired-state, convergence) — primary sources.
12. Crash-safe resume from filesystem+git state (ties to existing saga/checkpoint research A3).
13. Graceful-degradation patterns: failing a capability closed while keeping the platform up.

**W4 — Dynamic capability registries (extend `A1.5-auto-hiring-role-creation/` + new `B4-capability-registries/`)**
14. MCP-registry-style runtime capability discovery + verification/signing — primary docs + the supply-chain threat
    literature.
15. Agent-Skills NL capability packaging — how capabilities are declared, versioned, signed.
16. Capability/skill-growth modelling in organisations (ties to existing competency-gap + workforce-reshaping papers).
17. Append-only event-sourced registries (event sourcing as the growth log) — primary sources; reconstructable state.

**W5 — Exact cross-model cost (new folder `B5-exact-cost-accounting/`)**
18. Provider-returned usage vs local tokenizer accuracy — primary docs; prompt-cache + reasoning-token accounting
    semantics per provider.
19. Decimal/exact-money accounting standards (ties to existing `exact_money_arithmetic`) — avoiding float in financial
    ledgers.
20. Billing reconciliation methodology (ledger vs provider export) — accounting/audit literature.
21. Open price catalogs (LiteLLM `model_prices_and_context_window.json`) — versioning + staleness handling.

**Cross-cutting threat (extend `A7` / `A8` syntheses)**
22. Gateway-as-single-egress as a chokepoint: failure-mode and DoS analysis.
23. Multi-provider secret management at scale (per-provider least-privilege virtual keys) — extends A8.3.
24. Cost-data spoofing/tampering (a compromised agent inflating/hiding spend) — integrity controls.

---

## Part E — Threat-Model Deltas (STRIDE)

To be written into `docs/threat-model.md` (index) and `docs/threat-model-stride-components.md` (per-component
matrices). New/extended components and the fail-closed controls:

**C5′ — Model Egress Gateway as the single egress plane (extends existing C5 "Integration/API gateway (PEP)").**
- **S (Spoofing):** an agent forges a virtual key. *Control:* per-session virtual keys minted by the existing
  `CredentialBroker` with short TTL + SPIFFE-style scope; gateway rejects unknown/expired keys (fail-closed).
- **T (Tampering):** request mutated in flight. *Control:* TLS in transit; the request `correlation_id` is bound into
  the audit + cost record (cross-checkable).
- **R (Repudiation):** "I never made that call / spent that." *Control:* every invocation writes a hash-chained
  `UsageCostRecord` + audit record through the gateway path (which can fail closed) — no dropped-record repudiation
  (mirrors existing T2/C3 control).
- **I (Info disclosure):** prompt-injection-driven exfiltration via tool/model output, or cross-agent context leak
  through a shared gateway. *Control:* CaMeL/dual-LLM trusted-plan/untrusted-data separation already mandated (A7 §3);
  per-session scope; context minimisation via the knowledge assembler.
- **D (DoS):** gateway is now a single chokepoint — its outage halts all agents. *Control:* the `degraded_mode_policy`
  documented fallback (CLI agents can degrade to direct-to-Anthropic with a loud audited downgrade), provider failover
  in `model_selection_policy`, and gateway run as a supervised, auto-restarting local process under the W3
  bootstrapper.
- **E (Elevation):** an agent picks a more-capable/more-expensive model than allowed. *Control:*
  `ModelSelector.candidates` is a closed allowed-set per use-case; the deterministic core disposes; cost caps +
  kill-switch epoch refuse out-of-policy calls (fail-closed).

**C4′ — Multi-provider secrets (extends C4 "Credential broker").**
- **I/E:** one provider key leaks → blast radius. *Control:* per-provider, per-session least-privilege virtual keys,
  short-TTL, auto-revoked at retire; **no god-key spanning providers**; secrets only via env/secret-manager (existing
  `secret_source_protocol.py`); never in argv/logs/prompt (existing launcher invariant extended to the new env vars).

**C8′ — Dynamic capability supply-chain (extends C8 "Dynamic role spawn / hire path").**
- **S/T/E:** a malicious capability/skill/MCP server is loaded → capability sprawl / code execution. *Control:* dynamic
  capability loading must be **signed, verified, least-privilege, fail-closed** (research item 14); capability registry
  entries are authored only by the managing role (reuses the existing manager-authored / no-self-grant invariant);
  version-pinned manifests; `--bare` strips ambient config (existing); SAST/DAST/dependency scanning in CI. An
  unsigned/unverified capability is **refused, never quarantined-but-active**.
- **D:** capability-registry growth unbounded → resource exhaustion. *Control:* spawn-cap + the existing single-writer
  RACI bound growth to manager-authorised hires only; growth is auditable (every add traces to an org event).

**C9 (NEW) — Cost-data integrity & spoofing.**
- **T (Tampering):** an agent inflates/deflates/hides spend to evade caps or frame a victim. *Control:*
  `UsageCostRecord` is append-only + RFC-6962 hash-chained (reuses `audit/`); cost is computed deterministically from
  provider-returned usage + a versioned price snapshot (an agent cannot author an arbitrary cost number — it's a pure
  function of attested usage); periodic provider-billing reconciliation surfaces any drift.
- **R (Repudiation):** disputed totals. *Control:* `cost_source` + `price_catalog_version` make every figure
  reproducible and reconcilable to the unit.
- **S (Spoofing):** mis-attributing spend to another role. *Control:* `requesting_role_id` is bound from the
  authenticated virtual key, not self-declared.

All new rows carry the existing standing invariants: fail-closed, least-privilege/no god-keys, hashes-not-PII in the
audit log, global kill-switch (agent-cannot-disable), append-only audit, propose-then-dispose.

---

## Part F — Test & Evidence Strategy

**Adversarial / property / fuzz / metamorphic tests (the suite must FIND flaws, §3.6):**

- **W1 modelgateway:** property tests on `model_selection_policy` (any candidate ordering + any availability subset → a
  valid, in-policy plan); metamorphic tests on `ensemble_quorum_reconciler` (permuting equal answers doesn't change the
  verdict; one corrupted answer can't flip a clear quorum); fuzz the response parser with malformed/partial provider
  JSON (must fail-closed, never emit a blank cost); red-team: a response claiming a model **not** in the selector's
  candidate set is refused; determinism over repeats. **Mutation-critical:** `model_selection_policy.py`,
  `cli_gateway_env_injection.py` (a mutated env-builder that drops the kill-switch or leaks a key must be killed).
- **W2 knowledge:** property tests on as-of-time queries (no answer ever reflects a fact written after T);
  cross-provider fidelity tests (B's retrieval == A's intended fact); fuzz the assembler with adversarial/injection
  content (untrusted facts are tagged, never elevated to trusted plan); determinism. **Mutation-critical:**
  `cross_model_context_assembler.py`.
- **W3 bootstrap:** stateful tests that run each step twice and assert the second run is a **no-op** (idempotency);
  crash-injection mid-step then resume → converges; degraded-mode tests (remove a key → platform stays up, that
  capability fails closed). **Mutation-critical:** `degraded_mode_policy.py` (a mutant that turns a fail-closed degrade
  into a hard block, or worse, an open fallback, must be killed).
- **W4 capabilities:** property tests that the registry's current set == pure replay of the growth log for **any**
  sequence of hire/auto-create/rescope/fire; combinatorial growth tests (thousands of synthetic hires → no ceiling, no
  duplicate `capability_id`, gapless seq); hash-chain tamper tests; generality tests (arbitrary charter
  responsibilities → correct keyword surface, no special-casing). **Mutation-critical:**
  `org_event_to_capability_projection.py`, `capability_growth_log.py`.
- **W5 cost:** **zero-numerical-error** property tests on `exact_cost_computation` (Decimal exactness over wide ranges
  incl. cache/reasoning tokens; boundary-exact on/just-over/just-under cost caps); reconciliation drift == 0 over
  multi-provider synthetic billing exports; hash-chain tamper tests; spoofing red-team (an agent can't author a cost
  number). **Mutation-critical:** `exact_cost_computation.py`, `append_only_cost_ledger.py`,
  `provider_billing_reconciliation.py` — target ≈100% mutation score.

**Efficacy / quality tests (prove the system is GOOD, not just bug-free, §3.6):**
- W1: functional correctness vs the golden expected outputs ≥ CLI-only baseline; failover success rate;
  cost-attribution exactness.
- W2: retrieval precision/recall@k vs ground truth with error bars; coordination-task success rate.
- W4: "org-evolution" efficacy — given N hires, the routable capability surface grows correctly and the front-desk
  router resolves new requests to the new roles (end-to-end through `front_desk_request_router.py`).
- W5: ledger total == provider-reported total to the unit, across 1 and 100s of models.

**Evidence showcase (`evidence/`, analysis-only deps fenced by import-linter):**
- **W1:** model-selection flow diagram (B&W, HTML+PNG); failover behaviour graph; latency-distribution +
  cost-per-use-case bars.
- **W2:** the knowledge-graph rendered as the Obsidian-style view (PNG); retrieval precision/recall with CIs;
  coordination-success heatmap.
- **W3:** bootstrap flow diagram (B&W); clean-clone-to-green timing; idempotency proof (run-twice = no-op) chart.
- **W4 (headline):** the **capability-growth timeline** (PNG+interactive HTML), the **live role→capability graph**
  (B&W, regenerated from the registry), the **org-evolution replay** showing the surface growing frame-by-frame, and
  the capability inventory table.
- **W5:** ledger-vs-billing reconciliation (zero-drift) chart; exactness proof; per-role/per-model spend rollups.
- **Whole-system:** an updated overall B&W architecture diagram showing the single egress plane and the new boundaries
  — extends the existing whole-system diagram already in `evidence/`.

All graphs PNG + interactive HTML; all flow diagrams aesthetic B&W HTML + PNG; statistics to a peer-reviewed standard
(means ± CIs, hypothesis tests where applicable). One-command regeneration (the repo already has a `run_all` evidence
regenerator to extend).

---

## Part G — Risks & "Never Hits Blockers"

Top risks to an unattended autonomous build, each with an idempotent / self-healing / fail-closed-but-graceful
mitigation:

1. **A missing/invalid API key hard-blocks the platform.** *Mitigation:* `degraded_mode_policy.py` prunes that
   provider's candidates and continues on the others; if *all* providers for a use-case are unavailable, that use-case
   fails closed (refuses, audited) while the rest of the platform stays up. A missing key is **never** a hard stop for
   the whole platform — it's a scoped, loud, audited capability degrade (G's explicit requirement).
2. **Gateway becomes a single point of failure (it is now the one egress).** *Mitigation:* run it as a supervised,
   auto-restarting local process via the W3 bootstrapper; provider-level failover inside `model_selection_policy`; a
   documented CLI fallback to direct-to-Anthropic with an audited downgrade event. The kill-switch remains out-of-band
   and agent-cannot-disable.
3. **Quota/usage exhaustion stops the run.** *Mitigation:* the existing `CLAUDE.md §4.8` resilience watchdog
   (idempotent, "do nothing if a run is in progress or complete", OS-level scheduler option) auto-resumes from git +
   task list + roadmap when usage returns — unchanged and reused.
4. **Setup drifts between Windows dev box and Linux CI.** *Mitigation:* the bootstrap pipeline runs identically via
   `python -m ...` (the Makefile already enforces this); idempotent steps converge to the same desired state on both;
   the doctor report names exactly what differs.
5. **Cost price catalog goes stale → silent over/under-charging.** *Mitigation:* `price_catalog_version` is stamped on
   every record; provider-billing reconciliation surfaces any drift as a stop-and-fix; prefer provider-reported cost so
   a stale map only affects the fallback path.
6. **Capability registry grows unbounded / accrues malicious capabilities.** *Mitigation:* growth is bounded to
   manager-authorised org events (reuses single-writer RACI + spawn cap); dynamic capability loading is
   signed/verified/least-privilege/fail-closed; every add is audited and traces to an org event.
7. **A mutation survivor or RED North Star finding ships silently.** *Mitigation:* `make test` is fail-fast/fail-closed
   and the mutation gate fails on **any** survivor (verified in `Makefile` + `scripts/run_mutation_gate.py`); North
   Star RED is stop-and-fix before new feature work (§4.7). CI is Linux-only today — the mutation full-pass enforcement
   plane is CI (verified), so the gateway/cost modules' mutation runs must be wired into `.github/workflows/ci.yml` (a
   Phase-4 task; tracked as required-change #4 in [`gate1-decisions.md`](gate1-decisions.md)).
8. **A loser experiment branch lingers (graveyard).** *Mitigation:* every W1/W2/W5 bake-off deletes the losing branch
   in the same change that merges the winner; the North Star review explicitly grades branch hygiene.

---

## Critical Files for Implementation

- `src/autofirm/substrate/powershell_claude_launcher.py` — reconcile the CLI substrate with the gateway via
  point-of-use env-injection (`ANTHROPIC_BASE_URL` / `ANTHROPIC_AUTH_TOKEN` / discovery) and a new optional `--model`
  on `LaunchSpec`; the one surgical edit on the existing egress path.
- `src/autofirm/frontdoor/role_capability_index.py` — re-point capability derivation from the static org tuples to the
  new `capabilities/live_capability_registry.py`; this is where the locked-in list is actually retired.
- `src/autofirm/org/org_lifecycle_engine.py` — the source of `OrgEventKind` lifecycle events that
  `org_event_to_capability_projection.py` subscribes to so the capability registry grows automatically as the org
  hires/promotes/evolves.
- `src/autofirm/foundation/money/exact_money_arithmetic.py` — the exact-`Decimal` core that makes W5 cost computation
  zero-numerical-error and exact-to-the-unit.
- `src/autofirm/e2e/public_company_scenarios.py` + `src/autofirm/e2e/operate_platform_checks.py` — the hardcoded
  scenario tuples and ~60 fixed feature checks to retire (no graveyard) once the dynamic registry is wired, and to
  re-base on demonstrating *growth* rather than a fixed feature list.

(Supporting boundaries to mirror, not edit: `substrate/session_launcher_protocol.py` for the Protocol+Fake pattern;
`memory/agent_memory_layer.py` for the pluggable W2 base; `access/credential_broker.py` / `secret_source_protocol.py`
for per-provider virtual-key minting; `audit/rfc6962_hashing.py` for the cost + capability hash chains;
`docs/threat-model.md` + `docs/architecture/data-contracts.md` for Gate-1 ratification.)
