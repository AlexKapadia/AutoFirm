# BEST-PARTS — Six Sigma / DMAIC

## What AutoFirm should ADOPT

### 1. DMAIC as the structured operations-improvement protocol for EXISTING client processes — ADOPT
DMAIC complements TOC's five focusing steps (04): TOC finds the *constraint*, DMAIC reduces
*variation/defects* at it. **Build implication:** the operations playbook offers DMAIC as the
data-driven improvement routine — Define (CTQ from customer-defined value, ties to 02-womack
principle 1) → Measure (baseline KPIs from SCOR/Little) → Analyze (5 Whys, root cause) → Improve →
Control (lock the gain with monitoring). Maps cleanly onto AutoFirm's own gate/iterate loop (§3.7).

### 2. Variation-reduction + DPMO as a quantified quality KPI — ADOPT
DPMO is a deterministic, testable defect metric. **Build implication:** AutoFirm reports operations
quality as DPMO / sigma-level where opportunities are countable, feeding numeric quality charts into
`evidence/`. The principle "reduce variation, not just the mean" justifies AutoFirm's determinism
mandate (CLAUDE §3.6 determinism tests) — low variance IS the goal, not merely a good average.

### 3. "Control" phase = sustain-the-gain via monitoring — ADOPT
The Control phase is the operations-theory basis for AutoFirm's regression tests + North-Star drift
review: an improvement isn't done until it's locked against regression (control charts ↔ CI gates +
§4.7 heartbeat). **Build implication:** every operations improvement must ship with a control
mechanism (a monitored KPI / regression test), or it is incomplete.

### 4. CTQ (Critical-to-Quality) from the customer — ADOPT
Define-phase CTQ requirements are the measurable form of "customer-defined value" (02-womack).
**Build implication:** the playbook derives testable CTQ thresholds from customer needs and asserts
deliverables against them.

## What AutoFirm should REJECT / bound
- **REJECT the 3.4-DPMO / 1.5σ-shift figure as a universal asserted truth.** ASQ documents the shift
  is a convention, not a law. AutoFirm cites DPMO as a *definition* and computes the actual sigma
  level from real data; it does not claim "6σ = 3.4 DPMO" without the shift caveat.
- **REJECT heavyweight Six Sigma bureaucracy (belts/DOE) as a default.** For most client ops, use the
  DMAIC *thinking* and DPMO metric lightly; escalate to full statistical tooling only when the
  problem warrants it (simplicity, CLAUDE §5.2). Lean+Six-Sigma = "Lean Six Sigma" hybrid is the
  preferred default (CLAUDE §3.5 prefer hybrids).
- **REJECT the unaudited Motorola savings figure** as evidence.

## Concrete build implications
- **Component:** `operations/dmaic_engine` (5-phase routine) + `operations/quality_metrics` (DPMO /
  sigma-level, variation stats).
- **Contract:** every operations improvement ships with a Control artifact (monitored KPI/regression test).
- **Test:** deterministic DPMO unit tests (defects/opportunities × 1e6) with boundary cases (0 defects,
  all defects); a test asserting the engine records the 1.5σ-shift caveat rather than hard-coding 3.4.
