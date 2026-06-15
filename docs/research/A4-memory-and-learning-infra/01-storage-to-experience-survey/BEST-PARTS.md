# BEST-PARTS — Storage-to-Experience Survey

## ADOPT
- **The Storage → Reflection → Experience progression as AutoFirm's memory maturity model.**
  Build implication: the memory subsystem is **tiered by maturity, not just by recency**. AutoFirm
  writes raw trajectories (Storage), runs scheduled reflection passes that refine them (Reflection),
  and abstracts cross-project "experience" (reusable playbook deltas) into a durable layer
  (Experience). Maps onto L2.A4's tiered design.
- **The three drivers as design tests.** Long-range consistency, dynamic-environment robustness, and
  continual learning become **acceptance criteria** for the memory layer's evidence (`evidence/`):
  a determinism/consistency test, a distribution-shift test, and a learning-curve test.
- **Cross-trajectory abstraction** = the mechanism for AutoFirm's "learns from every company it
  builds" capability — generalize from many client engagements into industry-agnostic experience
  (ties to L1.B12 generalization).

## REJECT / DEFER
- **Reject treating the survey's numbers as primary.** As a secondary synthesis it cannot satisfy
  DEPTH-RUBRIC §1 alone; every quantitative claim AutoFirm relies on is corroborated here against the
  primary papers (folders 03, 04, 10, 11).
- **Defer "proactive exploration / curiosity"** for the autonomous company setting: curiosity-driven
  exploration is risky under fail-closed governance (could trigger unsanctioned external actions).
  Gate it behind A7 safety controls before adoption.

## Build implication (concrete)
Drives the **maturity-tiered memory contract** in L2.A4: `raw_trajectory` → `reflection` →
`experience` records, each with a `maturity_stage` field, and a scheduled reflection/abstraction job.
