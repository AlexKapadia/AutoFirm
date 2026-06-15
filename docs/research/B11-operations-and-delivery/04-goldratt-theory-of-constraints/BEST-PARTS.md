# BEST-PARTS — Theory of Constraints (Goldratt)

## What AutoFirm should ADOPT

### 1. The Five Focusing Steps as the operations-optimization loop — ADOPT
TOC gives AutoFirm a **rigorous, general algorithm** for improving any operating system: find the
bottleneck, exploit it, subordinate, elevate, repeat. This is provably better than "optimize
everything" (a constraint-blind agent wastes effort on non-constraints). **Build implication:** the
operations playbook's optimization routine is literally the five steps; for a client company the
agent (a) identifies the constraint (the resource at 100% utilization / the longest queue), (b)
proposes exploit/subordinate/elevate actions, (c) re-checks because the constraint *moves*. This
guards against the §3.9 overfit trap — you optimize the system, not a favorite local metric.

### 2. Throughput Accounting (T, I, OE) as the ops decision lens — ADOPT
T = revenue − truly-variable cost; maximize T, reduce I and OE. **Why adopt:** it aligns operations
decisions with money generation rather than misleading cost-allocation, and the three measures are
**deterministic formulas** → testable to the unit (CLAUDE §3.11). **Build implication:** the
modeling toolkit (L2.B4) computes T/I/OE alongside SCOR KPIs; throughput-per-constraint-hour becomes
the ranking metric when prioritizing which client operations action to take.

### 3. Drum-Buffer-Rope → buffer-before-the-bottleneck + WIP-release rule — ADOPT
DBR is the operations-theory counter-argument to naive zero-inventory JIT (see 01-ohno REJECT note):
*protect the constraint with a deliberate buffer; release work only at the constraint's pace.*
**Build implication:** AutoFirm's own orchestration uses a "rope" — release new agent tasks/branches
only at the rate the bottleneck stage (often the human gate or the QA/review function) can absorb,
and place a buffer (slack/checkpoint) before safety-critical gates. This directly bounds context
flooding (A1.4) and complements the kanban WIP limits from 01-ohno.

### 4. "Don't let inertia become the constraint" — ADOPT as a review prompt
Step 5's warning maps to the North-Star drift review (CLAUDE §4.7): periodically re-identify the
constraint because past solutions become today's bottleneck.

## What AutoFirm should REJECT / bound
- **REJECT throughput accounting as a replacement for GAAP/financial reporting.** It is an internal
  *operations decision* lens, not the client's statutory accounting (that is B-finance). Use it for
  ops prioritization only.
- **REJECT relying on narrative numbers from *The Goal*** (it is a novel). Cite the framework, never
  the plot's improvement figures as evidence.

## Concrete build implications
- **Component:** `operations/constraint_optimizer` (five-focusing-steps engine) +
  `operations/throughput_accounting` (T/I/OE).
- **Contract:** orchestrator task-release governed by a DBR "rope" keyed to the bottleneck stage's capacity.
- **Test:** (a) deterministic T/I/OE unit tests vs synthetic ledgers; (b) a property test that the
  optimizer never recommends elevating a NON-constraint while a constraint exists (kills the
  local-optimization mutant).
