# AutoFirm Threat Model — Per-Component STRIDE Matrices (Gate-2 v1)

> Companion to `threat-model.md` (the index + standing invariants + residual register). This file holds the
> full STRIDE enumeration per component / trust boundary, grounded in the ratified Gate-2 architecture and the
> A6/A7/A8 research syntheses. Every threat names a **specific** mitigating control with its citation. Controls
> are **fail-closed** (CLAUDE.md §5.6); the audit log stores **hashes/lineage, never raw PII** (T1); Claude Code
> **hooks are fail-OPEN — logging only, never the boundary** (T2). Cites: `overview.md`, `substrate.md`,
> `data-contracts.md`, `org-model.md`, `tension-resolutions.md`; research A6/A7/A8 SYNTHESIS.md.

Severity scale: **C**ritical / **H**igh / **M**edium / **L**ow (blast-radius × likelihood for an unattended,
money-spending, real-world-acting agent system).

---

## C1 — Claude Code CLI session substrate (A5)
The execution unit: `claude -p --bare --output-format json` headless sessions, roles as `.claude/agents/*.md`,
two-layer sandbox, `--resume` single-writer lease, `--fork-session` parallel branches.

| STRIDE | Threat | Control (cited) | Sev |
|---|---|---|---|
| **S** | A forged/replayed `session_id` resumes another role's worktree and inherits its authority | `--resume` bound to **single-writer lease** on the originating worktree (substrate §4); session actor is an attested **SPIFFE id**, not the raw session_id (data-contracts §5; A8.3) | H |
| **T** | Ambient hooks/MCP/settings drift mutate a production run, or a role file is edited to widen tools | `--bare` strips ambient hooks/MCP; **version-pinned** settings/mcp-config/agents manifests make a run replayable (substrate §1); role `tool_grants` are managed-scope deny-first (substrate §2) | H |
| **R** | "Which session did this?" — a side-effect with no provable origin | JSON envelope returns `session_id` + `total_cost_usd` captured into the **append-only audit log** via the A8 gateway path, not via the fail-open hook (substrate §1, §3; T2) | M |
| **I** | Cross-agent context leakage; a subagent reads another role's secrets/transcript | **Two-layer OS+container/VM sandbox** mirrored by permission deny-rules; cross-agent context-leakage tests are a substrate test hook (substrate §3, §7; A7 §3) | H |
| **D** | Runaway `--fork-session` fan-out exhausts compute/spend | **Fixed depth-5 nesting cap** + A1 ~3–4-per-cluster routing cap; `total_cost_usd` is a first-class metric feeding graduated containment (substrate §2; A7 §4) | H |
| **E** | A subagent silently spawns subagents to escalate reach beyond its brief | **Subagents never silently spawn** — fan-out is an explicit orchestrator SPAWN request gated by governance (substrate §2; org-model §2.3; CLAUDE.md §3.1) | C |

**Note:** sandbox-escape is a named threat category (A7 §3 SoK) — sandbox is **never the sole control**; the A8
gateway + SPIFFE creds are the egress boundary. Container-vs-VM is a deferred L2 build choice (substrate §8).

---

## C2 — Message / work-flow bus (A2, A3)
Typed, signed `MessageEnvelope` (FIPA-ACL + A2A Agent-Card + JWS + Anthropic delegation contract); deterministic
declared DAG default; Contract-Net for dynamic allocation; saga checkpoints for long-horizon work.

| STRIDE | Threat | Control (cited) | Sev |
|---|---|---|---|
| **S** | An agent forges a `sender`/`agent_card` to impersonate a privileged role | `sender`/`receiver` are **attested SpiffeIds**; **JWS `signature` verified before any action**; missing field → refuse (data-contracts §1; A2) | H |
| **T** | Envelope tampered in flight (intent/content/boundaries altered) | **JWS tamper-evidence verified before action**; `vocabulary_version` pin prevents ontology-confusion; `trace_id` joins audit+lineage (data-contracts §1) | H |
| **R** | An agent denies sending a consequential `request` | Every envelope carries `conversation_id` + `trace_id` recorded into the A6 audit/PV lineage; provenance is the why-record (data-contracts §1, §3; A6.1) | M |
| **I** | Untrusted ingested content smuggled through `content` becomes an instruction (indirect prompt injection — PRIMARY vector) | **Deterministic DAG routing is the default — LLM-mediated routing forbidden for structured flows** (T5); dual-LLM/CaMeL keeps untrusted data out of control flow (overview §2.5; A8.1; A7 §3) | C |
| **D** | Message flooding / orphan messages / non-terminating saga loops | Saga **checkpointed phases + idempotent replay log**; "no orphan messages, every forward action has a compensator" invariant; gateway throttling (data-contracts §4; A8.1 §02) | H |
| **E** | A worker uses Contract-Net bidding to award itself out-of-scope work | Contract-Net is **announce→bid→award under the orchestrator**, permitted only for dynamic allocation; `boundaries` (autonomy_level, cost cap, deny-list) are required and validated (T5; data-contracts §1) | H |

---

## C3 — Append-only hash-chained audit log (A6, A6.4)
PROV-DM why-record + FHIR security-record, RFC-6962 leaf hashing, history-tree, Signed Tree Heads at gates.
Data layer **refuses UPDATE/DELETE**. Stores **hashes/lineage, never raw PII** (T1).

| STRIDE | Threat | Control (cited) | Sev |
|---|---|---|---|
| **S** | A record written under a spoofed actor identity | `agent` field = **attested SpiffeId** (A8.3); `act` delegation chain recorded for human→agent→tool lineage (data-contracts §3; A6.1) | H |
| **T** | Mid-log edit or record substitution | **Forward hash chain** (`prev_hash`/`record_hash`, RFC-6962 0x00 domain-sep) + **history-tree consistency proofs**; UPDATE/DELETE refused at the data layer (data-contracts §3; A6.2) | C |
| **R** | An action occurs with no durable record (repudiation via dropped log) | Record is written **through the A8 gateway mediation path which can fail closed** — refuse the action if the record cannot be written/sealed; **never depends on a fail-open hook** (T2; substrate §3; A6 veto) | C |
| **I** | Raw PII/client content leaks into the immutable, un-erasable log | **T1 data-separation invariant** — log stores hashes + lineage only; VF erasure purges memory/PV stores and writes a **tombstone**, never rewriting the chain (T1; data-contracts §3) | H |
| **D** | **Log truncation / delayed-detection** attack drops recent entries | **Signed Tree Heads at every gate + external anchoring** detect truncation/equivocation; forward-secure signing keys (A6.2 src 05/06; threat-model.md must name truncation — done) | H |
| **E** | A writer role gains power to seal/forge an STH | STH signing is a separate privilege (out of agent scope); read-only audit agent verifies inclusion/consistency proofs (A6.2, A6.3 src 09; A7 §4 detect layer) | M |

---

## C4 — Credential broker (SPIFFE identity + short-TTL secrets) (A8.3)
Mints per-session attested SPIFFE SVIDs + short-TTL, least-privilege, **sender-constrained** tokens at spawn-cap
rate. No standing/god-keys. OAuth scope-narrowing + RFC-8693 token exchange per hop.

| STRIDE | Threat | Control (cited) | Sev |
|---|---|---|---|
| **S** | A workload requests an identity it is not entitled to | **Attested SPIFFE SVID** fetched at runtime via Workload API (no standing secret); identity bound to `spiffe://<company>/agent/<role>/session/<id>` (A8.3 src 13; data-contracts §5) | H |
| **T** | A token's scope/audience is widened in flight | **RFC-8693 exchange-and-narrow** at each hop; tokens **audience-bound + sender-constrained (mTLS/DPoP)** so they cannot be re-scoped or replayed (A8.3 src 10/12) | H |
| **R** | Disputed "who held this credential when?" | **`act` delegation chain** recorded into the append-only audit (actor = SPIFFE id); credential issue/revoke is an audited event (A8.3 src 10; A6.1) | M |
| **I** | Secret leaks into a prompt, log, or transcript | Credentials **runtime-injected, never in prompts/logs**; auto-revoked at session end; "0 secrets in logs" is an A8 evidence target (A8.3; A8 evidence hooks) | C |
| **D** | Broker cannot mint at spawn-cap rate → stall, or is flooded | Broker **must mint at spawn-cap rate — validated as a substrate test** (T3 scaling constraint); fail-closed: no credential → no action, never a default-grant (T3; CLAUDE.md §5.6) | M |
| **E** | A leaked leaf-agent token grants broad or cross-audience power | **Least-privilege + audience-restricted + sender-constrained** → a leaked token is "useless if leaked"; **no god-keys** (A8.3 src 09/12/13; T3) | C |

---

## C5 — Integration / API gateway (PEP) (A8.1)
The **only** path to the outside world: TLS, OWASP-API validation, throttling, circuit breakers, audit; dual-LLM
+ CaMeL capability interpreter so untrusted input can never trigger consequential actions.

| STRIDE | Threat | Control (cited) | Sev |
|---|---|---|---|
| **S** | Outbound call to a spoofed/look-alike endpoint, or an unverified inbound caller | **mTLS** + **TLS-only egress with redirect allowlist**; gateway is the single ingress/egress PEP (A8.1 src 02/01) | H |
| **T** | Untrusted API response tampered/poisoned, mutating downstream behavior | **Validate-and-sanitize all external responses (untrusted-by-default)**; untrusted-by-default trust tag; provider-reputation shortcut **rejected** (A8.1 src 01) | H |
| **R** | An external effect with no provenance | Gateway **audits every external call** (what/when/who) into the A6 log; this is the fail-closed path, not the hook (A8.1 src 02; T2) | M |
| **I** | Data exfiltration via tool args / side-channel using untrusted-origin data | **CaMeL IFC/taint** — untrusted-origin data tagged, cannot become instructions or exfiltration args; **context-minimization** sends only the minimum (A7 §3; A8.1 src 03/04) | C |
| **D** | A flood of inbound/outbound calls exhausts quota/spend (API exhaustion) | **Throttling + circuit breakers + resource/time limits** at the gateway; graduated containment (warn→throttle→isolate→kill) (A8.1 src 01/02; A6.3 MI9) | H |
| **E** | Indirect prompt injection makes the agent invoke a high-risk tool it shouldn't | **Plan-Then-Execute control-flow integrity + least-privilege tool scopes + HITL challenge-response on irreversible actions** (separation of privilege: two keys) (A8.1 src 03/06; A7 §3/§4) | C |

---

## C6 — Per-company / tenant data isolation (Postgres RLS FORCE) (A8.2)
Pool model + RLS: `ENABLE + FORCE ROW LEVEL SECURITY`, `USING` + `WITH CHECK` on `tenant_id`, non-owner /
non-BYPASSRLS app role, per-transaction `app.current_tenant`. Schema-audit **fails the build** if absent.

| STRIDE | Threat | Control (cited) | Sev |
|---|---|---|---|
| **S** | A session sets a `tenant_id` it does not own to read another tenant | Tenant context set **per-transaction from the attested session**, not from request data; `WITH CHECK` blocks cross-tenant writes (A8.2 src 07/08; data-contracts §5) | H |
| **T** | Cross-tenant UPDATE/DELETE (write past the boundary) | `WITH CHECK` predicate blocks modification outside the tenant boundary; cross-tenant **IDOR matrix** (A C/R/U/D on B = 0 successes) proves it (A8.2 src 08/11) | C |
| **R** | Disputed which tenant a write belongs to | Every audit record carries **`tenant_id` (PS scoping)**; provenance ties the write to the tenant (data-contracts §3; A6.1) | L |
| **I** | One missing app-layer `WHERE tenant_id` clause leaks all tenants | **Isolation in the engine, not convention** — app-layer-filter-only is **rejected**; default-deny when no policy exists; **Silo** (DB-per-tenant) offered for heavy-compliance tenants (A8.2 src 08/11) | C |
| **D** | A heavy tenant starves others (noisy neighbor) | Per-tenant throttling at the gateway; Silo isolation for high-ACV/compliance tenants caps blast radius (A8.1 src 02; A8.2) | M |
| **E** | App connects as table owner / BYPASSRLS role and silently bypasses RLS | App **must connect as a non-owner, non-BYPASSRLS role with FORCE enabled**; **schema-audit test fails the build** otherwise (A8.2 src 07/08; data-contracts §5) | C |

---

## C7 — Global kill-switch (A7)
Deterministic, **out-of-band**, agent-cannot-disable. On trip: immediate stop + state capture + immutable log +
quarantine + rollback, propagating to all live subagents. The single config flag halts all external calls.

| STRIDE | Threat | Control (cited) | Sev |
|---|---|---|---|
| **S** | A rogue actor spoofs an "all-clear" to keep a contained agent running | Kill-switch is **deterministic + out-of-band**; the agent **never holds the kill credential** (A7 §4 src 08; T3; data-contracts §5) | C |
| **T** | An agent edits the kill policy / flag to neuter it | "Kill switches fail if the agent writes the policy" — therefore the flag is **out-of-band and agent-cannot-overwrite** (A7 §4 src 08) | C |
| **R** | Disputed whether/when a kill fired | Trip writes **immediate immutable log + state capture** into the append-only audit (A7 §4 src 08; A6.2) | M |
| **I** | State-capture snapshot leaks secrets/PII on shutdown | Snapshot follows the same hashes-not-PII discipline + PUBLIC/PRIVATE 4-gate scanner (T1; A6.4) | M |
| **D** | Kill propagation fails to reach a forked subagent → orphan keeps acting | **Layered shutdown propagates to all live subagents**; pre-execution gates (A7 §4 src 08); depth-5 cap bounds the propagation set (substrate §2) | H |
| **E** | A contained agent escalates to re-enable itself | Graduated containment (warn→throttle→isolate→kill) is enforced by the governance plane the agent cannot reach; out-of-band credential (A6.3 MI9; A7 §4) | C |

---

## C8 — Dynamic role spawn / hire path (A1.5, T3)
5-stage lifecycle (GAP-DETECT→ROLE-SPEC→SPAWN→ONBOARD→RETIRE). SPAWN is a **request** to the governance plane,
RACI-gated, fail-closed; broker mints fresh per-session SPIFFE id + short-TTL creds; role never holds the kill cred.

| STRIDE | Threat | Control (cited) | Sev |
|---|---|---|---|
| **S** | An agent self-spawns a privileged role to impersonate authority | **No agent unilaterally creates a role** — SPAWN is governance-gated by RACI decision-rights, fail-closed (T3; org-model §2.3; A7) | C |
| **T** | An under-specified or tampered `RoleSpec` widens scope | **Charter-completeness (MPS-collapse) gate** rejects under-specified roles; `tool_grants` least-privilege, SPIFFE-bound; missing required field → refuse (org-model §2.2; data-contracts §2) | H |
| **R** | Untraceable hire/fire ("who created this role?") | Every lifecycle transition is **decision-gated and audited**; RoleSpec status (DRAFT→ACTIVE→RETIRED) is queryable data (org-model §2; A6) | M |
| **I** | A retired role's credentials/memory linger and leak | RETIRE **deregisters identity (A8.3 revokes creds)** + harvests memory into A4 with VF-erasable provenance; **retire property test: zero orphaned artifacts** (org-model §2.5; T1) | M |
| **D** | Spawn loop explodes the roster (capability sprawl / fan-out DoS) | **Saturating spawn cap → P_eq equilibrium** + Graicunas span curve; broker mint-rate bounded; spawn-saturation test (org-model §2.3, §7; A7 §3 capability sprawl) | H |
| **E** | A new role grants itself broader tools than its brief, or two roles co-own one artifact | **Single-writer RACI invariant** — exactly one Accountable per artifact, disjointness is a build-failing test; spawn-time creds minted by broker, **never self-granted** (org-model §3; T3) | C |

---

## Coverage map
8 components × full STRIDE (S/T/R/I/D/E) = 48 enumerated threats, each with a cited fail-closed control.
Components: C1 substrate · C2 bus · C3 audit log · C4 credential broker · C5 API gateway PEP · C6 tenant RLS ·
C7 kill-switch · C8 dynamic spawn. Cross-cutting vectors from A7 §2 (indirect/direct prompt injection,
memory/RAG poisoning, tool abuse, privilege escalation, supply-chain, collusion, exfiltration) are each placed
on at least one component row above.
