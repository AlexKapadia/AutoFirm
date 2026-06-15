# BEST-PARTS — Blackboard Architecture for Control (Hayes-Roth 1985)

## ADOPT (selectively)
1. **Opportunistic, data-driven control as a CONCEPT for the orchestrator's scheduler** -- the idea
   that the next action is chosen each cycle by rating *all* currently-enabled work against an explicit
   policy (not a fixed script). *Build implication:* AutoFirm's orchestrator may pick the
   highest-value ready subagent task from a queue rather than a rigid DAG order, while still logging
   *why* each was chosen (the "explainable control plan"). Pairs with the typed dependency graph (06).
2. **Control-as-data / explainable control plans** -- recording goals + policies + the rated choice
   per cycle. *Build implication:* feeds CLAUDE.md 3.11 (explain every decision) and the A6 audit
   trail: every orchestration scheduling decision is itself an auditable record.

## REJECT (as a primary topology)
- **Blackboard / global shared mutable workspace as AutoFirm's coordination backbone** -- REJECT.
  Rationale tied to evidence: (a) all coordination funnels through one shared store + one scheduler ->
  contention and a single point of failure (this source, Limitations); (b) shared mutable state across
  many writers creates write-write/stale-read hazards and weak per-contribution auditability -- the
  opposite of AutoFirm's typed-contract, append-only-audit, fail-closed posture (CLAUDE.md 5.6);
  (c) it conflicts with the breadth-first, context-isolated, single-writer subagent model AutoFirm
  relies on (source 02 Anthropic; CLAUDE.md 3.1 context safety). The hierarchical orchestrator-worker
  backbone (03 HALO, 02) is retained instead.

## DEFER -> now RESOLVED
- The prior SYNTHESIS DEFERRED blackboard "not surveyed against a primary LLM-blackboard study." This
  source supplies the **canonical primary architecture definition + its intrinsic failure modes**, so
  the pattern is now SURVEYED and a reasoned ADOPT-concept/REJECT-as-backbone decision is recorded
  (DEPTH-RUBRIC 4.2). An LLM-specific blackboard re-evaluation is only needed if L2.A1 reconsiders a
  shared-workspace design; the *structural* rejection rationale already holds for LLM agents.

## Build implication (concrete)
- Keep **typed contracts + append-only audit** as the shared-state substitute (no global mutable
  blackboard). Borrow ONLY the *opportunistic scheduling + explainable-control-plan* idea for the
  orchestrator's ready-task selection, with every scheduling choice logged. Feeds L2.A1 (topology) and
  L2.A6 (audit of orchestration decisions).
