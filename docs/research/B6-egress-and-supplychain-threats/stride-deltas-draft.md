# AutoFirm Threat Model — B6 STRIDE Deltas (DRAFT for Gate-1 review)

> **Status: DRAFT.** Proposed per-component STRIDE rows for the *platform-evolution* surfaces that the existing
> Gate-2 matrices (`../../threat-model-stride-components.md`) do not yet fully cover. These deltas EXTEND, not
> replace, components **C4** (credential broker) and **C5** (integration/API gateway PEP), and ADD **C8'**
> (dynamic capability/skill supply-chain) and **C9** (cost-data integrity). Same house format: every threat
> names a **specific** mitigating control with its citation; controls are **fail-closed** (CLAUDE.md §5.6); the
> audit log stores **hashes/lineage, never raw PII** (T1); Claude Code **hooks are fail-OPEN — logging only,
> never the boundary** (T2). Sources cited by folder slug under `docs/research/B6-egress-and-supplychain-threats/`.
>
> **Grounded in the existing code seams:** `src/autofirm/access/credential_broker.py` (fail-closed issuance,
> least-privilege scope, append-only non-secret audit, `authorize` re-check) and
> `src/autofirm/access/secret_source_protocol.py` (env/secret-manager-only source, `RedactedSecret`,
> fail-closed on missing secret). The deltas below describe the controls these seams must satisfy at multi-provider
> scale; they do not invent a parallel mechanism.

Severity scale: **C**ritical / **H**igh / **M**edium / **L**ow (blast-radius × likelihood for an unattended,
money-spending, real-world-acting agent system). Sources: B6 research folders (slugs in parentheses).

---

## C5′ — Model-Egress Gateway as the single outbound chokepoint (extends C5 / A8.1)

The gateway is the **only** path to model providers (and the outside world): TLS, OWASP-API validation,
throttling, circuit breakers, dual-LLM/CaMeL capability interpreter, audit. Because it is the *single egress*,
its **availability** is itself a primary threat surface for an unattended autonomous run. **Degraded-mode
principle (binding here):** the gateway being down must **fail the affected capability closed, never block the
whole platform**. AutoFirm's CLI agents are **Anthropic-only** and may **degrade to direct-to-Anthropic with a
loud, audited downgrade event** (fail-static fallback); **programmatic any-model traffic** that genuinely needs
the gateway's routing/policy **fails that capability closed** while the gateway is unavailable.

| STRIDE | Threat | Control (cited) | Sev |
|---|---|---|---|
| **S** | A spoofed/look-alike provider endpoint, or a forged "gateway-healthy" signal, keeps traffic flowing to an attacker | **mTLS + TLS-only egress with redirect allowlist** on every provider hop; the health/degrade signal is **out-of-band and not agent-assertable** (same posture as the kill-switch — `safely-interruptible-agents`; A8.1 src 02) | H |
| **T** | A poisoned provider/router response (or tampered route table) silently redirects spend to a costlier/attacker model | **Validate-and-sanitize all external responses (untrusted-by-default)**; route/price tables are **version-pinned** snapshots, not provider-asserted at call time (`owasp-api4-resource-consumption`; A8.1 src 01) | H |
| **R** | An egress side-effect with no provable origin during a degraded/fallback window | Gateway **audits every external call** (what/when/who) into the C3 log via the fail-closed path; **the direct-to-Anthropic fallback emits a loud `egress.downgrade` audit event** so the degraded window is fully attributable (A8.1 src 02; T2) | M |
| **I** | Untrusted-origin data exfiltrated through tool/model arguments on the one channel everything funnels through | **CaMeL IFC/taint + context-minimization** — untrusted-origin values cannot become exfiltration args; taint travels **with the value across agent hops** (`camel-defeating-prompt-injection-by-design`; `dual-llm-pattern-willison`; A8.1 src 03/04) | C |
| **D** | **SINGLE-EGRESS DoS / cascading failure** — the gateway overloads, crashes, or is flooded, and *every* agent in an unattended run stalls behind it (whole-platform SPOF) | **Graceful degradation + load shedding + backoff-with-jitter + retry budgets + circuit breakers** at the gateway (`google-sre-cascading-failures`); per-operation throttling + spend caps (`owasp-api4-resource-consumption` API4:2023); **supervised auto-restart with a MaxR-in-MaxT restart-intensity cap** so a crash-loop escalates rather than thrashes (`erlang-otp-supervision-trees`); **degraded-mode is fail-static, not fail-stop:** CLI/Anthropic traffic degrades to **direct-to-Anthropic with a loud audited downgrade**, programmatic any-model traffic **fails that capability closed** — *never* a whole-platform block | **C** |
| **E** | Indirect prompt injection makes an agent invoke a high-risk egress (spend/outreach/tool) it shouldn't, abusing the single chokepoint's reach | **Plan-Then-Execute control-flow integrity (P-LLM plans before untrusted data is seen) + least-privilege tool scopes + HITL challenge-response on irreversible actions** (`camel-defeating-prompt-injection-by-design`; A8.1 src 03/06) | C |

**Degraded-mode mitigation, expanded (the load-bearing D-row note).** Google SRE Ch. 22 frames cascading
failure as *positive-feedback overload* whose canonical defenses are **load shedding, graceful degradation,
backoff+jitter, retry budgets, deadline propagation, and circuit breaking** (`google-sre-cascading-failures`).
Applied to a *single egress*: the failure of the chokepoint must not propagate to a total halt. AutoFirm splits
egress by capability — **(a)** Anthropic-only CLI traffic has a **fail-static fallback** (direct-to-Anthropic)
gated by a **loud `egress.downgrade` audit event** and the same out-of-band trust signal as the kill-switch, so
the convenience of central policy is lost but the run survives; **(b)** any traffic that *requires* the gateway's
routing/IFC/policy (programmatic any-model) **fails that capability closed** (no silent direct-call bypass of
CaMeL). The restart of the gateway itself is an **OTP-style supervised restart** with a restart-intensity cap
(`erlang-otp-supervision-trees`) so a crash-loop hits the cap and **escalates to the kill-switch / overseer**
rather than thrashing or silently degrading forever.

---

## C4′ — Multi-provider secret management at scale (extends C4 / A8.3)

The credential broker (`credential_broker.py`) now mints credentials for **many providers** (multiple model
APIs, registries, tool endpoints). The new surface is **blast radius across providers**: a key or token that
spans providers, or a leaked session token reusable elsewhere, turns one compromise into many.

| STRIDE | Threat | Control (cited) | Sev |
|---|---|---|---|
| **S** | A workload requests a provider identity it is not entitled to (cross-provider impersonation) | **Attested SPIFFE SVID per session** fetched via the Workload API — the workload holds *no standing token* and proves identity through node+workload **attestation** before any SVID is issued (`spiffe-spire-workload-identity`; A8.3 src 13) | H |
| **T** | A token's scope/audience is widened in flight to reach a second provider | **RFC-8693 token exchange is downscope-only** — each hop narrows `scope`/`resource`/`audience`, never widens; audience-binding means a token minted for provider A is rejected by provider B (`rfc-8693-oauth-token-exchange`; A8.3 src 10) | H |
| **R** | Disputed "which provider credential was held when, by whom?" | **`act` delegation chain** (RFC-8693) recorded into the C3 append-only audit; the broker already audits **issuance + every authorize OK/DENY** with non-secret metadata only (`credential_broker.py`; `rfc-8693-oauth-token-exchange`; A8.3 src 10) | M |
| **I** | A provider secret leaks into a prompt, log, transcript, or shared-knowledge entry | **Secrets via env/secret-manager only**, wrapped `RedactedSecret` so the value is opaque from entry; broker audits **metadata only** (`audit_projection`); short-TTL auto-expiry caps the leak window (`secret_source_protocol.py`; `spiffe-spire-workload-identity`; A8.3) | C |
| **D** | Broker cannot mint per-session creds at provider-spawn-cap rate → stall; or one provider's outage cascades into a credential-mint storm | **Broker mint-rate is a substrate test (fail-closed: no credential → no action)**; per-provider isolation so one provider's failure is a **bulkhead**, not a fleet-wide stall (`google-sre-cascading-failures`; T3) | M |
| **E** | A leaked leaf-agent token grants broad or **cross-provider** power — one compromise spans all providers (god-key) | **No god-key spanning providers** — per-provider, per-session, least-privilege, **short-TTL** SVIDs (`spiffe-spire-workload-identity`) + **sender-constrained (DPoP) tokens** that are *"useless if leaked"* without the bound private key (`rfc-9449-dpop-sender-constrained-tokens`; A8.3 src 12/13) | **C** |

---

## C8′ — Dynamic capability / skill supply-chain (cross-links C8 spawn-path & cross-cutting vector 6)

Agents can **load skills / MCP servers / tools at runtime**. The new surface is **supply-chain compromise of the
loaded artifact**: a poisoned skill executing attacker code, a malicious tool `description` injecting through the
tool channel, or a **rug-pull** (a server that passes audit then silently swaps its definition). House posture:
**signed + verified + least-privilege loading; refuse-NOT-quarantine on any verification miss (fail-closed).**

| STRIDE | Threat | Control (cited) | Sev |
|---|---|---|---|
| **S** | A malicious artifact masquerades as a trusted skill/MCP server (identity spoof) | **Verify signature + signer identity before load** — Sigstore keyless signing binds an OIDC identity (not a long-lived key) and records it in the **Rekor append-only transparency log** (`sigstore-artifact-signing`; OWASP **LLM03:2025** Supply Chain) | H |
| **T** | The artifact is tampered between build and load, or its definition drifts after audit (**rug-pull / TOCTOU**) | **SLSA-provenance verify-before-load** (L2 signed provenance detects post-build tampering) + **version-pinned manifests** + **re-verify on EVERY load, not just install** — trust granted once does not bind later behavior (`slsa-supply-chain-framework`; `mcp-tool-poisoning-rug-pull`; substrate §1) | **C** |
| **R** | "Where did this capability come from / who published it?" is unanswerable after an incident | Load events record the **artifact digest + signer identity + provenance attestation** into the C3 audit; the Rekor entry is an independent, append-only witness (`sigstore-artifact-signing`; `slsa-supply-chain-framework`) | M |
| **I** | A poisoned tool **`description`** is indirect prompt injection in the tool channel; the loaded skill reads/writes the shared-knowledge layer and exfiltrates | **Treat tool metadata as untrusted data** — it passes through the CaMeL Q-LLM/IFC path, never the trusted plan; least-privilege scope on the loaded capability (`mcp-tool-poisoning-rug-pull`; `camel-defeating-prompt-injection-by-design`; OWASP **LLM01:2025** indirect injection) | **C** |
| **D** | A flood of dynamic loads, or a heavyweight/recursive skill, exhausts compute/spend | Load is **governance-gated (the C8 SPAWN request path, not self-service)**; per-load resource caps + the gateway's throttling/circuit-breakers bound the blast radius (`google-sre-cascading-failures`; `owasp-api4-resource-consumption`; org-model §2.3) | H |
| **E** | A loaded skill widens its own privileges or executes code beyond its declared scope | **Least-privilege loading + minimum required SLSA level per capability class**; **refuse-not-quarantine** on any signature/provenance/version miss — an unverified artifact is **never loaded into a sandbox "to inspect"**, it is refused (`slsa-supply-chain-framework`; `sigstore-artifact-signing`; CLAUDE.md §5.6 fail-closed) | C |

---

## C9 — Cost-data integrity (NEW component)

Cost is the budget-cap and kill-switch's primary input on an unattended run. The threat: a **compromised/rogue
agent inflates spend** (to frame a victim / exhaust a competitor's budget) or **hides spend** (to evade caps and
keep spending). **Control thesis (binding):** cost is **NEVER a number an agent can choose**. It is a
**deterministic pure function of provider-ATTESTED usage × a VERSIONED PRICE SNAPSHOT**, written **append-only +
hash-chained**, and **independently RECONCILED against the provider's billing/usage meter**. The spender is not
the scorekeeper.

| STRIDE | Threat | Control (cited) | Sev |
|---|---|---|---|
| **S** | A cost record is written under a spoofed actor, or self-reported usage is passed off as provider-attested | Usage figure is the **provider-attested meter** (provider usage/billing API), not an agent claim; the cost actor is an **attested SPIFFE id**; the **agent has no write path to the cost-of-record** (`billing-reconciliation-internal-control`; `nist-sp-800-92-log-management`; `spiffe-spire-workload-identity`) | H |
| **T** | An agent edits a cost figure, or recomputes cost with a different price to under/over-state it | **Cost = f(attested_usage, versioned_price_snapshot)** computed by the deterministic core (propose-then-dispose); the price snapshot is **immutable + versioned**; recomputation is reproducible to the unit (CLAUDE.md §3.11 zero-numerical-error; `billing-reconciliation-internal-control`) | **C** |
| **R** | An agent denies the spend it incurred, or claims a different total | Every cost event is provable via an **RFC-6962 inclusion proof** against a signed cost-tree head; the per-window total is a **Merkle-aggregated authenticated sum**, so the cap decision itself is provable (`rfc-6962-certificate-transparency`; `crosby-wallach-tamper-evident-logging`) | M |
| **I** | The cost ledger leaks tenant/PII or sensitive deal context | **Hashes/lineage only (T1)**; ledger transit is TLS, storage append-only/write-once, access least-privilege (`nist-sp-800-92-log-management`) | M |
| **D** | **Silent cap evasion** — a compromised reporter quietly **UNDER-reports or TRUNCATES its own spend** so the cap-enforcer sees a low total while spend continues unattended (or **OVER-reports** to frame/DoS another tenant's budget) | **History-tree consistency proofs defeat truncation** (a plain hash chain does NOT — entries can be dropped off the end); **signed cost commitments are gossiped to independent auditors** (reconciler + enforcer + North-Star overseer) so **equivocation/forking is exposed**; budget cap is a provable authenticated aggregate, not a self-reported counter; **fail-closed: during the reconciliation window, use the conservative (higher) of provisional vs reconciled cost** and trip containment if reconciliation diverges (`crosby-wallach-tamper-evident-logging`; `rfc-6962-certificate-transparency`; `billing-reconciliation-internal-control`) | **C** |
| **E** | A compromised component seals/forges a cost-tree head, or grants itself the reconciler role | **Cost-tree-head signing + reconciliation are a separate privilege the spending agent never holds** (segregation of duties); the **reconciler compares against the provider meter as source of truth** and the spender cannot become the scorekeeper (`billing-reconciliation-internal-control` COSO segregation-of-duties; `crosby-wallach-tamper-evident-logging`) | C |

---

## Coverage map (B6 deltas)

4 components × full STRIDE = **24 enumerated deltas**, each with a cited fail-closed control.

- **C5′** Model-egress gateway — single-egress **DoS/SPOF** + degraded-mode (fail-static CLI fallback / fail-capability-closed programmatic).
- **C4′** Multi-provider secrets — **no god-key spanning providers**, sender-constrained short-TTL per-provider SVIDs.
- **C8′** Dynamic capability supply-chain — **signed/verified/pinned, re-verify-every-load, refuse-not-quarantine**.
- **C9** Cost-data integrity — **cost is attested-usage × versioned-price, hash-chained + reconciled; never self-reported**.

Cross-links: C5′ extends C5 (A8.1); C4′ extends C4 (A8.3, `credential_broker.py`/`secret_source_protocol.py`);
C8′ cross-links C8 spawn-path + cross-cutting vector 6 (supply-chain) + vector 1 (indirect injection via tool
metadata); C9 sits on the C3 audit-log substrate (RFC-6962 / history tree).

**Proposed new residual-register rows (for the maintainer to fold into `threat-model.md`):**
- **RR-9** Single-egress availability — mitigated by degraded-mode fail-static + supervised restart; residual = a
  gateway-down window degrades *programmatic any-model* capability (fails closed, by design). **Sev L** (capability-
  scoped, never whole-platform).
- **RR-10** Reconciliation timing gap (C9) — provider meter lags real-time usage; mitigated by conservative
  provisional cost + true-up; residual = a bounded window where provisional ≠ reconciled. **Sev M**.
- **RR-11** Q-LLM content corruption persists (C5′/C8′) — CaMeL guarantees control-flow/exfiltration safety, **not**
  that parsed *content* is trustworthy; a poisoned shared-knowledge entry can still mislead read-back. **Sev H**
  (this is the most dangerous attack found — see below).

---

## Most dangerous attack found (across B6) & the gap the original plan missed

**Most dangerous attack — shared-knowledge poisoning that fans out across agents.** A *single* indirect-prompt-
injection / poisoned-embedding entry written into the **shared memory/RAG layer** (OWASP **LLM01:2025** indirect +
**LLM04:2025** data/embedding poisoning) is read back by **many** agents — one poisoned entry steers the whole
fleet. CaMeL's guarantee explicitly does **not** cover *corrupted content* returned by the Q-LLM (only that
untrusted data cannot seize control flow or exfiltrate) — so read-back trust alone is insufficient. **Structural
defense:** taint/provenance must be attached **at write-time** and travel **with every value across agent hops**,
with consequential actions gated by the deterministic capability interpreter; the shared layer needs
verify-before-write + provenance + tenant-scoped, rollback-able writes (already named as cross-cutting vector 3,
but the **cross-agent fan-out amplification** should be made explicit). Runner-up: the **MCP rug-pull**
(time-of-check ≠ time-of-use — trust granted at install does not bind later behavior).

**Gap the original plan missed — single-egress AVAILABILITY as a first-class threat.** The Gate-2 C5 matrix
covers egress *confidentiality/integrity* (exfiltration, injection-triggered tool abuse) but the **D-row treats
flooding generically** and does **not** model the gateway-as-SPOF for an *unattended* run, nor a **degraded-mode
that fails the capability closed without halting the platform**. C5′ adds that explicitly (fail-static
direct-to-Anthropic for CLI traffic with a loud audited downgrade; fail-capability-closed for programmatic
any-model; OTP-style supervised restart with a restart-intensity cap that escalates to the kill-switch). Second
gap: **cost-data integrity had no component at all** — the original residual register tracked spend as a metric
feeding containment, but nothing modeled an agent *lying about its own spend*; **C9 closes that** by making cost a
reconciled, attested, hash-chained pure function the spender can never author.
