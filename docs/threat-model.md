# AutoFirm Threat Model (STRIDE) — living document

> **Status: COMPLETED at Gate 2** against the ratified architecture (`overview.md`, `substrate.md`,
> `data-contracts.md`, `org-model.md`, `tension-resolutions.md`) and the A6/A7/A8 research syntheses.
> Updated whenever the design changes (CLAUDE.md §5.6). The full **per-component STRIDE matrices** (48
> threats, each with a cited fail-closed control) live in the companion file
> **[`threat-model-stride-components.md`](./threat-model-stride-components.md)**. This file is the index:
> why-it-matters, the standing invariants, the trust-boundary map, the cross-cutting threat catalogue,
> and the residual-risk register.

## Why this matters here (more than usual)

AutoFirm orchestrates long-running, self-relaunching agents with real-world side effects — they can spend
money, send outreach, touch real services, and operate unattended. The blast radius of a compromised or
runaway agent is large. Therefore the design assumes from day one: **untrusted document input,
prompt-injection at every boundary, secret-leakage risk, and the need for a global kill-switch and
spend/rate limits.** AutoFirm is itself an LLM multi-agent system, so its own substrate is in scope of the
threat model (A7 §1).

## Standing invariants (binding now — enforced across every component)

- **Fail closed** — missing/ambiguous permission, key, check, or required contract field → **refuse** the
  action (CLAUDE.md §5.6; data-contracts §1; A8.2 default-deny RLS).
- **Least-privilege / no god-keys** — per-session SPIFFE identity + short-TTL, sender-constrained,
  audience-bound credentials minted at spawn; auto-revoked at retire (A8.3; T3).
- **Hashes, not PII, in the audit log** — the immutable log stores hashes + lineage of sensitive records,
  never raw PII/client content; VF erasure purges the content store and writes a tombstone without ever
  rewriting the hash chain (T1; data-contracts §3).
- **Hooks are fail-OPEN — never the boundary (T2).** Claude Code hooks are a logging/iterate-gate plane
  only. The true enforcement boundary is **permission deny-rules + OS/container sandbox + the A8 gateway PEP
  + SPIFFE-scoped credentials**. Every audit record is written through the gateway path (which can fail
  closed), so a dropped hook can never silently lose a record (substrate §3; T2).
- **Global kill-switch — out-of-band, agent-cannot-disable.** A single deterministic flag halts all external
  calls; on trip: stop + state-capture + immutable-log + quarantine + rollback, propagated to all live
  subagents. The agent never holds the kill credential (A7 §4; T3).
- **Synthetic-only-for-sensitive** — never real PII/client/deal data in tests or validation; public
  corporate data is allowed and clearly labelled (CLAUDE.md §3.12).
- **Append-only audit log** of every sensitive action and external call (what / when / who), tamper-evident
  via RFC-6962 hash-chaining + Signed Tree Heads at gates (A6.2).
- **An LLM never makes a hard decision** — propose-then-dispose: the stochastic layer proposes; the
  deterministic core disposes and records (overview §1; A7 §3).

## Trust boundaries / components in scope (→ STRIDE matrices)

Each is enumerated across all six STRIDE categories in
[`threat-model-stride-components.md`](./threat-model-stride-components.md):

| # | Component / trust boundary | Cite | Top concern |
|---|---|---|---|
| C1 | Claude Code CLI session substrate | A5 | cross-agent context leak; silent fan-out (E) |
| C2 | Message / work-flow bus | A2, A3 | indirect prompt injection via `content` (I/C) |
| C3 | Append-only hash-chained audit log | A6, A6.4 | tampering; dropped-record repudiation (T/R) |
| C4 | Credential broker (SPIFFE / short-TTL) | A8.3 | secret leakage; leaked-token reach (I/E) |
| C5 | Integration / API gateway (PEP) | A8.1 | exfiltration; injection-triggered tool abuse (I/E) |
| C6 | Per-tenant data isolation (Postgres RLS FORCE) | A8.2 | cross-tenant read/write (S/T/I/E) |
| C7 | Global kill-switch | A7 | agent disables/escapes containment (S/T/E) |
| C8 | Dynamic role spawn / hire path | A1.5, T3 | self-spawn / capability sprawl (S/D/E) |

## Cross-cutting threat catalogue (A7 §2 — ≥3-source-corroborated)

These vectors cut across components; each is placed on ≥1 component row above and carries an adversarial
red-team test (CLAUDE.md §3.6):

1. **Indirect prompt injection** via ingested untrusted data — **PRIMARY vector** (AutoFirm reads
   filings/web/tool output). Mitigation: deterministic DAG routing default (T5) + dual-LLM/CaMeL
   trusted-plan/untrusted-data separation (A7 §3; A8.1). → C2, C5.
2. **Direct prompt injection.** Mitigation: same CaMeL control-flow integrity + least-privilege. → C2, C5.
3. **Memory / RAG poisoning** (links A4.4). Mitigation: verify-before-write reflection loop; provenance-
   tracked, tenant-scoped, rollback-able writes (overview §2.3). → C2, C6.
4. **Tool-use abuse / tool poisoning.** Mitigation: least-privilege tool scopes + HITL on high-risk. → C5.
5. **Privilege escalation / capability sprawl.** Mitigation: single-writer RACI, spawn cap, no self-grant.
   → C1, C8.
6. **Supply-chain** (MCP servers, skills, deps). Mitigation: version-pinned manifests; `--bare` strips
   ambient config; dependency/SAST/DAST scanning in CI (substrate §1; CLAUDE.md §5.6). → C1.
7. **Collusive / emergent multi-agent misbehavior.** Mitigation: read-only audit agent (drift detection) +
   graduated containment (A6.3, A7 §4). → C3, C7.
8. **Data exfiltration via side-channels.** Mitigation: CaMeL IFC/taint + context-minimization + sender-
   constrained creds (A7 §3; A8.1; A8.3). → C4, C5.

Out-of-scope for the **platform** model (named per A7 §2 rubric): CBRN, obscene/violent content,
environmental harm — these belong to **client-business** content moderation (B-side), not the substrate.

## Residual-risk register

Risks that remain after the controls above. Each names the residual, why it persists, and the
mitigation / acceptance posture.

| ID | Residual risk | Why it persists | Mitigation / posture | Sev |
|---|---|---|---|---|
| RR-1 | **Prompt injection is not provably eliminated** | Prevention is provably incomplete (OWASP caveat; CaMeL solves 77% with provable security, not 100% — A7 §3, A8.1) | Defense-in-depth: PREVENT + DETECT (read-only audit agent, time-to-detection KPI) + CONTAIN (kill-switch); measured on AgentDojo into `evidence/` | **H** |
| RR-2 | **Fail-OPEN hooks could drop convenience-plane logs/iterate-gates** | T2: Claude Code hooks cannot be made to fail closed | Accepted by design — hooks are **never** the audit path; every record flows through the fail-closed A8 gateway (T2). Residual is only redundant convenience logging | **L** |
| RR-3 | **Credential broker mint-rate under spawn-burst** | Broker must mint at spawn-cap rate; a burst could stall (T3 scaling constraint) | Fail-closed: no credential → no action (never default-grant); broker mint-rate is a **substrate test** before merge | **M** |
| RR-4 | **Stochastic LLM layer non-determinism** (~80 unique completions / 1000 prompts) | LLMs are inherently non-deterministic (A5 §6) | LLM never makes hard decisions; validated statistically via A9 pass@k harness, never asserted reproducible | **M** |
| RR-5 | **Log truncation / delayed-detection window** | An attacker may drop recent leaves before the next STH seal (A6.2 src 05) | Signed Tree Heads at every gate + external anchoring + consistency proofs shrink the window; forward-secure keys | **M** |
| RR-6 | **Sandbox-escape category** (C1) | Sandbox escape is a named attack class; no sandbox is perfect (A7 §3 SoK) | Sandbox is **never sole control** — A8 gateway + SPIFFE creds are the egress boundary; escape tests in the substrate suite (substrate §7) | **M** |
| RR-7 | **Cross-tenant leak via misconfigured RLS** | One missing ENABLE/FORCE/policy leaks tenants (A8.2 src 11) | **Schema-audit fails the build** if any tenant table lacks the invariant; cross-tenant IDOR matrix = 0 successes; Silo for heavy-compliance tenants | **M** |
| RR-8 | **Unverified research formulae** (TRiSM CSS/TUE, Verifiability-First OPERA numbers) | Some safety sources read abstract-only; PDFs 403'd / deferred (A7 §9) | Do **not** implement guessed formulae; flagged as open items for QA / next wave; gated until primary source confirmed | **L** |

**Posture:** no residual is rated Critical — every Critical-severity threat in the component matrices has a
fail-closed deterministic control. The highest residual (RR-1) is the inherent incompleteness of prompt-
injection prevention, which the DETECT + CONTAIN layers (read-only audit agent + out-of-band kill-switch)
are specifically designed to bound, and which `evidence/` quantifies on AgentDojo.
