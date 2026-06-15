# SUMMARY — A Blackboard Architecture for Control

## Full citation
- **Title:** A Blackboard Architecture for Control
- **Author:** Barbara Hayes-Roth (Stanford University, Heuristic Programming Project)
- **Year:** 1985
- **Venue:** *Artificial Intelligence*, Vol. 26, Issue 3, pp. 251-321 (peer-reviewed journal).
- **DOI/URL:** https://doi.org/10.1016/0004-3702(85)90063-3 ;
  ACM mirror: https://dl.acm.org/doi/10.1016/0004-3702(85)90063-3
- Companion precursor (blackboard *model* overview, context only, NOT the primary cited here):
  Nii 1986, "Blackboard Systems Part One", *AI Magazine* 7(2), https://doi.org/10.1609/aimag.v7i2.537

## Questions informed
- **L1.A1.1** (taxonomy of MAS coordination -- the **blackboard / shared-workspace** pattern) -- PRIMARY.
  Closes the prior gap where blackboard was DEFERRED without a primary architecture source.
- L1.A1.4 (coordination cost) -- supporting (control/contention cost of a shared mutable workspace).

## GRADE tier
**High.** Peer-reviewed *Artificial Intelligence* journal; the canonical, seminal architecture paper
for blackboard control (the BB1 architecture). It is the primary definition of the pattern, not a
secondary survey. Down-rate for **indirectness** vs LLM multi-agent systems (1985 symbolic-AI setting,
not LLMs); we therefore rely on it for the *pattern's structure and intrinsic failure modes*, not for
any LLM-era quantitative number. No quantitative claim is taken from it.

## Method / model (faithful)
- A **blackboard system** has three parts: (1) a **blackboard** -- a global, structured shared data
  store (a hierarchy of "solution-island" abstraction levels) holding the evolving partial solution;
  (2) independent **knowledge sources (KSs)** -- modular experts that read the blackboard and, when
  their preconditions match, contribute changes to it; (3) a **control component** that decides which
  pending KS action to execute next.
- The paper's central contribution is treating **control itself as a blackboard problem**: it adds a
  separate **control blackboard** plus control KSs, so the system reasons explicitly about *what to do
  next* using goals, **policies**, strategies, "foci of attention", and a scheduler that rates and
  picks the best pending action each cycle. The architecture "can construct, explain, and justify
  control plans" and supports **opportunistic** problem solving.
- **Opportunistic control:** the system is not fixed to a forward/backward chain -- at each cycle it
  may shift to whichever KS action is most promising given the current blackboard state, interleaving
  top-down and bottom-up reasoning.

## Key findings (faithful)
- KSs are **anonymous and decoupled**: they communicate *only* through the blackboard, never directly
  with each other -- the defining property of the pattern (indirect, data-driven coordination).
- Making control explicit and data-driven (control on a blackboard) lets the system **adapt its own
  problem-solving strategy at run time** and justify why each action was chosen -- an early
  "explainable control plan" result.
- The blackboard is **shared mutable state**: every KS sees and can modify the same global structure;
  the scheduler is the single arbiter of access order.

## Limitations / intrinsic failure modes (faithful + analysis)
- **Contention & control complexity:** all coordination flows through one shared store and one
  scheduler -- the scheduler is a potential bottleneck and single point of failure, and the control
  reasoning is itself substantial overhead.
- **Shared mutable state hazards:** concurrent/interleaved KS contributions to a global structure
  create consistency and ordering hazards (write-write conflicts, stale reads) absent in
  message-passing designs.
- **Weak auditability of authorship** unless every contribution is provenance-tagged -- relevant to
  AutoFirm's append-only audit requirement (CLAUDE.md 5.6).
- **Indirectness for LLMs:** symbolic KSs != LLM agents; the *mechanism* ports, the *numbers* do not.

## Reproducibility note
Pattern structure (blackboard + KS + control blackboard, opportunistic/anonymous coordination,
solution-island levels) is stated in the abstract and section structure of the paper and corroborated
by the Nii 1986 *AI Magazine* overview. No quantitative claim is drawn from this source.
