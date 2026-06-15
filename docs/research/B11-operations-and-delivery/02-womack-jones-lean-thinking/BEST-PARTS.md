# BEST-PARTS — Lean Thinking (Womack & Jones)

## What AutoFirm should ADOPT

### 1. The five principles as the operations playbook backbone — ADOPT
L2.B11's operations playbook should be structured directly on **value → value stream → flow → pull →
perfection**, because (a) it is the most general, industry-agnostic lean codification (works for
SaaS, services, manufacturing, retail — every B12 panel row), and (b) it maps cleanly to AutoFirm's
own loop. **Build implication:** the playbook generator emits, for ANY client company, a
value-stream definition keyed to *that company's* end-customer value — satisfying the generality bar
(CLAUDE §3.9) rather than a manufacturing-only recipe.

### 2. Value defined by the END CUSTOMER — ADOPT as the north-star input
Principle 1 forbids the producer defining value. **Build implication:** before building any client
company, the opportunity-validation step (B3) must capture customer-defined value; AutoFirm should
*refuse* to proceed (fail-closed) if value is only stated from the producer's side.

### 3. Value-stream mapping with the 3-class split — ADOPT as a real artifact
The value-adding / Type-1 muda / Type-2 muda taxonomy is a concrete, quantifiable diagnostic.
**Build implication:** the operations engine produces a **value-stream map** per client process,
tagging each step into one of the three classes and computing a **value-add ratio** (value-adding
time / total lead time) — a numeric KPI that flows into `evidence/` (CLAUDE §3.10) and can be tested
against ground truth.

### 4. Flow + single-piece over batch — ADOPT for delivery cadence
Prefer continuous flow (small batches, frequent integration) over big-batch delivery — this is the
operations-theory root that DORA (09) later quantifies (small batches → better delivery perf).

## What AutoFirm should REJECT / bound
- **REJECT "perfection" as a literal end-state.** Treat it as the iterate-to-perfection *loop*
  (CLAUDE §3.7), bounded by the §RESEARCH-PROGRAM circuit-breaker (≥3 fails → arbitration). Infinite
  kaizen with no stopping rule contradicts the bounded-loop discipline.
- **REJECT lean-as-headcount-cutting.** A common misreading; AutoFirm uses lean to remove process
  waste, not to justify under-resourcing safety/QA functions.

## Concrete build implications
- **Component:** `operations/value_stream_map` (per-process, 3-class tagging, value-add ratio).
- **Contract:** playbook is parameterized by `customer_defined_value` (required input; fail-closed
  if absent).
- **Test:** generalization test — the value-stream generator must produce a sensible map for all 8
  B12 panel industries (overfit to one = FAIL).
