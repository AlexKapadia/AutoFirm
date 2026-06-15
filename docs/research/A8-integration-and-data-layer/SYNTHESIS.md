# SYNTHESIS — A8 Integration & Data Layer (L1.A8.1 / L1.A8.2 / L1.A8.3)

> Branch A8, Layer-1 foundations. Covers external-tool/API integration & untrusted-input handling
> (A8.1), multi-tenant data isolation enforced in the data layer (A8.2), and secrets/credential
> scoping for autonomous agents (A8.3). 10 sources; one folder each. All claims cited to primary
> standards/peer-reviewed work; quantitative claims carry exact numbers + locators.

---

## L1.A8.1 — External-tool/API integration & untrusted-input handling

### Alternative space surveyed (with ADOPT/REJECT/DEFER)
Two distinct trust problems must both be solved: (i) **classical API consumption** (a service
calling another service/API) and (ii) **LLM-agent ingestion** (an agent reading untrusted content
and then acting via tools — prompt injection).

**(i) Classical API/untrusted-input defenses**
- **Validate-and-sanitize all external responses (untrusted-by-default)** — OWASP API10:2023 [#01]. **ADOPT** (core invariant).
- **API gateway as single ingress/policy point + mTLS + throttling + circuit breakers** — NIST SP 800-204 [#02]. **ADOPT** (the enforcement home).
- TLS-only egress + redirect allowlist + resource/time limits — OWASP API10:2023 [#01]. **ADOPT**.
- Provider-reputation trust shortcut — **REJECT** (OWASP explicitly warns against it [#01]).

**(ii) LLM-agent prompt-injection defenses** (full pattern menu from [#03]):
- **Action-Selector** — DEFER (adopt only for narrow fixed-action sub-tools; too rigid as default).
- **Plan-Then-Execute** — **ADOPT** as default control-flow-integrity layer.
- **LLM Map-Reduce** — **ADOPT** for batch untrusted-doc ingestion (isolates poisoned docs).
- **Dual LLM** — **ADOPT** for reading untrusted content (privileged orchestrator + quarantined reader + symbolic variables).
- **Code-Then-Execute** — DEFER (modest gain; subsumed by CaMeL).
- **Context-Minimization** — **ADOPT** as a cheap add-on.
- **CaMeL capability / control-vs-data-flow interpreter** — Debenedetti et al. [#04]; **ADOPT** as the non-LLM enforcement engine (solves **67% of AgentDojo tasks with provable security** [#04]).
- **LLM-only guardrails as the primary control** — **REJECT** (a guardrail LLM is itself injectable; "significant limitations against persistent attackers" [#06]).
- **Least privilege for tools + HITL for high-risk actions** — OWASP LLM cheat sheet [#06]. **ADOPT**.
- **Measurement:** AgentDojo (97 tasks, 629 security cases) [#05] is the golden-set/metric — defenses compete on experiment branches, measured here, not asserted.

### Recommendation (A8.1)
Layer defense-in-depth: **(a)** an **API gateway** [#02] as the mandatory ingress/egress point doing
TLS, validation [#01], throttling, audit; **(b)** an **untrusted-by-default trust tag** on every
value with the invariant "untrusted input can never trigger consequential actions" [#03]; **(c)** a
**dual-LLM + CaMeL-style non-LLM capability interpreter** [#03][#04] enforcing control/data-flow
separation; **(d)** **least-privilege tool scopes + HITL** for high-risk actions [#06]; **(e)**
graded continuously on **AgentDojo** (+ AutoFirm-added, panel-diverse tasks) [#05]. No single
pattern is trusted alone.

---

## L1.A8.2 — Multi-tenant data isolation (data-layer, not convention)

### Alternative space surveyed
- **Silo** (DB-per-tenant) — highest isolation, highest cost; **ADOPT for heavy-compliance/high-ACV** clients.
- **Bridge** (schema-per-tenant) — logical isolation + customization; DEFER (useful middle option).
- **Pool** (shared tables, tenant_id) + **Row-Level Security** — **ADOPT as default** [#07][#08].
- **App-layer WHERE tenant_id filter only** — **REJECT as sole control** (one missing clause leaks all tenants).

### Engine-enforced RLS, exact mechanics (primary: PostgreSQL docs [#08], corroborated by AWS [#07])
- On ENABLE ROW LEVEL SECURITY, "If no policy exists ... a **default-deny** policy is used" [#08] — fail-closed.
- Policy must specify **BOTH USING (visibility/filter) and WITH CHECK (modification/block)** [#08] so a tenant can neither read nor write outside its boundary.
- "**Superusers and roles with the BYPASSRLS attribute always bypass** the row security system" and "**Table owners normally bypass** row security ... unless ... **FORCE ROW LEVEL SECURITY**" [#08]. So the app MUST connect as a **non-owner, non-BYPASSRLS** role with FORCE enabled [#07][#08].
- Tenant context via current_setting('app.current_tenant') set per transaction (SET LOCAL for pgBouncer safety) [#07].

### Recommendation (A8.2)
Default to **Pool + Postgres RLS with ENABLE+FORCE, USING+WITH CHECK on tenant_id, a restricted
non-owner app role, and per-transaction tenant context** [#07][#08] — isolation lives in the engine,
satisfying CLAUDE.md §5.6 "data layer, not convention." Offer **Silo** for heavy-compliance tenants.
A schema-audit test fails the build if any tenant table lacks these invariants.

---

## L1.A8.3 — Secrets & credential scoping for autonomous agents

### Alternative space surveyed
- **Standing/shared god-keys** — **REJECT** (anti-pattern 800-207 exists to kill [#09]).
- **Per-session, least-privilege, time-bound credentials** (ZTA) — **ADOPT** [#09].
- **Dynamic policy (PE/PA/PEP)** evaluating each consequential access by context — **ADOPT** [#09].
- **OAuth scopes** (RFC 6749 §3.3) for third-party integrations — **ADOPT** [#10].
- **Token Exchange** (RFC 8693) to narrow scope + set audience across each agent->tool hop — **ADOPT** [#10].
- **act (actor) delegation claims** for auditable human->agent->tool lineage — **ADOPT** [#10].
- **Capability-based data-flow control** over what a credentialed tool may do with data — **ADOPT** (CaMeL [#04]).

### Recommendation (A8.3)
A **secrets_broker** issues **per-session, least-privilege, short-TTL** credentials (ZTA tenet
[#09]), runtime-injected (never in prompts/logs), auto-revoked at session end. For third-party APIs,
request **minimal OAuth scopes** [#10] and **exchange-and-narrow** tokens at each hop [#10] so a
compromised leaf agent never holds full upstream authority. Record the **act delegation chain**
[#10] into the append-only audit (A6). Pair with the **capability interpreter** [#04] so scope is
enforced not just at issuance but on every data flow.

---

## Cross-cutting integration (one fail-closed system)
The three sub-questions converge on **one enforcement spine**: the **API gateway** [#02] is the
ingress/egress PEP; the **non-LLM capability interpreter** [#04] tags every value with
provenance/tenant/sensitivity and blocks disallowed flows; **RLS** [#07][#08] enforces the tenant
boundary in the database; the **secrets broker + token exchange** [#09][#10] guarantee per-session
least privilege; and **AgentDojo** [#05] measures the injection-robustness of the whole. Every layer
is **deny-by-default / fail-closed** (CLAUDE.md §5.6) and **industry/size-agnostic** (B12 panel-safe).

## Evidence/metric hooks (for evidence/)
- AgentDojo robustness/utility curve per candidate A8.1 defense (target: beat the 67% provable-secure baseline [#04]).
- RLS schema-audit pass-rate (must be 100% of tenant tables: ENABLE+FORCE+USING+WITH CHECK+non-owner role).
- Credential-scope tests: 0 credentials usable outside session/scope; 0 secrets in logs.

## Source independence check (DEPTH-RUBRIC §1)
- A8.1 untrusted-input invariant: OWASP [#01] + NIST 800-204 [#02] + Beurer-Kellner et al. [#03] + Debenedetti et al. [#04] + OWASP LLM [#06] — 5 independent orgs (>= 3, safety-critical: PASS).
- A8.2 RLS bypass/FORCE behavior: PostgreSQL primary [#08] + AWS [#07] — primary + independent corroboration (PASS).
- A8.3 per-session least-privilege + scope narrowing: NIST 800-207 [#09] + IETF RFC 6749/8693 [#10] (+ CaMeL capabilities [#04]) — independent standards bodies (PASS).

## Open items / re-verify before L2
- CaMeL interpreter internals: re-read arXiv:2503.18813 v2 PDF §3-4 before quoting verbatim (the 67%/capability/control-flow claims ARE verified).
- pgBouncer transaction-pooling + SET LOCAL tenant context: validate empirically in L2.A8 build (caveat noted by [#07]).
- Non-human agent identity for OAuth: evolving area; confirm provider support per integration in L2.
