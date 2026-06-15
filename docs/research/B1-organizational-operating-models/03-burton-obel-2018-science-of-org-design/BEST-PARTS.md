# BEST-PARTS — Burton & Obel (2018)

## What AutoFirm ADOPTS

1. **"Structure<->coordination fit" is THE design objective for AutoFirm's org engine.** AutoFirm's
   dynamic-org engine (L2.ORG) is precisely a structure (how it decomposes the goal into subagents)
   + coordination (how it integrates them) problem. The engine's success criterion = minimize
   **misfit cost**.
   - **Build implication:** the orchestration-topology choice (L2.A1) is evaluated by a fit metric,
     not taste — directly enabling branch-per-experiment selection on a golden set (CLAUDE.md §3.4).

2. **Multi-contingency parameterization = the generalization mechanism.** Burton & Obel prove there
   is NO single best structure; the right design is a function of contingencies. This is the
   theoretical license for AutoFirm to **parameterize every playbook by industry/size** (B12) rather
   than ship one template — and the warning against overfitting (CLAUDE.md §3.9).
   - **Build implication:** the org/business engine takes contingency inputs
     `{env_uncertainty, interdependence, strategy, technology, capability}` and selects design by
     rule, proven across the fixed industry panel.

3. **Forward-looking / scientific design.** AutoFirm should *design before building* (matches §3.1
   plan-first) and treat designs as testable propositions, not descriptions.

4. **Misfit cost as a measurable, fail-closed signal.** A detectable misfit (e.g. coordination
   overhead spiking, agents contradicting) should trigger re-design — the basis for the North Star
   heartbeat and the SARFIT-style adaptation loop (see source 05).

## What AutoFirm REJECTS / caution
- **Reject one-size-fits-all topology.** Even AutoFirm's own orchestrator-worker default must be
  justified per workload against contingencies, not assumed universal.
- Caution: the multi-contingency model is rich; AutoFirm should encode a *tractable* subset of
  contingencies (the five above) rather than the full Organizational Consultant rule base, to keep
  the engine deterministic and auditable.

## Quantification for evidence/
- **Fit/misfit score** per org configuration on the golden set: lower misfit -> measured higher
  task success / lower coordination overhead. This is the headline efficacy chart for L2.ORG.
- Contingency-sensitivity test: vary one contingency, confirm the engine changes the recommended
  design (a metamorphic test — proves it is contingency-driven, not constant).
