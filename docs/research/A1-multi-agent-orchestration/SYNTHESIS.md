# SYNTHESIS — A1 Multi-Agent Orchestration & Coordination (Layer 1)

Branch owner: Research Analyst, A1. Covers L1.A1.1-L1.A1.4. Sources 01-09 in this folder.
Every recommendation traces to at least the DEPTH-RUBRIC source minimum (3+ independent for
safety/correctness-critical and the central multi-beats-single claim; 2+ for architecture choices).

---

## L1.A1.1 - Taxonomy of MAS coordination (FULL method space surveyed)

| Pattern | Primary source(s) | Strength | Failure mode | AutoFirm decision |
|---|---|---|---|---|
| Orchestrator-worker (lead + parallel workers) | 02 Anthropic; 01 Tran | parallel breadth, single accountable owner | lead is single point of failure; sync bottleneck; over-spawn | ADOPT - backbone |
| Hierarchical (plan/role/execute tiers) | 03 HALO; 01 Tran | tasks distributed across levels; reduces cognitive overload | latency/complexity | ADOPT - backbone (3-tier) |
| Decentralized peer-to-peer mesh | 01 Tran | scalability | high communication overheads; weak auditability | REJECT as primary |
| Blackboard (shared workspace) | 01; 06 | opportunistic, diverse experts | contention; shared mutable state | DEFER (use typed contracts) |
| Market / auction (Contract Net) | 08 Smith 1980 | self-selecting best contractor | overhead; non-determinism; diffuse ownership | ADOPT narrowly (optional) |
| Debate / society-of-minds | 05 Du et al. ICML 2024 | factuality + reasoning, error correction | compute cost; shared-context; herding; convergence not guaranteed | ADOPT as bounded sub-routine |
| Consensus / voting (multi-turn) | 09 Tian et al. | matches/exceeds strongest single model | herding to premature consensus | ADOPT for high-stakes gates |

Failure-mode foundation (definitive): source 04 (MAST/MASFT, peer-reviewed, 1600+ traces) gives a
14-mode, 3-category taxonomy. Inter-agent misalignment is the largest class (39.1%);
verification/termination is 32.5% (FM-3.2 no/incomplete verification = 14.6%, the most common single
mode). These 14 modes are AutoFirm's mandatory adversarial test matrix (owned by A9).

## L1.A1.2 - Does multi-agent beat a single strong agent? (EVIDENCE)

Yes, conditionally - corroborated by 4+ independent sources with explicit boundary conditions:
- FOR: 02 Anthropic (+90.2% internal research eval); 03 HALO (+26.6% avg vs single-agent ReAct);
  05 Du et al. (gains on all six reasoning/factuality tasks); 09 Tian (matches or exceeds strongest
  single model); clinical-workload study at intake (90.6% multi vs 73.1% single at 5 tasks, diverging
  under load).
- AGAINST / boundary: 04 MAST (benchmark gains often minimal; many systems fail from poor design;
  better models alone will not fix it); 02 (poor fit for shared-context / high-dependency tasks).
- Dominant lever is token usage: 02 reports token usage alone explains 80% of performance variance
  (3 factors explain 95%); multi-agent wins by spreading reasoning across more context/compute, at
  ~15x the token cost of a chat.

Decision rule (routing predicate AutoFirm adopts): use multi-agent IFF breadth-first AND
low inter-dependency AND exceeds one context window AND quality gain clears the ~15x cost bar.
Otherwise prefer a single strong agent. (02 + 04, corroborated by 03/05/09.)

## L1.A1.3 - Hierarchical / role-based orchestration & DYNAMIC role assignment

- 3-tier hierarchy with dynamic role instantiation is the cited, measured winner (03 HALO: planning
  A_plan -> role-design A_role -> inference agents, Eq. 6-8), reinforced by the
  cooperation/role-based/hierarchical coordinate in 01 and dynamic-spawn behavior in 02.
- Roles are instantiated from the task, not hard-coded (03 Eq. 7; 02 complexity-scaled spawn;
  08 dynamic manager/contractor) -> supports CLAUDE.md L2.ORG spawn/retire/re-scope.
- Principled termination: HALO Byzantine-inspired 66% quorum early-stop (03) plus MAST termination
  failures (04) -> AutoFirm needs explicit, tested start/continue/stop predicates.

## L1.A1.4 - Coordination-cost / context-flooding (information-processing view)

- Theory: Galbraith OIPT (07) - uncertainty implies more information processed between decision
  makers; manage it by reducing the need (self-contained tasks, slack) or increasing capacity
  (vertical information systems, lateral relations). Malone & Crowston (06) - coordination = managing
  dependencies; each dependency type maps to a cited mechanism.
- LLM-era confirmation: the orchestrator context window is its information-processing capacity;
  source 02 token-usage-80%-of-variance is the empirical realization of Galbraith. The debate
  context-length limit (05) and decentralized high communication overheads (01) are concrete costs.
- AutoFirm coordination-cost model: default to self-contained scoped subagents (cheapest; reduce
  need) -> add slack (checkpoints/retries) and vertical systems (typed contracts + audit) -> invoke
  lateral coordination (bounded debate/consensus) only for high-uncertainty subtasks.

---

## CONCRETE RECOMMENDATION FOR AUTOFIRM (feeds L2.A1 / L2.ORG)

1. Backbone = hierarchical orchestrator-worker, 3 tiers (plan -> dynamic role-design -> scoped
   execution), cooperative + role-based [02, 03, 01]. REJECT decentralized mesh as primary [01];
   REJECT market/debate/consensus as the primary topology [08, 05, 09].
2. Coordination = explicit typed dependency graph; route each dependency to its cited mechanism
   (prerequisite -> sequencing/gates; shared-resource -> span-cap/priority/bidding; usability ->
   typed contracts/standardized outputs; task/subtask -> planning agent; simultaneity ->
   fan-out/fan-in) [06].
3. Information-processing budget: prefer self-contained tasks; treat token usage as the first-class
   dominant cost metric (log and chart it); cap fan-out via span caps [07, 02].
4. Multi-agent routing predicate: parallelize IFF breadth-first AND low-dependency AND exceeds one
   context AND gain greater than ~15x cost; else single agent [02, 04].
5. Bounded sub-routines for quality: insert (a) debate (3 agents, up to 4 rounds, stubborn prompts)
   for factuality/reasoning checks [05]; (b) cross-model, anonymized, private-tally consensus for
   highest-stakes gates [09]; always with a separate verifier agent (generator/evaluator split) and a
   quorum/Definition-of-Done termination predicate [04, 03].
6. Mandatory test matrix: the 14 MASFT modes [04] become required adversarial tests in A9; per-pattern
   failure modes (single-point-of-failure, herding, over-spawn, sync bottleneck) become resilience tests.

Generality check (CLAUDE.md 3.9): recommendations are stated as topology/coordination mechanisms
independent of any industry or single benchmark; cited gains are directional evidence only, with
AutoFirm own golden-set re-measurement required (no overfitting to HALO GPT-4o numbers or Anthropic
internal eval).

## Open items / dependencies for downstream layers
- Exact per-benchmark deltas for sources 05 and 09 live in figures/tables not text-extractable here;
  directional conclusions are relied upon and triangulated. Re-extract tables if a quantitative L2
  target is needed (flagged for QA).
- Blackboard pattern is DEFERRED, not surveyed against a primary LLM-blackboard study; revisit if a
  shared-workspace design is reconsidered in L2.A1.
- Cross-half edge satisfied: org theory (07 Galbraith, 06 Malone & Crowston) feeds L2.A1/L2.ORG -
  the platform orchestration IS organizational design.
