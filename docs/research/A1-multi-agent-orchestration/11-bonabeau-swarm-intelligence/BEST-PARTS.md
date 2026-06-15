# BEST-PARTS — Swarm Intelligence (Bonabeau, Dorigo & Theraulaz 1999)

## ADOPT (selectively, as a bounded primitive only)
1. **Stigmergy as an OPTIONAL low-bandwidth coordination primitive** -- coordinating indirectly through
   a shared *artifact* rather than direct messaging. *Build implication:* AutoFirm already does a
   constrained, auditable form of this -- agents coordinate via shared **typed artifacts** (the audit
   log, task list, roadmap doc; CLAUDE.md 4.8 resume-from-git-state). Adopt the *principle* (env-mediated
   coordination) but in a **single-writer, provenance-tagged** form, never an anonymous pheromone free-for-all.
2. **Negative feedback / decay to forget stale state** -- the ACO evaporation idea. *Build implication:*
   stale checkpoints, expired locks, and abandoned task claims should **decay/expire** rather than persist
   forever, preventing the system acting on stale shared state.
3. **Robustness via no-single-critical-agent** -- borrow the resilience goal (one worker dying must not
   sink the run) WITHOUT the leaderless topology: achieve it via orchestrator retries + checkpoints
   (CLAUDE.md 4.8), not emergence.

## REJECT (as a topology)
- **Swarm / leaderless emergent coordination as an AutoFirm topology** -- REJECT. Rationale tied to
  evidence: (a) emergent outcomes are **non-deterministic and hard to guarantee/steer** (this source) --
  incompatible with AutoFirm's deterministic-core + exact-explanation mandate (CLAUDE.md 3.2, 3.11);
  (b) **no single accountable decision-maker** breaks the append-only "who decided" audit invariant
  (CLAUDE.md 5.6); (c) convergence can need many agents/iterations -- expensive at LLM-token cost
  (corroborated by sources 02, 12 on token cost dominating). AutoFirm needs *named, accountable* roles
  on a hierarchy (03 HALO, 02), not anonymous emergence.

## DEFER -> now RESOLVED
- Swarm was named in the L1.A1.1 required enumeration (orchestrator-worker, hierarchical, blackboard,
  market/auction, debate, **swarm**) but was MISSING from the prior SYNTHESIS pattern table. It is now
  SURVEYED from the canonical primary source with an explicit ADOPT-as-primitive / REJECT-as-topology
  decision (DEPTH-RUBRIC 4.1-4.2), completing full-method-space coverage.

## Build implication (concrete)
- Treat the audit log / task list / roadmap as a **disciplined stigmergic medium** (single-writer,
  provenance-tagged, with decay of stale entries) -- the auditable opposite of anonymous pheromones.
  Feeds L2.A1 (topology rejection), L2.ORG (task-claim/lock decay), and L2.A6 (provenance on shared state).
