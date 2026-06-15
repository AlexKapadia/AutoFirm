# BEST-PARTS — Maister (PSF)

## What AutoFirm ADOPTS

1. **Leverage = AutoFirm's agent staffing-mix law (applies to its OWN org AND to PSF clients).**
   Maister's central rule — *match the junior:middle:senior mix to the skill mix of the work* — maps
   directly onto AutoFirm's choice of how many cheap/fast subagents vs. expensive/capable agents to
   deploy on a task. This is the economic core of the dynamic-org engine.
   - **Build implication:** L2.ORG classifies each unit of work as **Brains / Grey-Hair / Procedure**
     and sets agent leverage accordingly: Procedure work -> high fan-out of cheap scoped subagents;
     Brains work -> few, highly-capable agents with rich context. Logged + auditable.

2. **The three project types are a decomposition primitive.** Before fanning out, AutoFirm should
   tag subtasks Brains/Grey-Hair/Procedure — this *is* the "what can be delegated cheaply vs. needs
   the senior agent" decision that protects the orchestrator's context (CLAUDE.md §3.1) and avoids
   the two mismatch costs (seniors on grunt work; juniors on frontier work).

3. **Utilization & realization as agent-fleet efficiency metrics.** Utilization = fraction of agent
   capacity doing productive (billable-equivalent) work vs. idle/overhead; realization = fraction of
   agent output that survives review/QA into the final deliverable (rework is lost realization).
   - **Build implication:** evidence/ tracks agent-fleet "utilization" and "realization" (output
     accepted at QA / output produced) — a direct, quantified efficiency story; low realization =
     too-weak agents or too-hard tasks, triggering re-leverage (a SARFIT adaptation, source 05).

4. **Profitability identity is deterministic and exact.** profit ~ rate x utilization x realization
   x leverage — closed-form, belongs in the deterministic core for PSF/services clients (panel row
   2), with boundary tests.

## What AutoFirm REJECTS / caution
- **Reject maximizing utilization.** Maister + the modern literature warn: maximize *profitable*
  utilization, not raw utilization (a senior at 60% on premium work beats a junior at 90% on
  commodity work). AutoFirm optimizes value-weighted, not hours-weighted.
- **Reject high leverage on Brains work.** Over-delegating frontier tasks to many cheap agents
  produces quality failures — the explicit Brains mismatch cost. Frontier/novel client problems get
  low leverage (capable agents).

## Quantification for evidence/
- Agent-fleet utilization + realization rates per run; leverage ratio per work-type — chartable.
- A "right-leverage" test: confirm the engine assigns high leverage to Procedure tasks and low
  leverage to Brains tasks across the panel (metamorphic — proves it is work-driven, not constant).
