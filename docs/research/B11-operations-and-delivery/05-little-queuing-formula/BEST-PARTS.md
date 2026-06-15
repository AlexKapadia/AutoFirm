# BEST-PARTS — Little's Law

## What AutoFirm should ADOPT

### 1. L = λW as the deterministic backbone of ALL operations capacity claims — ADOPT
This is the single most important quantitative primitive for B11. It is a **proven theorem**, so any
operations claim AutoFirm makes about WIP, throughput, or lead time can be stated as an exact,
testable equation (CLAUDE §3.11 zero-numerical-error; §3.6 boundary-exact assertions). **Build
implication:** the ops-modeling toolkit (L2.B4.3) implements `cycle_time = wip / throughput` (and the
two rearrangements) as a verified deterministic function used everywhere capacity is reasoned about —
for ANY industry, because the law is distribution-free and industry-agnostic (perfect for B12 generality).

### 2. WIP = Throughput × Cycle Time as the lever-map for the orchestrator itself — ADOPT
Applied to AutoFirm's own agent pipeline: to cut delivery lead time, either raise throughput or cut
WIP. Since raising agent throughput is bounded (quota/context), **capping WIP** is the controllable
lever — this is the mathematical justification for the kanban WIP-limits (01-ohno) and the DBR rope
(04-goldratt). **Build implication:** the orchestrator's WIP cap per phase is chosen via Little's
Law to hit a target lead time, not guessed.

### 3. Distribution-free generality — ADOPT as a correctness guarantee
Because the law needs no assumption about arrival/service distributions, AutoFirm can apply it to
queues of support tickets (B9), order fulfillment (SCOR Deliver), or build jobs (B14) identically —
one primitive, all industries. **Build implication:** a single `littles_law` module backs queue/
capacity reasoning across every business function, avoiding per-industry special-casing (anti-overfit).

### 4. Steady-state requirement → an explicit precondition check — ADOPT (fail-closed)
The law holds only in a stable system (arrival rate ≤ service capacity; averages exist). **Build
implication:** the module must *refuse* to report a finite W when λ ≥ capacity (an unstable/exploding
queue) rather than emitting a misleading number — a fail-closed guard (CLAUDE §5.6). This is a
genuine correctness edge case to test.

## What AutoFirm should REJECT / bound
- **REJECT using L=λW for transient/non-stationary windows** without flagging it. It is a *long-run
  average* relationship; short bursts violate the premise. The module must label results as
  steady-state estimates.
- **REJECT importing heavy queueing models (M/M/1, M/G/k) as defaults.** Start with the
  distribution-free Little's Law; only escalate to specific queue models when a client problem
  genuinely needs waiting-time distributions (simplicity, CLAUDE §5.2; defer to a follow-up source).

## Concrete build implications
- **Component:** `operations/littles_law` — exact `L=λW` with all three rearrangements + a
  steady-state precondition guard.
- **Contract:** capacity/lead-time APIs across B9/B11/B14 consume this one primitive.
- **Test:** (a) boundary-exact unit tests (the retail L=5 and line cycle-time=0.5-day worked cases);
  (b) property test: `L == λ*W` for random valid (λ,W); (c) fail-closed test: λ ≥ capacity → refuses
  (no finite W). These kill any off-by-one or distribution-assumption mutant.
