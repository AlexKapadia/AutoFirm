# BEST-PARTS — MAST / Cemri et al. 2025

## ADOPT
1. **MASFT as AutoFirm's mandatory failure-mode test matrix** — the 14 modes become **named,
   required adversarial test cases** in the A9 platform-eval harness and the iterate-to-perfection
   loop (CLAUDE.md §3.6). *Build implication:* each mode → at least one teeth-having test that fails
   if AutoFirm exhibits it. This is the single most build-relevant artifact in branch A1.
2. **"Inter-agent misalignment is the biggest failure class (39.1%)"** — *Implication:* AutoFirm
   invests coordination effort in **typed contracts + explicit handoff state** (ties A2 communication
   protocols), not just better individual prompts. FM-2.3 task derailment (10.6%) and FM-2.5 ignored
   input (6.6%) directly justify the orchestrator's "fan-in / reconcile" step (CLAUDE.md §4.3).
3. **Verification is a first-class failure source (FC3, 32.5%; FM-3.2 "no/incomplete verification"
   = 14.6%, the single most common mode)** — *Implication:* AutoFirm's design must include a
   **dedicated, separate verifier agent** (generator/evaluator split, CLAUDE.md §4.9) and an explicit
   **termination/Definition-of-Done gate**, not self-verification. Validates the North Star/CCO and
   QA roles as structural, not optional.
4. **The core thesis: better models won't fix MAS; better ORG DESIGN will** — this is the cited
   foundation for AutoFirm's entire premise that orchestration discipline (CLAUDE.md §2–§4) is the
   product, not the model. Cite at the top of the L3.PLATFORM synthesis.
5. **FM-1.5 "Unaware of termination conditions" (5.3%) + FM-3.1 "Premature termination" (13.2%)** —
   AutoFirm needs explicit, tested **start/continue/stop** predicates (pairs well with HALO's 66%
   quorum early-stop, source 03).

## REJECT / caution
- **Self-verification by the producing agent** — REJECT (FM-3.3 incorrect verification, FM-2.6
  reasoning-action mismatch): the judge must be a different agent (CLAUDE.md §4.9).
- **Assuming multi-agent is automatically better** — REJECT: paper shows "minimal" benchmark gains in
  many systems; AutoFirm must *prove* the gain on its golden set, not assume it (L1.A1.2 caveat).

## Build implication (concrete)
- A 14-row **failure-mode → test-case map** owned by A9; a **separate verifier/QA agent** in the org
  engine (L2.ORG); explicit, tested termination predicates; typed handoff contracts (A2). The κ=0.77
  LLM-as-judge result supports using an LLM evaluator in the loop — but as an independent agent.
