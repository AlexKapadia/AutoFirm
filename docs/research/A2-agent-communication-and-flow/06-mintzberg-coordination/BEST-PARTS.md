# BEST-PARTS — Mintzberg Coordination (the org-theory <-> MAS bridge)

## The bridge (L1.A2.3 core insight)
AutoFirm IS an organization of agents, so its inter-agent coordination = Mintzberg's coordinating
mechanisms instantiated in software. Each mechanism maps to a comms primitive:
- Mutual adjustment  -> free-form agent-to-agent chat (high flexibility, high FC2 failure risk).
- Direct supervision -> orchestrator issuing/monitoring tasks (the COO/CTO model, CLAUDE S1).
- Std. of work processes -> deterministic DAG / fixed protocol templates (source 08, FIPA, S04).
- **Std. of OUTPUTS -> typed output contracts between stages (the key A2 adoption).**
- Std. of skills -> capability/Agent-Card-based role definitions (source 01).
- Std. of norms  -> the binding CLAUDE.md doctrine all agents share.

## What AutoFirm should ADOPT and why

1. **Standardization of OUTPUTS as the primary inter-team coordination mechanism.** ADOPT typed,
   schema-validated output contracts at every stage boundary: specify WHAT each agent must
   deliver (shape, fields, units, acceptance criteria), leave the HOW to the agent. This is
   exactly Mintzberg's std-of-outputs and it is the cheapest reliable coordinator for a modular,
   multi-unit org. Build implication: every stage handoff is a typed artifact validated against
   the next stage's input contract (CTO data contracts, CLAUDE S CTO role) — minimizes the
   coordination chatter that drives MAST FC2 (source 02). This is the answer to L1.A2.3.

2. **Match mechanism to flow type (contingency).** ADOPT: structured/repeatable flows ->
   standardization (outputs + processes); novel/exploratory work -> bounded mutual adjustment
   under direct supervision. Build implication: AutoFirm's flow engine selects coordination
   mode by task type, not one-size-fits-all (links to source 08 deterministic-vs-dynamic).

3. **Divisionalized-Form analogy for the dynamic agent company.** ADOPT semi-autonomous agent
   "divisions" (teams) coordinated by output standards + targets, with the orchestrator setting
   targets not micromanaging method. Build implication: scalable span-of-control for L2.ORG.

## What AutoFirm should REJECT
- **REJECT mutual adjustment (free chat) as the default coordinator at scale.** Mintzberg: mutual
  adjustment is the mechanism of the *Adhocracy* (small, novel work) — it does NOT scale, and in
  MAS it concentrates inter-agent-misalignment failures (source 02, 36.94%). Reserve it for small
  exploratory sub-tasks under supervision.

## Concrete build implication
L1.A2.3 -> AutoFirm's dominant coordination mechanism is **standardization of outputs via typed
stage contracts**, contingent on flow type. Drives the CTO "typed data contracts between stages"
deliverable and a test: an output that fails its contract is rejected at the boundary
(fail-closed), so coordination errors surface at the producer, not silently downstream.
