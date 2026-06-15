# BEST-PARTS — Verifiability-First / Audit Agents for AutoFirm

## ADOPT
1. **Adopt the verifiability-first principle as the A6 design axiom: make every agent action provably observable and auditable, and optimise for FAST detection of misalignment.** This reframes A6's purpose precisely: AutoFirm cannot guarantee a stochastic agent never errs, so it guarantees that any error is *detected and attributable* via the tamper-evident audit trail (sources 03/04/06). Matches CLAUDE.md §2 North Star (catch drift early) + §5.6.
2. **Adopt the lightweight audit-agent pattern (generator/evaluator split).** A separate, least-privilege **audit agent** continuously checks *intent vs. behaviour* — exactly CLAUDE.md §2's read-only North Star / audit role and §4.9's separate evaluator agent. *Build implication:* L2.A6 ships a dedicated audit agent that consumes the audit log + telemetry and challenges the orchestrator, never edits.
3. **Adopt challenge-response attestation for high-risk operations.** Before a destructive/external/high-Agency-Risk action (cf. source 08), require an attestation that produces a cryptographic proof-chain entry — a fail-closed HITL/agent gate (CLAUDE.md §5.6). Pairs with the history-tree inclusion proof (source 04).
4. **Adopt OPERA-style evaluation as AutoFirm's governance test rig:** measure (a) detectability of injected misbehaviour, (b) time-to-detection under stealthy/adversarial strategies, (c) resilience to prompt/persona injection. This is tests-with-teeth for the governance layer (CLAUDE.md §3.6) and feeds evidence/ (§3.10): inject faulty/malicious agent actions and assert the audit layer catches them — a *mutation-testing analogue for governance*.

## REJECT / DEFER
- **Reject "detect-only" as a licence to weaken prevention.** AutoFirm keeps fail-closed prevention (deny-by-default, least-privilege) AND adds verifiability-first detection. Adopt detection as a *complement*, not a replacement (CLAUDE.md §5.6 non-negotiable).
- **Defer the specific symbolic-verification implementation**; AutoFirm's attestation can start with signed audit records (sources 03/04/06) and add symbolic checks later.

## Why (cited)
This source gives A6 its guiding principle (provable observability + fast detection) and the concrete audit-agent + attestation patterns, plus an evaluation methodology (OPERA) that lets AutoFirm *prove* its governance has teeth rather than asserting it.
