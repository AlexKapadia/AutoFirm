# BEST-PARTS — Verifiability-First Agents

## ADOPT
1. **The "detect-and-remediate, not prevent-only" stance — completes AutoFirm's defense-in-depth.** Sources 02/05 show prevention is incomplete; this source supplies the second half: assume some misalignment/injection slips through, and make it *fast to detect and reverse*. *Build:* AutoFirm pairs CaMeL-style prevention (source 05) with runtime audit + fast remediation (this source) + a kill-switch (source 08).
2. **Lightweight Audit Agents (intended-vs-actual comparison) as a core A7 component.** This is the orchestration-native form of oversight: a *separate, read-only* agent continuously checks each worker's actions against the trusted plan/brief — exactly the generator/evaluator split AutoFirm already uses for QA and the North Star review (CLAUDE.md §2 CCO, §4.9 visual-verification loop). *Build:* an audit subagent (read-only, least-privilege) watches the audit log + tool calls and flags drift; it never edits (matches the read-only CCO).
3. **Runtime attestations (tamper-evident verification of actions).** Maps onto branch A6 (append-only audit, provenance). *Build:* each privileged action emits a signed attestation into the immutable audit log (CLAUDE.md §5.6).
4. **Challenge-response gates for high-risk ops.** Concretely realizes OWASP #5 (human approval) — high-risk/irreversible actions require an extra verification step. *Build:* the HITL gate is a challenge-response, not a silent auto-approve.
5. **Adopt "time-to-detection" as a safety KPI** (from OPERA). *Build:* `evidence/` reports mean time-to-detect injected misbehavior under red-team — a quantitative oversight metric.

## REJECT / DEFER
- **Defer OPERA's specific numbers** (single unverified preprint) — adopt the *metric definitions* (detection rate, time-to-detection, stealthy-attack resilience), not any reported value, until corroborated or independently measured (DEPTH-RUBRIC §1: single source insufficient for a numeric claim).
- **Reject audit-agent-as-sole-control** — an audit agent is itself an LLM and can be fooled; it is a layer atop deterministic fail-closed checks (sources 09/10), not a replacement.

## Concrete build implications
- Supplies the **oversight half of the A7 stack**: read-only audit agents + runtime attestations + challenge-response HITL, feeding the kill-switch.
- Cross-branch: attestations -> A6 audit log; audit-agent -> A9 eval; HITL -> OWASP #5 (source 02).
