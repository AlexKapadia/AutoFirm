# BEST-PARTS — HALO (Hou, Tang, Wang 2025)

## ADOPT
1. **The three-tier hierarchy as AutoFirm's literal org template** — plan (high) → role-design (mid)
   → execution (low). This maps 1:1 onto AutoFirm's COO/CTO (plan) → role assignment (mid) → scoped
   subagents (low). *Build implication:* validates the L2.ORG "dynamic, audited, scalable agent-org
   engine" as a **three-layer** design with cited precedent and measured gains.
2. **DYNAMIC role instantiation (Eq. 7), not a fixed roster** — A_role instantiates specialists per
   subtask. *Build implication:* AutoFirm should spawn roles from the task, not hard-code an org
   chart — directly supports CLAUDE.md L2.ORG "spawn/retire/re-scope". This is the strongest cited
   answer to L1.A1.3 "dynamic role assignment."
3. **Step-wise decomposition with execution history (Eq. 6)** — decompose one subtask at a time,
   conditioning on H_{k-1}, instead of full up-front planning. *Implication:* AutoFirm's roadmap/phase
   engine should re-plan from completed-gate state (ties to A3 handoff/resume).
4. **66% consistency early-stop (Byzantine-inspired)** — a cited, principled **termination rule**.
   *Implication:* AutoFirm gates can adopt a quorum-consistency stop to avoid the "unaware of
   termination conditions" failure (see source 04 MAST FM-1.5).
5. **"Cognitive overload" mechanism** — the cited *reason* hierarchy beats a monolith: it splits
   planning/reasoning/reflection across agents. Feeds the L1.A1.2 evidence base and the A4/A1.4
   context-flooding argument.

## REJECT / adapt-with-care
- **MCTS workflow search as a runtime default** — DEFER, do not adopt wholesale: MCTS multiplies
  agent calls (cost) and HALO reports GPT-4o-only results. For AutoFirm's auditable, cost-bounded
  runtime, prefer **deterministic gate-based phases** (CLAUDE.md §4.2); reserve MCTS-style search for
  the **offline branch-per-experiment** selection (§3.4), not the live company loop.
- **Treating the 14.4–26.6% gains as AutoFirm targets** — REJECT as targets: single-team,
  sub-sampled, one model. Use as *directional* evidence only; AutoFirm's own A9 harness must
  re-measure on its golden set (generality, CLAUDE.md §3.9).

## Build implication (concrete)
- L2.ORG = a **three-tier hierarchy with dynamic role instantiation** (cite HALO Eq. 6–8) +
  **quorum-consistency termination** (cite 66% early-stop). UCT (Eq. 9) is adopted only inside the
  offline experiment-selection harness, not the production orchestration loop.
