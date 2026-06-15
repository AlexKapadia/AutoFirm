# SYNTHESIS — A3: Long-Horizon Autonomy, Handoff & Resume (Layer-1 Foundations)

> Branch A3 of the AutoFirm research ontology. Covers L1.A3.1 (levels-of-autonomy frameworks),
> L1.A3.2 (long-horizon failure modes), L1.A3.3 (checkpoint/handoff/resume & state externalization).
> 10 sources, one folder each. This file surveys the option space and states AutoFirm's cited
> recommendation. Feeds L2.A3 (the resume protocol) and L2.A7 (HITL/autonomy gates).

---

## L1.A3.1 — Levels-of-autonomy frameworks

### Surveyed space (full menu)
| Framework | Structure | Tier |
|---|---|---|
| SAE J3016 (driving automation, L0–L5) | the origin 6-level ladder all others adapt | Standard |
| CSA / Reavis 2026 (src 01) | 6 levels (0–5) for agentic AI + in/on/out-of-loop oversight | Low–Mod |
| Interface/Ada Lovelace 2025 (src 02) | 5 levels via 3 dimensions (scope, control, tool-access) + liability shift | Moderate |
| Cihon et al. 2025 (src 03) | measurement via static code inspection on 2 axes: impact x oversight | Moderate |
| METR / Kwa et al. 2025 (src 04) | empirical capability metric: task time-horizon (not a normative ladder) | Mod–High |

These are complementary, not competing: normative ladders (01, 02), a measurement method (03), and an empirical capability frontier (04). They converge on a 5–6 level continuum and an in/on/out-of-the-loop oversight axis (independence => corroboration, clearing the >=2-source bar).

### Recommendation for AutoFirm
- **Declare an `autonomy_level in {0..5}` per session/subagent** using CSA's named ladder (src 01), **described by Interface's three dimensions** `{scope, control, tool_access}` (src 02), and **derived by static inspection of the orchestration config** (src 03) via `level = f(impact, oversight)` — a pre-flight "autonomy linter" with **no runtime cost** (src 03's key advantage; AutoFirm's config IS the orchestration code).
- **Default = Level 3 (Conditional):** act within boundaries, escalate on breach. "Run autonomously" raises specific phases to **Level 4** (monitored) but **never Level 5** — hard fail-closed prohibition (src 01: control mechanisms do not exist yet; reinforced by src 07 goal-misgeneralization).
- **Size tasks by METR's time-horizon** (src 04): decompose until each unit sits well inside the model's measured 50% time horizon, then checkpoint. Turns "decompose for reliability" into a measured rule.

---

## L1.A3.2 — Long-horizon failure modes

### Surveyed space (what breaks, and why)
- **Wang et al., COLM 2026 (src 05)** — 7-category taxonomy; [L]ong-horizon-specific = Catastrophic Forgetting, History Error Accumulation, Memory Limitation; [S]amplified = Environment/Instruction Error, False Assumption, Planning Error. **72.5% process-level vs 27.5% design-level**; base-model scaling alone unlikely to fully address.
- **Zhu et al. 2025 (src 06)** — AgentErrorTaxonomy of 5 modules (memory, reflection, planning, action, system); error **cascade/propagation** is the core bottleneck; AgentDebug attribution+correction gives **24% higher all-correct accuracy, 17% higher step accuracy, up to 26% relative task-success gain** (ALFWorld/GAIA/WebShop).
- **Langosco et al., ICML 2022 (src 07, High tier)** — **goal misgeneralization:** an agent retains capabilities out-of-distribution yet pursues the wrong goal. The dangerous silent drift — competent but mis-aimed.
- **METR (src 04)** — quantifies the frontier: success probability decays with task length; reliability is finite and measurable.

### Synthesis (the threat model AutoFirm's resume protocol must defeat)
Two independent author groups (05, 06) converge: long-horizon failure is dominated by **memory/context loss + planning errors that cascade**, and it is mostly a **process/orchestration problem, not a model problem**. Langosco (07) adds the most dangerous variant — **goal drift that stays competent**. Mandate: AutoFirm must **externalize goal + state and validate at milestones**, because (a) scaling will not fix it (05) and (b) early errors compound if not caught (06).

---

## L1.A3.3 — Checkpoint / handoff / resume & state externalization

### Surveyed space (the recovery decision menu)
| Mechanism | Source | Key property |
|---|---|---|
| Saga (forward + semantic compensation) | Garcia-Molina & Salem 1987 (src 08, High) | long-lived txns; all-complete OR compensate; semantic (approximate) undo |
| Coordinated checkpointing | Elnozahy et al. 2002 (src 09, High) | consistent global state, **no domino effect**, sync overhead |
| Uncoordinated checkpointing | src 09 | independent, but **domino-effect** risk — rejected as default |
| Communication-induced checkpointing | src 09 | forces checkpoints to avoid domino without full coordination |
| Log-based recovery (PWD + replay) | src 09 | replay nondeterministic events to recreate pre-failure state (durable execution) |
| SagaLLM (saga applied to LLM agents) | Chang & Geng 2025 (src 10, Moderate) | SA/SO/SD checkpoint state + GlobalValidationAgent + compensation graph |

### Recommendation for AutoFirm (the L2.A3 design seed)
1. **Model each multi-gate workflow as a SAGA** (src 08): a sequence of checkpointed, locally-atomic phases, each with a declared **semantic compensating action** (revert-commit, delete-branch, cancel-order). On failure, compensate back to an acceptable state — operationalizes §3.8 no-graveyard.
2. **Checkpoint COORDINATED at every gate** (src 09): the gate is the coordination point; saved consistent global state = git commit + task-list + roadmap + memory snapshot + **verbatim stored goal** (src 07) + SA/SO/SD (src 10). Avoids the domino effect by construction.
3. **PWD + idempotent event-logging for sub-gate resume** (src 09): the append-only audit log (branch A6.2) doubles as the replay log; every side-effecting tool call carries an **idempotency key** so replay never double-applies side effects.
4. **Re-ground on resume** (src 05/07/10): re-inject SA/SO/SD + the verbatim stored goal into the fresh context window; never let a resumed session re-infer its goal from a drifted transcript.
5. **Independent validation at each checkpoint** (src 10 + src 06): a **separate validation agent** (generator/evaluator split, §4.9) verifies outputs and dependencies before a checkpoint is committed — catches cascading errors early (src 06's lever).

### Checkpoint data contract (concrete, for L2.A3)
```
Checkpoint = {
  goal_verbatim,                 # stored once, re-grounded on resume (src 07)
  SA: workspace/git/files,       # Application State (src 10)
  SO: saga_step + txn_log + decision_reasoning,   # Operation State (src 10)
  SD: dependency_graph + compensation_metadata,   # Dependency State (src 10)
  autonomy_level + {scope,control,tool_access},   # (src 01/02/03)
  replay_log: [ {tool_call, result, idempotency_key} ]   # PWD replay (src 09)
}
```
Invariant (testable): consistent global state = **no orphan messages** (src 09) — no consumed delegated result whose producing step is uncheckpointed; every forward action has a registered compensator (src 08, fail-closed if missing).

---

## Cross-cutting recommendation (one line)
AutoFirm runs long-horizon work as **coordinated-checkpointed sagas with idempotent replay logs and externalized, re-grounded goals, validated by a separate agent at every gate, operating at a statically-derived autonomy level capped below Level 5** — grounded in High-tier DB/distributed-systems theory (src 08, 09), corroborated LLM-agent failure studies (src 05, 06), the goal-drift result (src 07), the LLM-specific saga realization (src 10), three convergent autonomy taxonomies (src 01–03), and METR's empirical time-horizon metric (src 04).

## Open items / honesty ledger (carry into QA + L2)
- **METR logistic-equation parameters & exact o3 minute figure** (src 04): cited as illustrative only; read arXiv:2503.14499 PDF verbatim before any constant becomes load-bearing.
- **Elnozahy page-locator quotes** (src 09): canonical taxonomy is uncontested, but verbatim section/page quotes pending a clean PDF read (text-extractor failed on compressed streams).
- **SagaLLM has no efficacy numbers** (src 10): architecture adopted; efficacy must be proven on AutoFirm's own golden suite (branch A9).
- **Goal-misgeneralization indirectness** (src 07): deep-RL, not LLM agents; transfer is by analogy, corroborated by src 05's False-Assumption/drift categories.
