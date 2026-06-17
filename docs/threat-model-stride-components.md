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

---

# Gate-1 evolution deltas (RATIFIED) — C5′ / C4′ / C8′ / C9

> Ratified at Gate 1 from the B6 egress/supply-chain digests and ADR-003. These EXTEND (not replace) C4 / C5 / C8
> and ADD C9. Same house format: every threat names a **specific** cited fail-closed control; the audit log stores
> **hashes/lineage, never raw PII** (T1); hooks are **fail-OPEN — logging only, never the boundary** (T2). Sources
> are B6 research folder slugs (under `docs/research/B6-egress-and-supplychain-threats/`) plus the existing A7/A8
> syntheses. Grounded in the existing code seams `access/credential_broker.py` and `access/secret_source_protocol.py`
> (fail-closed issuance, env/secret-manager-only source, `RedactedSecret`) — the deltas describe the controls those
> seams satisfy at multi-provider scale, not a parallel mechanism.

## C5′ — Model-egress gateway as the single outbound chokepoint (extends C5 / A8.1; ADR-003)
The gateway is the **only** path to model providers and the outside world: TLS, OWASP-API validation, throttling,
circuit breakers, dual-LLM/CaMeL capability interpreter, audit. Because it is the *single egress*, its
**availability** is itself a primary threat surface for an unattended run. **Degraded-mode principle (binding):**
the gateway being down **fails the affected capability closed, never blocks the whole platform** — CLI agents are
Anthropic-only and **fail static to direct-to-Anthropic with a loud audited downgrade**; programmatic any-model
traffic **fails that capability closed**.

| STRIDE | Threat | Control (cited) | Sev |
|---|---|---|---|
| **S** | A spoofed/look-alike provider endpoint, or a forged "gateway-healthy" signal, keeps traffic flowing to an attacker | **mTLS + TLS-only egress with redirect allowlist** on every provider hop; the health/degrade signal is **out-of-band and not agent-assertable** (same posture as the kill-switch) (A8.1 src 02; B6 `safely-interruptible-agents`) | H |
| **T** | A poisoned provider/router response (or tampered route table) silently redirects spend to a costlier/attacker model | **Validate-and-sanitize all external responses (untrusted-by-default)**; route/price tables are **version-pinned** snapshots, not provider-asserted at call time (A8.1 src 01; B6 `owasp-api4-resource-consumption`) | H |
| **R** | An egress side-effect with no provable origin during a degraded/fallback window | Gateway **audits every external call** (what/when/who) into the C3 log via the fail-closed path; the direct-to-Anthropic fallback emits a loud **`egress.downgrade`** audit event so the degraded window is fully attributable (A8.1 src 02; T2) | M |
| **I** | Untrusted-origin data exfiltrated through tool/model arguments on the one channel everything funnels through | **CaMeL IFC/taint + context-minimization** — untrusted-origin values cannot become exfiltration args; **taint travels with the value across agent hops** (A8.1 src 03/04; B6 `camel-defeating-prompt-injection-by-design`, `dual-llm-pattern-willison`) | C |
| **D** | **SINGLE-EGRESS DoS / cascading failure** — the gateway overloads, crashes, or is flooded and *every* agent in an unattended run stalls behind it (whole-platform SPOF) | **Graceful degradation + load shedding + backoff-with-jitter + retry budgets + circuit breakers** (B6 `google-sre-cascading-failures`); per-operation throttling + spend caps (B6 `owasp-api4-resource-consumption` API4:2023); **supervised auto-restart with a MaxR-in-MaxT restart-intensity cap** so a crash-loop escalates to the kill-switch rather than thrashing (B6 `erlang-otp-supervision-trees`); **degraded-mode is fail-static, not fail-stop** — CLI/Anthropic traffic → direct-to-Anthropic with a loud audited downgrade; programmatic any-model traffic → fail that capability closed; *never* a whole-platform block | **C** |
| **E** | Indirect prompt injection makes an agent invoke a high-risk egress (spend/outreach/tool) it shouldn't, abusing the single chokepoint's reach | **Plan-Then-Execute control-flow integrity (P-LLM plans before untrusted data is seen) + least-privilege tool scopes + HITL challenge-response on irreversible actions**; `ModelSelector.candidates` is a closed allowed-set per use-case (A8.1 src 03/06; data-contracts §7) | C |

**Degraded-mode note (the load-bearing D-row).** Google SRE Ch. 22 frames cascading failure as positive-feedback
overload whose canonical defenses are load shedding, graceful degradation, backoff+jitter, retry budgets, deadline
propagation, and circuit breaking. Applied to a single egress, AutoFirm splits by capability — **(a)** Anthropic-only
CLI traffic has a **fail-static** fallback (direct-to-Anthropic) gated by a loud `egress.downgrade` audit event and
the same out-of-band trust signal as the kill-switch; **(b)** any traffic that *requires* the gateway's
routing/IFC/policy (programmatic any-model) **fails that capability closed** (no silent CaMeL-bypassing direct call).
Gateway restart is OTP-supervised with a restart-intensity cap that escalates to the kill-switch / overseer rather
than thrashing or silently degrading forever. **No operator intervention required — unattended-safe.**

## C4′ — Multi-provider secret management at scale (extends C4 / A8.3; `credential_broker.py`)
The broker now mints credentials for **many providers**. The new surface is **blast radius across providers**: a
key spanning providers, or a leaked session token reusable elsewhere, turns one compromise into many.

| STRIDE | Threat | Control (cited) | Sev |
|---|---|---|---|
| **S** | A workload requests a provider identity it is not entitled to (cross-provider impersonation) | **Attested SPIFFE SVID per session** via the Workload API — the workload holds *no standing token* and proves identity through node+workload attestation before any SVID issues (A8.3 src 13; B6 `spiffe-spire-workload-identity`) | H |
| **T** | A token's scope/audience is widened in flight to reach a second provider | **RFC-8693 token exchange is downscope-only** — each hop narrows scope/resource/audience, never widens; a token minted for provider A is audience-rejected by provider B (A8.3 src 10; B6 `rfc-8693-oauth-token-exchange`) | H |
| **R** | Disputed "which provider credential was held when, by whom?" | **`act` delegation chain** recorded into the C3 audit; the broker already audits issuance + every authorize OK/DENY with **non-secret metadata only** (`credential_broker.py`; A8.3 src 10) | M |
| **I** | A provider secret leaks into a prompt, log, transcript, or shared-knowledge entry | **Secrets via env/secret-manager only**, wrapped `RedactedSecret` opaque from entry; broker audits metadata only; short-TTL auto-expiry caps the leak window; never in argv/prompt/log (`secret_source_protocol.py`; A8.3) | C |
| **D** | Broker cannot mint per-session creds at provider-spawn-cap rate → stall; or one provider's outage cascades into a mint storm | **Broker mint-rate is a substrate test (fail-closed: no credential → no action)**; **per-provider isolation = a bulkhead**, so one provider's failure is not a fleet-wide stall (B6 `google-sre-cascading-failures`; T3) | M |
| **E** | A leaked leaf-agent token grants broad or **cross-provider** power — one compromise spans all providers (god-key) | **No god-key spanning providers** — per-provider, per-session, least-privilege **short-TTL** SVIDs + **sender-constrained (DPoP)** tokens that are *"useless if leaked"* without the bound private key (A8.3 src 12/13; B6 `rfc-9449-dpop-sender-constrained-tokens`) | **C** |

## C8′ — Dynamic capability / skill supply-chain (extends C8 spawn-path & cross-cutting vector 6)
Agents can **load skills / MCP servers / tools at runtime**. The new surface is **supply-chain compromise of the
loaded artifact**: a poisoned skill executing attacker code, a malicious tool `description` injecting through the
tool channel, or a **rug-pull** (a server that passes audit then silently swaps its definition). House posture:
**signed + verified + least-privilege loading; refuse-NOT-quarantine on any verification miss (fail-closed).**

| STRIDE | Threat | Control (cited) | Sev |
|---|---|---|---|
| **S** | A malicious artifact masquerades as a trusted skill/MCP server (identity spoof) | **Verify signature + signer identity before load** — Sigstore keyless signing binds an OIDC identity and records it in the **Rekor append-only transparency log** (B6 `sigstore-artifact-signing`; OWASP LLM03:2025 Supply Chain) | H |
| **T** | The artifact is tampered between build and load, or its definition drifts after audit (**rug-pull / TOCTOU**) | **SLSA-provenance verify-before-load** (L2 signed provenance) + **version-pinned manifests** + **re-verify on EVERY load, not just install** — trust granted once does not bind later behavior (B6 `slsa-supply-chain-framework`, `mcp-tool-poisoning-rug-pull`; substrate §1) | **C** |
| **R** | "Where did this capability come from / who published it?" is unanswerable after an incident | Load events record the **artifact digest + signer identity + provenance attestation** into the C3 audit; the Rekor entry is an independent append-only witness (B6 `sigstore-artifact-signing`, `slsa-supply-chain-framework`) | M |
| **I** | A poisoned tool **`description`** is indirect prompt injection in the tool channel; the loaded skill reads/writes the shared-knowledge layer and exfiltrates | **Treat tool metadata as untrusted data** — it passes the CaMeL Q-LLM/IFC path, never the trusted plan; least-privilege scope on the loaded capability (B6 `mcp-tool-poisoning-rug-pull`, `camel-defeating-prompt-injection-by-design`; OWASP LLM01:2025) | **C** |
| **D** | A flood of dynamic loads, or a heavyweight/recursive skill, exhausts compute/spend | Load is **governance-gated (the C8 SPAWN request path, not self-service)**; per-load resource caps + the gateway's throttling/circuit-breakers bound the blast radius (B6 `google-sre-cascading-failures`, `owasp-api4-resource-consumption`; org-model §2.3) | H |
| **E** | A loaded skill widens its own privileges or executes code beyond its declared scope | **Least-privilege loading + minimum required SLSA level per capability class**; **refuse-not-quarantine** on any signature/provenance/version miss — an unverified artifact is **never loaded into a sandbox "to inspect"**, it is refused (B6 `slsa-supply-chain-framework`, `sigstore-artifact-signing`; CLAUDE.md §5.6 fail-closed) | C |

## C9 — Cost-data integrity (NEW component; B5/B6, on the C3 audit substrate)
Cost is the budget-cap and kill-switch's primary input on an unattended run. The threat: a compromised/rogue agent
**inflates spend** (to frame a victim / exhaust a competitor's budget) or **hides spend** (to evade caps and keep
spending). **Control thesis (binding):** cost is **NEVER a number an agent can choose** — it is a deterministic
pure function of provider-**attested usage × a versioned price snapshot**, written **append-only + hash-chained**,
**independently reconciled** against the provider's billing/usage meter. **The spender is not the scorekeeper.**

| STRIDE | Threat | Control (cited) | Sev |
|---|---|---|---|
| **S** | A cost record is written under a spoofed actor, or self-reported usage is passed off as provider-attested | Usage is the **provider-attested meter** (provider usage/billing API), not an agent claim; cost actor is an **attested SPIFFE id**; `requesting_role_id` is **bound from the authenticated virtual key, not self-declared**; the **agent has no write path to the cost-of-record** (B6 `billing-reconciliation-internal-control`, `nist-sp-800-92-log-management`; A8.3) | H |
| **T** | An agent edits a cost figure, or recomputes cost with a different price to under/over-state it | **Cost = f(attested_usage, versioned_price_snapshot)** computed by the deterministic core (propose-then-dispose); the price snapshot is **immutable + versioned**; recomputation is reproducible to the unit (CLAUDE.md §3.11; B6 `billing-reconciliation-internal-control`; data-contracts §8) | **C** |
| **R** | An agent denies the spend it incurred, or claims a different total | Every cost event is provable via an **RFC-6962 inclusion proof** against a signed cost-tree head; the per-window total is a **Merkle-aggregated authenticated sum**, so the cap decision itself is provable (B6 `rfc-6962-certificate-transparency`, `crosby-wallach-tamper-evident-logging`; reuses `audit/rfc6962_hashing.py`) | M |
| **I** | The cost ledger leaks tenant/PII or sensitive deal context | **Hashes/lineage only (T1)**; ledger transit TLS, storage append-only/write-once, access least-privilege (B6 `nist-sp-800-92-log-management`) | M |
| **D** | **Silent cap evasion** — a compromised reporter quietly UNDER-reports or TRUNCATES its own spend so the enforcer sees a low total while spend continues (or OVER-reports to frame/DoS another tenant) | **History-tree consistency proofs defeat truncation** (a plain hash chain does NOT — entries can be dropped off the end); **signed cost commitments gossiped to independent auditors** (reconciler + enforcer + North-Star overseer) expose equivocation; budget cap is a provable authenticated aggregate, not a self-reported counter; **fail-closed: in the reconciliation window use the conservative (higher) of provisional vs reconciled cost** and trip containment on divergence (B6 `crosby-wallach-tamper-evident-logging`, `rfc-6962-certificate-transparency`, `billing-reconciliation-internal-control`) | **C** |
| **E** | A compromised component seals/forges a cost-tree head, or grants itself the reconciler role | **Cost-tree-head signing + reconciliation are a separate privilege the spending agent never holds** (segregation of duties); the **reconciler compares against the provider meter as source of truth** — the spender cannot become the scorekeeper (B6 `billing-reconciliation-internal-control` COSO SoD, `crosby-wallach-tamper-evident-logging`) | C |

---

## Coverage map
**12 components × full STRIDE (S/T/R/I/D/E) = 72 enumerated threats**, each with a cited fail-closed control.
Gate-2 base (48): C1 substrate · C2 bus · C3 audit log · C4 credential broker · C5 API gateway PEP · C6 tenant RLS ·
C7 kill-switch · C8 dynamic spawn. Gate-1 evolution deltas (24): C5′ model-egress gateway (single-egress DoS/SPOF +
degraded-mode) · C4′ multi-provider secrets (no god-key spanning providers) · C8′ dynamic capability supply-chain
(signed/verified/pinned, re-verify-every-load, refuse-not-quarantine) · C9 cost-data integrity (attested-usage ×
versioned-price, hash-chained + reconciled). Cross-cutting vectors from A7 §2 (indirect/direct prompt injection,
memory/RAG poisoning **with cross-agent fan-out amplification**, tool abuse, privilege escalation, supply-chain,
collusion, exfiltration) are each placed on at least one component row above.
