# AutoFirm — Typed Data Contracts (Gate-2 v1, ratified)

> The typed contracts between components. Contracts are **fail-closed**: a missing required field is a
> refusal, never a default (A2, A4-WA, A8). Shapes are language-neutral; the build picks the encoding
> (typed JSON per A6's PROV-DM-as-JSON ruling — RDF/PROV-O rejected as heavy). Every contract cites
> the branch that proves it. Companion: `org-model.md` (role/lifecycle), `substrate.md` (session).

---

## 1. Message-bus envelope (A2)
Derived from FIPA-ACL + A2A Agent-Card + JWS signature + Anthropic 4-part delegation contract.
Missing any required field → **refuse (fail-closed)**.

```
MessageEnvelope {
  # FIPA-ACL core
  intent          : Performative            # REQUIRED, closed set: request|inform|propose|
                                            #   accept|reject|query|failure|verify (A2)
  sender          : SpiffeId                # REQUIRED, attested scoped identity (A8.3)
  receiver        : SpiffeId                # REQUIRED
  content         : DelegationContract|any  # REQUIRED
  vocabulary_version : SemVer               # REQUIRED (ontology/version pin, A2)
  conversation_id : Uuid                    # REQUIRED (thread)
  in_reply_to     : Uuid?                   # OPTIONAL
  reply_by        : Timestamp?              # OPTIONAL deadline

  # A2A capability + trust
  agent_card      : CapabilityHeader        # REQUIRED (declared capabilities/scopes)
  signature       : JwsSignature            # REQUIRED (tamper-evidence; verified before action)

  # provenance hook
  trace_id        : Uuid                    # REQUIRED (joins A6 audit + A4 PV lineage)
}

DelegationContract {                        # Anthropic 4-part (A2)
  objective       : string                  # REQUIRED  what + why
  output_format   : SchemaRef               # REQUIRED  typed stage-output contract
  tools_sources   : ScopedToolGrant[]       # REQUIRED  least-privilege (A8.3)
  boundaries      : Constraint[]            # REQUIRED  autonomy_level, cost cap, deny-list
}
```
**Coordination rule (A2, Mintzberg):** standardize the *typed stage output* (`output_format`),
specify WHAT not HOW; validate at every boundary.

---

## 2. Role spec — roles-as-data (A1.5)
The charter a manager writes to hire/re-scope a role. JCM 5-dimension + RACI single-writer.
Full lifecycle in `org-model.md`.

```
RoleSpec {
  role_id         : Uuid                    # REQUIRED
  title           : string                  # REQUIRED  self-documenting (CLAUDE.md §5.7)
  reports_to      : RoleId                  # REQUIRED  strict hierarchy (one manager)
  # JCM five dimensions (A1.5 src 03) — charter completeness gate (MPS-collapse test)
  skill_variety   : ScopeSpec               # REQUIRED
  task_identity   : Deliverable[]           # REQUIRED  whole, identifiable artifacts
  task_significance : string                # REQUIRED  why it matters in the flow
  autonomy_level  : 0..5                    # REQUIRED  A3 ladder; default 3
  feedback        : SignalSpec[]            # REQUIRED  how it learns it's on track
  # decision rights + single-writer invariant (A1.5 RACI)
  raci            : { accountable: ArtifactId[], responsible: ArtifactId[],
                      consulted: RoleId[], informed: RoleId[] }   # REQUIRED
  # exactly ONE Accountable owner per artifact across the whole org (single-writer lock)
  tool_grants     : ScopedToolGrant[]       # REQUIRED  least-privilege, SPIFFE-bound (A8.3)
  must_study      : ResearchRef[]           # REQUIRED  gate: onboarding blocks until acked (A1.5)
  report_spec     : ReportSpec?             # OPTIONAL  manager-defined output contract (org-model)
  status          : DRAFT|ACTIVE|RETIRING|RETIRED   # REQUIRED  lifecycle
}
```

---

## 3. Audit record — PROV-shaped + hash-chained (A6, A6.4, A3)
Two-record invariant (A6, FHIR split): a **why-record** (PROV-DM) and a **security-record**
(AuditEvent). Append-only; the data layer **refuses UPDATE/DELETE** (A6). Doubles as the A3 replay
log. Stores **hashes/lineage of sensitive data, never raw PII** (T1 ruling).

```
AuditRecord {
  seq             : u64                     # REQUIRED  monotonic, gapless
  prev_hash       : Hash                    # REQUIRED  chain link (RFC-6962 leaf, 0x00 domain-sep)
  record_hash     : Hash                    # REQUIRED  H(canonical(this record))
  # PROV-DM why-record (A6 src 01)
  entity          : EntityRef               # REQUIRED  what was acted on (hash/lineage, not raw PII)
  activity        : ActivityRef             # REQUIRED  what happened
  agent           : SpiffeId                # REQUIRED  who (actor = attested identity, A8.3)
  used / generated / wasDerivedFrom : Ref[] # PROV edges (lineage; joins A4 PV)
  # FHIR security-record (A6 src 02)
  outcome         : SUCCESS|DENY|ERROR      # REQUIRED  (DENY = fail-closed refusal logged)
  policy_decision : OpaDecisionRef?         # OPTIONAL  governance loop (A6 GAAT)
  timestamp       : Timestamp               # REQUIRED
  tenant_id       : TenantId                # REQUIRED  PS scoping (A8.2)
}

SignedTreeHead {                            # gate-time Merkle commitment (A6 src 06, RFC 6962)
  tree_size : u64, root_hash : Hash, signature : Signature, sealed_at : Timestamp
}
```
**Erasure rule (T1):** a VF deletion (A4) purges the memory store + PV-derived records and writes a
*new* tombstone AuditRecord; it **never rewrites or breaks the hash chain**.

---

## 4. Task / handoff / resume state — the saga checkpoint (A3)
Saved at every gate so any session can resume in a fresh context window without re-inferring the goal.

```
Checkpoint {
  checkpoint_id   : Uuid                    # REQUIRED
  goal_verbatim   : string                  # REQUIRED  stored EXACT; re-injected on resume
                                            #   (A3 src 07 goal-misgeneralization defense)
  autonomy        : { level: 0..5, scope, control, tool_access }   # REQUIRED (A3 src 02)
  # SagaLLM tri-state (A3 src 10)
  SA              : { worktree, git_commit, files }                # workspace anchor
  SO              : { saga_step, txn_log, reasoning }              # operation state
  SD              : { dependency_graph, compensators: Compensator[] }   # dependency state
  replay_log      : IdempotentEvent[]       # REQUIRED  every side-effect carries idempotency_key
  memory_snapshot : MemoryRef               # REQUIRED  A4 tier snapshot (RB rollback point)
}

Compensator {                               # Saga semantic undo (A3 src 08)
  forward_action  : ActionRef, undo : "revert-commit"|"delete-branch"|"cancel-order"|...
}

IdempotentEvent { idempotency_key : Uuid, effect : ActionRef, applied : bool }
```
**Invariant (A3):** no orphan messages; **every forward action has a registered compensator**;
replay never double-applies (idempotency key). Validated by a separate validation agent before the
checkpoint commits.

---

## 5. Identity, tenancy & credential contracts (A8)
```
SpiffeId        = "spiffe://<company>/agent/<role>/session/<id>"   # attested (A8.3)
ScopedToolGrant { tool: ToolRef, scopes: OAuthScope[], audience: SpiffeId,
                  ttl: Duration, sender_constrained: true }        # RFC 9700 / 8693 (A8.3)
TenantContext   = current_setting('app.current_tenant')           # per-txn RLS key (A8.2)
```
**RLS invariant (A8.2, A6.4):** every tenant table has `ENABLE + FORCE ROW LEVEL SECURITY`, a
`USING` (visibility) and `WITH CHECK` (modification) predicate on `tenant_id`, served by a
non-owner, non-`BYPASSRLS` app role. Schema-audit **fails the build** if any table lacks this.

---

## 6. Business-layer contracts (B-side) — deterministic formulae as typed functions
All exact, unit-tested, boundary-tight (CLAUDE.md §3.11). The cross-function handoff edges (T6, T7)
are made explicit here.

```
IndustryProfile { naics: Naics(2..6, required), gics: Gics?,                       # B12
                  axes: { b2b_b2c, regulated_tier, physical_digital } }
PlaybookSpine  = APQC.Category[13] × ProcessGroup × Process                        # B12 (invariant)
VariationPoint { mode: ON|OFF|OPT, requires: Predicate[], default, metrics: KPI[] } # B12
  # derive_playbook(profile) is DESIGN-TIME; fail-closed refuses unlawful variants

ODI            : Opportunity = Importance + max(Importance − Satisfaction, 0)       # B3 (Ulwick)
EVC            : WTP_ceiling = ReferenceValue + DifferentiationValue − SwitchingCost# B5
Lerner         : (P − MC) / P = 1 / |e|                                            # B5
CLV            : m · r / (1 + i − r)            # contractual; m = margin FROM B5    # B-fin (T6 edge)
Valuation      : range = triangulate(DCF_FCFF, relative_harmonic, residual_income) # B-fin (never point)
AccountingId   : assert A = L + E ; assert CFS ties cash-delta   # exact-to-cent fail-closed# B-fin/B15
Dilution       : ownership = investment / post_money_cap         # leverage band ← B-fin (T7)# B6
Graicunas      : C(n) = n(2^(n−1) + n − 1)                                          # B1 span curve
LittlesLaw     : L = λ · W   (CycleTime = WIP / Throughput)                         # B11 (distribution-free)
SLA            : { response, resolution, service_hours, priority = f(impact,urgency) }# B9 (ITIL)
HealthScore    : composite + rate-of-change alarm (trend-fire)                      # B9
```

### 6.1 Named cross-function edges (resolved per T6/T7; see `tension-resolutions.md`)
| Edge | Producer → Consumer | Payload |
|---|---|---|
| margin | **B5 EVC/price engine → B-fin CLV** | `m` (gross margin %) — T6 |
| valuation | **B-fin → B6 dilution** | enterprise/post-money value — T7 |
| leverage ceiling | **B-fin trade-off model → B6** | max debt capacity — T7 |
| eligibility predicates | **B10 legal → B6** | grant/RBF/venture-debt lawfulness — T7 |
| stage class | **B1 growth-cycle → B6** | round-stage classifier — T7 |
| GTM motion | **B7 → B8** | early-adopter vs mainstream segment flag |
| legal gate | **B5 pricing → B10** | discrimination + dynamic-pricing approval |
| support map | **B2 Porter Service → B9** | APQC Cat-5 customer-service handoff |

All edges are **typed contracts validated at the boundary** (fail-closed); none is an implicit
assumption (closes QA-REVIEW C1.3 / LAYER1-SIGNOFF §5.5).

---

# Part II — Gate-1 evolution contracts (RATIFIED, frozen for Phase-2 build)

> Ratified at Gate 1 from `evolution-plan.md` §A.3 and ADR-003. These are the **frozen Pydantic v2 contracts**
> the Phase-2 tracks implement field-by-field. **House-style invariants (binding on every model below):**
> `model_config = ConfigDict(frozen=True)`; **`Decimal` not `float` for any money/price**; money arithmetic
> reuses `foundation/money/exact_money_arithmetic.py` (existing — exact-to-the-cent, zero rounding error,
> CLAUDE.md §3.11); hash links reuse `audit/rfc6962_hashing.py` (`leaf_hash` / `node_hash`, 0x00/0x01 domain
> separation); **≤300 lines per source file**, module + field docstrings, inline `# fail-closed:` /
> `# least-privilege:` comments on every security-relevant line. **Fail-closed validation rule (every field):**
> a missing or ambiguous *required* field is a **refusal** (`ValueError` in a `@field_validator` /
> `@model_validator`), **never a silent default**. **Generality rule (binding):** no magic constants and no
> provider/company hard-coding — every contract works for *any* provider, *any* company, *any* use-case
> (CLAUDE.md §3.9). Closed `Literal`/enum sets are **extensible** (add a member), never a per-fixture special case.

## 7. Model-gateway contracts (`src/autofirm/modelgateway/`)

`ModelRef`, `UseCaseId`, `RoleId`, closed enums live in `model_reference.py`; the request/response/selector/usage
shapes in `model_invocation_contract.py`. `ModelSelector` is a **selection policy, not a model string** — the core
of "many models per use-case" (ADR-003 §3).

```
ModelRef {                                   # (provider, model_name) — provider-agnostic, no hard-coding
  provider   : str                # REQUIRED  fail-closed: non-empty, lower-cased identity (e.g. "anthropic")
  model_name : str                # REQUIRED  fail-closed: non-empty; never a default model picked silently
}
Message {
  role       : Literal["system","user","assistant","tool"]   # REQUIRED  closed set; refuse unknown role
  content    : str                # REQUIRED  fail-closed: refuse None (empty string is allowed, None is not)
  trust_tag  : Literal["trusted","untrusted"]   # REQUIRED  injection-tagging — untrusted content cannot
                                  #   become control flow (CaMeL/dual-LLM; threat-model C5/C5′ I-row).
                                  #   fail-closed: default-deny → if origin unknown, MUST be "untrusted"
}
ModelSelector {                              # SELECTION POLICY — pinned | preferred_with_failover | ensemble_quorum
  strategy   : Literal["pinned","preferred_with_failover","ensemble_quorum"]   # REQUIRED  refuse unknown strategy
  candidates : tuple[ModelRef,...]   # REQUIRED  ordered; @model_validator: len>=1 (fail-closed: empty → refuse);
                                  #   pinned ⇒ len==1 (refuse >1); failover/quorum ⇒ len>=1
  quorum     : PositiveInt | None    # REQUIRED-IFF strategy=="ensemble_quorum": @model_validator refuses if
                                  #   None when quorum, or set when not; refuse quorum > len(candidates)
}
ModelInvocationRequest {
  correlation_id     : UUID            # REQUIRED  joins audit (A6 trace_id) + cost ledger; refuse if absent
  requesting_role_id : RoleId          # REQUIRED  who is spending (W5 attribution); least-privilege: bound from
                                  #   the authenticated virtual key, NOT self-declared (threat-model C9 S-row)
  use_case           : UseCaseId       # REQUIRED  closed-set-extensible routing key; refuse unknown only if the
                                  #   selector policy demands a known use-case (else accept any non-empty id)
  model_selector     : ModelSelector   # REQUIRED  the policy above
  messages           : tuple[Message,...]   # REQUIRED  @model_validator: len>=1; each Message validated
  max_output_tokens  : PositiveInt     # REQUIRED  bounded work — no unbounded spend (fail-closed: refuse <=0)
  temperature        : Decimal         # OPTIONAL  default Decimal("0") (deterministic); refuse <0 or >2
  credential_ref     : ScopedCredentialReference   # REQUIRED  secret-FREE handle; least-privilege: the virtual
                                  #   key is resolved at point-of-use, never carried in the request
  kill_switch_token  : KillSwitchEpoch # REQUIRED  fail-closed: refuse the call if the epoch is tripped (C7)
}
ModelInvocationResponse {
  correlation_id : UUID            # REQUIRED  echoes the request exactly; refuse on mismatch
  served_by      : ModelRef        # REQUIRED  which model/provider actually answered (failover-aware)
  output         : Message         # REQUIRED  trust_tag of model output is "untrusted" by default (C5 T-row)
  usage          : TokenUsage      # REQUIRED  provider-RETURNED counts echoed verbatim (never locally guessed)
  finish_reason  : Literal["stop","length","tool_use","content_filter","error"]   # REQUIRED  closed set
  served_at      : Timestamp       # REQUIRED  injected clock (deterministic-testable), never wall-clock in core
}
```

**TokenUsage echo invariant.** `ModelInvocationResponse.usage` is the **provider-returned** `TokenUsage`
(§8 below) carried through unchanged — the gateway never substitutes a locally-computed count. This is the
single source the cost ledger trusts (W5: "trust provider usage over local tokenizers").

## 8. Cost-ledger contracts (`src/autofirm/costledger/`)

`TokenUsage`, `UsageCostRecord`, `PriceVector` in `usage_cost_record.py`; the versioned snapshot in
`price_catalog_contract.py`. **Money is `Money` (Decimal-backed via `exact_money_arithmetic`); never `float`.**

```
TokenUsage {                                 # provider-RETURNED counts ONLY (trust usage over local tokenizers)
  input_tokens       : NonNegInt    # REQUIRED  fail-closed: refuse <0
  output_tokens      : NonNegInt    # REQUIRED  fail-closed: refuse <0
  cache_read_tokens  : NonNegInt    # REQUIRED (default 0)  prompt-cache READ accounting (priced separately)
  cache_write_tokens : NonNegInt    # REQUIRED (default 0)  prompt-cache WRITE accounting (priced separately)
  reasoning_tokens   : NonNegInt    # REQUIRED (default 0)  reasoning-model output accounting (priced separately)
}
PriceVector {                                # the EXACT per-token prices applied — a frozen Decimal snapshot
  currency             : str        # REQUIRED  ISO-4217; fail-closed: cross-currency totals NEVER silently summed
  input_price          : Decimal    # REQUIRED  price per input token; refuse <0
  output_price         : Decimal    # REQUIRED  price per output token; refuse <0
  cache_read_price     : Decimal    # REQUIRED  per cache-read token; refuse <0
  cache_write_price    : Decimal    # REQUIRED  per cache-write token; refuse <0
  reasoning_price      : Decimal    # REQUIRED  per reasoning token; refuse <0
}                                   # ALL Decimal — a float here is an own-goal against §3.11; refuse non-Decimal
UsageCostRecord {                            # ONE immutable ledger row per invocation (append-only, hash-chained)
  correlation_id     : UUID         # REQUIRED  joins invocation + audit; refuse if absent
  requesting_role_id : RoleId       # REQUIRED  attribution (per-role/team/use-case/company rollups)
  use_case           : UseCaseId    # REQUIRED
  served_by          : ModelRef     # REQUIRED
  usage              : TokenUsage   # REQUIRED  the provider-attested counts
  unit_prices        : PriceVector  # REQUIRED  the exact prices applied (frozen snapshot)
  cost               : Money        # REQUIRED  EXACT Decimal via exact_money_arithmetic; recomputation MUST
                                  #   equal f(usage, unit_prices) to the unit (zero numerical error, §3.11)
  cost_source        : Literal["provider_reported","price_map_computed"]   # REQUIRED  provenance of the number:
                                  #   provider_reported = provider's own cost figure (PREFERRED when available);
                                  #   price_map_computed = fallback computed from the versioned snapshot
  price_catalog_version : SemVer    # REQUIRED  which price snapshot was used (reconcilable; stamped on every row)
  recorded_at        : Timestamp    # REQUIRED  injected clock
  prev_hash          : Hash         # REQUIRED  RFC-6962 chain link to the previous ledger row (leaf_hash, 0x00)
  record_hash        : Hash         # REQUIRED  H(canonical(this record)); tamper-evidence (C9 T-row).
}                                   #   @model_validator: record_hash MUST equal the canonical hash → refuse mismatch
```

**`price_catalog_contract` (the versioned, frozen snapshot):**

```
PriceCatalog {
  version           : SemVer        # REQUIRED  SemVer; a price-shape-breaking change is a MAJOR bump
  source_pin_sha    : Hash          # REQUIRED  the commit SHA of the pinned upstream catalog snapshot
                                  #   (LiteLLM model_prices_and_context_window.json) — frozen in-repo, item 5
  prices            : Mapping[ModelRef, PriceVector]   # REQUIRED  per-model price vectors; refuse empty
  effective_at      : Timestamp     # REQUIRED  when this snapshot became authoritative
}                                   # frozen=True; an update is a deliberate, version-bumped, reconciled change —
                                  #   NOT an in-place edit (item 5). Lookup miss → fail-closed refuse, never $0.
```

**Cost-computation invariant (item 4, item 6).** `exact_cost_computation.py` is the pure function
`(TokenUsage, PriceVector) -> Money`, summed per token-class via `exact_money_arithmetic` (no `float`, no
intermediate rounding). When `cost_source == "provider_reported"` the provider's figure is the cost of record and
the computed figure is the reconciliation cross-check; when `"price_map_computed"` the computed figure IS the cost.
These three modules — `exact_cost_computation.py`, `append_only_cost_ledger.py`,
`provider_billing_reconciliation.py` — are **mutation-critical** (CI mutation gate, item 4).

## 9. Capability-registry contracts (`src/autofirm/capabilities/`)

`CapabilityDescriptor` in `capability_descriptor.py`; the append-only growth event in
`capability_registry_event.py`. Replaces the locked-in static capability list (no graveyard — item 3).

```
CapabilityDescriptor {                       # ONE advertised capability of the LIVE org
  capability_id      : CapabilityId   # REQUIRED  stable identity; refuse if absent
  name               : str            # REQUIRED  self-documenting ("own paid acquisition"); refuse empty
  keywords           : frozenset[str] # REQUIRED  routing surface; @field_validator: refuse empty set
                                  #   (fail-closed: an unroutable capability is a defect, not a default)
  owning_role_id     : RoleId         # REQUIRED  single-writer link — exactly one owning role
  required_clearance : str            # REQUIRED  least-privilege: NO default; a deny-by-default sentinel
                                  #   must be set explicitly — an unset clearance is a refusal
  provenance         : CapabilityProvenance   # REQUIRED  WHY it exists (hire/promote/auto_create + gap ref)
  maturity           : Literal["proposed","active","deprecated"]   # REQUIRED  lifecycle; refuse unknown
}
CapabilityRegistryEvent {                    # append-only growth log — HOW growth is recorded AND shown
  seq            : NonNegInt        # REQUIRED  monotonic, GAPLESS; @model_validator: refuse a gap vs prev seq
  kind           : Literal["CAPABILITY_ADDED","CAPABILITY_PROMOTED",
                           "CAPABILITY_DEPRECATED","CAPABILITY_RESCOPED"]   # REQUIRED  closed set
  descriptor     : CapabilityDescriptor   # REQUIRED  the POST-event state of the capability
  triggered_by   : RoleId           # REQUIRED  the managing role whose lifecycle action caused growth;
                                  #   least-privilege: NOT self-grant — only a managing role authors growth
  org_event_ref  : OrgEventId       # REQUIRED  link back to the org-lifecycle event (hire/auto_create)
  rationale      : str              # REQUIRED  PII-FREE 'why' (audited); refuse empty
  occurred_at    : Timestamp        # REQUIRED  injected clock
  prev_hash      : Hash             # REQUIRED  RFC-6962 chain link to the previous event (leaf_hash, 0x00)
  record_hash    : Hash             # REQUIRED  H(canonical(this event)); tamper-evidence (reuses audit/)
}                                   #   @model_validator: record_hash MUST equal the canonical hash → refuse mismatch
```

**Registry invariants.** The growth log is the **source of truth** for "show the evolution";
`live_capability_registry.py` derives the *current* set from the gapless log + live `OrgState`, and
`role_capability_index.py` / the operate-platform checks are **re-pointed** to read it (the surgical edit that
retires the static tuples without a graveyard — item 3). Growth is bounded by the existing spawn-cap +
single-writer RACI; every add traces to an org event (`org_event_ref`).
