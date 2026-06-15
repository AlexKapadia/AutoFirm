# SYNTHESIS — A1 Multi-Agent Orchestration & Coordination (Layer 1)

Branch owner: Research Analyst, A1. Covers L1.A1.1-L1.A1.4. Sources 01-12 in this folder.
Every recommendation traces to at least the DEPTH-RUBRIC source minimum (3+ independent for
safety/correctness-critical and the central multi-beats-single claim; 2+ for architecture choices).

---

## L1.A1.1 - Taxonomy of MAS coordination (FULL method space surveyed)

| Pattern | Primary source(s) | Strength | Failure mode | AutoFirm decision |
|---|---|---|---|---|
| Orchestrator-worker (lead + parallel workers) | 02 Anthropic; 01 Tran; 12 Kim et al. | parallel breadth, single accountable owner; lowest error amplification (4.4x vs 17.2x, Google Research blog) | lead is single point of failure; sync bottleneck; over-spawn | ADOPT - backbone |
| Hierarchical (plan/role/execute tiers) | 03 HALO; 01 Tran | tasks distributed across levels; reduces cognitive overload | latency/complexity | ADOPT - backbone (3-tier) |
| Decentralized peer-to-peer mesh | 01 Tran; 12 (independent systems amplify error 17.2x, Google Research blog) | scalability | high communication overheads; weak auditability; error amplification | REJECT as primary |
| Blackboard (shared workspace) | 10 Hayes-Roth 1985 (primary); 01; 06 | opportunistic control; anonymous decoupled experts; explainable control plan | contention; single-scheduler bottleneck; shared mutable state hazards; weak authorship audit | REJECT as backbone; ADOPT only opportunistic-scheduling + explainable-control-plan idea |
| Market / auction (Contract Net) | 08 Smith 1980 | self-selecting best contractor | overhead; non-determinism; diffuse ownership | ADOPT narrowly (optional) |
| Debate / society-of-minds | 05 Du et al. ICML 2024 | factuality + reasoning, error correction | compute cost; shared-context; herding; convergence not guaranteed | ADOPT as bounded sub-routine |
| Swarm / stigmergic (leaderless emergent) | 11 Bonabeau, Dorigo & Theraulaz 1999 (primary) | scalability; robustness (no single critical agent); env-mediated low-bandwidth coordination | non-determinism; no accountable decision-maker; slow convergence; weak audit | REJECT as topology; ADOPT only disciplined single-writer stigmergy (audit log/task list/roadmap) + decay-of-stale-state |
| Consensus / voting (multi-turn) | 09 Tian et al. | matches/exceeds strongest single model | herding to premature consensus | ADOPT for high-stakes gates |

Full-method-space note: the six ontology-required patterns (orchestrator-worker, hierarchical,
blackboard, market/auction, debate, swarm) are now ALL surveyed against a primary source with an
explicit ADOPT/REJECT/DEFER decision (DEPTH-RUBRIC 4). Blackboard (10) and swarm (11) were the two
prior gaps and are now closed.

Failure-mode foundation (definitive): source 04 (MAST/MASFT, peer-reviewed, 1600+ traces) gives a
14-mode, 3-category taxonomy. Inter-agent misalignment is the largest class (39.1%);
verification/termination is 32.5% (FM-3.2 no/incomplete verification = 14.6%, the most common single
mode). These 14 modes are AutoFirm's mandatory adversarial test matrix (owned by A9). Source 12 adds a
quantitative topology-level failure metric (Google Research blog locator): independent systems amplify
errors 17.2x vs 4.4x for centralized coordination -> a resilience test for AutoFirm's chosen backbone.

## L1.A1.2 - Does multi-agent beat a single strong agent? (EVIDENCE)

Yes, conditionally - corroborated by 5+ independent sources with explicit boundary conditions:
- FOR: 02 Anthropic (+90.2% internal research eval); 03 HALO (+26.6% avg vs single-agent ReAct);
  05 Du et al. (gains on all six reasoning/factuality tasks); 09 Tian (matches or exceeds strongest
  single model); 12 Kim et al. (+80.8% on decomposable/parallelizable financial-reasoning tasks,
  arXiv abstract); clinical-workload study at intake
  (90.6% multi vs 73.1% single at 5 tasks, diverging under load).
- AGAINST / boundary: 04 MAST (benchmark gains often minimal; many systems fail from poor design;
  better models alone will not fix it); 02 (poor fit for shared-context / high-dependency tasks);
  12 Kim et al. (sequential planning degraded -70.0% headline per the arXiv abstract; every
  multi-agent variant degraded sequential tasks by -39-70% per the Google Research blog; benefit
  saturates beyond a ~3-4-agent resource ceiling and once single-agent baselines are already strong).
- Dominant lever is token usage: 02 reports token usage alone explains 80% of performance variance
  (3 factors explain 95%); multi-agent wins by spreading reasoning across more context/compute, at
  ~15x the token cost of a chat. This cost/diminishing-returns framing -- previously resting mainly on
  the Low-Moderate-tier Anthropic blog (02) -- is now INDEPENDENTLY corroborated by 12 (a controlled
  study across GPT/Gemini/Claude: 260 configs / six benchmarks per the arXiv abstract; 180 configs /
  four benchmarks per the Google Research blog), satisfying the >=2-independent-source bar for this
  Important claim and removing the single-weak-source exposure.

Decision rule (routing predicate AutoFirm adopts): use multi-agent IFF breadth-first AND
low inter-dependency AND exceeds one context window AND quality gain clears the ~15x cost bar.
Otherwise prefer a single strong agent. Sequential/high-dependency work defaults to single agent
(12 shows multi-agent actively hurts it). Cap fan-out near 3-4 per cluster (12 saturation point),
re-tuned on AutoFirm's own golden set. (02 + 04 + 12, corroborated by 03/05/09.)

## L1.A1.3 - Hierarchical / role-based orchestration & DYNAMIC role assignment

- 3-tier hierarchy with dynamic role instantiation is the cited, measured winner (03 HALO: planning
  A_plan -> role-design A_role -> inference agents, Eq. 6-8), reinforced by the
  cooperation/role-based/hierarchical coordinate in 01 and dynamic-spawn behavior in 02.
- Roles are instantiated from the task, not hard-coded (03 Eq. 7; 02 complexity-scaled spawn;
  08 dynamic manager/contractor) -> supports CLAUDE.md L2.ORG spawn/retire/re-scope.
- Coordinated > leaderless: 12 (17.2x vs 4.4x error amplification, Google Research blog) gives
  quantitative backing for a named-accountable hierarchy over swarm/mesh emergence (11, 01).
- Principled termination: HALO Byzantine-inspired 66% quorum early-stop (03) plus MAST termination
  failures (04) -> AutoFirm needs explicit, tested start/continue/stop predicates.

## L1.A1.4 - Coordination-cost / context-flooding (information-processing view)

- Theory: Galbraith OIPT (07) - uncertainty implies more information processed between decision
  makers; manage it by reducing the need (self-contained tasks, slack) or increasing capacity
  (vertical information systems, lateral relations). Malone & Crowston (06) - coordination = managing
  dependencies; each dependency type maps to a cited mechanism.
- Pattern-cost spectrum (now spanning the full method space): blackboard (10) funnels all coordination
  through one shared store + scheduler (contention + bottleneck); swarm (11) has near-zero direct
  messaging cost but pays in slow emergent convergence and lost accountability; debate (05) hits
  context-length limits; decentralized mesh (01) has high communication overhead. AutoFirm's
  hierarchy keeps coordination cost low and accountable.
- LLM-era confirmation: the orchestrator context window is its information-processing capacity;
  source 02 token-usage-80%-of-variance (corroborated by 12) is the empirical realization of Galbraith.
- AutoFirm coordination-cost model: default to self-contained scoped subagents (cheapest; reduce
  need) -> add slack (checkpoints/retries) and vertical systems (typed contracts + audit) -> invoke
  lateral coordination (bounded debate/consensus) only for high-uncertainty subtasks.

---

## CONCRETE RECOMMENDATION FOR AUTOFIRM (feeds L2.A1 / L2.ORG)

1. Backbone = hierarchical orchestrator-worker, 3 tiers (plan -> dynamic role-design -> scoped
   execution), cooperative + role-based [02, 03, 01]. REJECT decentralized mesh as primary [01, 12];
   REJECT blackboard as backbone [10]; REJECT swarm as topology [11]; REJECT market/debate/consensus
   as the primary topology [08, 05, 09].
2. Coordination = explicit typed dependency graph; route each dependency to its cited mechanism
   (prerequisite -> sequencing/gates; shared-resource -> span-cap/priority/bidding; usability ->
   typed contracts/standardized outputs; task/subtask -> planning agent; simultaneity ->
   fan-out/fan-in) [06]. Borrow blackboard's opportunistic-scheduling + explainable-control-plan idea
   for ready-task selection, logging every scheduling choice [10]; use disciplined single-writer
   stigmergy (audit log/task list/roadmap with stale-state decay) as the only swarm-derived primitive [11].
3. Information-processing budget: prefer self-contained tasks; treat token usage as the first-class
   dominant cost metric (log and chart it); cap fan-out via span caps ~3-4 per cluster [07, 02, 12].
4. Multi-agent routing predicate: parallelize IFF breadth-first AND low-dependency AND exceeds one
   context AND gain greater than ~15x cost; else single agent; sequential work -> single agent
   [02, 04, 12].
5. Bounded sub-routines for quality: insert (a) debate (3 agents, up to 4 rounds, stubborn prompts)
   for factuality/reasoning checks [05]; (b) cross-model, anonymized, private-tally consensus for
   highest-stakes gates [09]; always with a separate verifier agent (generator/evaluator split) and a
   quorum/Definition-of-Done termination predicate [04, 03].
6. Mandatory test matrix: the 14 MASFT modes [04] become required adversarial tests in A9; per-pattern
   failure modes (single-point-of-failure, herding, over-spawn, sync bottleneck, error amplification
   17.2x for uncoordinated topologies vs 4.4x centralized [12, Google Research blog]) become resilience tests.

Generality check (CLAUDE.md 3.9): recommendations are stated as topology/coordination mechanisms
independent of any industry or single benchmark; cited gains are directional evidence only, with
AutoFirm own golden-set re-measurement required (no overfitting to HALO GPT-4o numbers, Anthropic
internal eval, or the 12 benchmark-specific ~45% single-agent-baseline threshold from the Google
Research blog).

## Open items / dependencies for downstream layers
- Exact per-benchmark deltas for sources 05 and 09 live in figures/tables not text-extractable here;
  directional conclusions are relied upon and triangulated. Re-extract tables if a quantitative L2
  target is needed (flagged for QA).
- RESOLVED (was AMBER): blackboard is now surveyed against a primary architecture source (10
  Hayes-Roth 1985) with an explicit decision; it is no longer merely DEFERRED.
- RESOLVED (was AMBER): swarm/stigmergic -- named in the L1.A1.1 enumeration but previously absent --
  is now surveyed against the canonical primary source (11 Bonabeau/Dorigo/Theraulaz 1999).
- RESOLVED (was AMBER): the multi-vs-single cost/diminishing-returns claim previously leaned on the
  Low-Moderate-tier Anthropic blog (02); it is now independently corroborated by 12 (Google Research,
  3 model families), meeting the source-tier and independence bar.
- Cross-half edge satisfied: org theory (07 Galbraith, 06 Malone & Crowston) feeds L2.A1/L2.ORG -
  the platform orchestration IS organizational design.
