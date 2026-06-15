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
