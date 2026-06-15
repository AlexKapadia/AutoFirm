# BEST-PARTS — Scaling Agent Systems (Kim et al., Google Research / Google DeepMind / MIT, 2026)

## ADOPT
1. **Route by TASK STRUCTURE, not by default-to-multi-agent** -- the study's core, independently
   replicated result: parallelizable -> multi-agent helps (**+80.8%** on decomposable financial
   reasoning, arXiv abstract); sequential -> multi-agent HURTS (headline **-70.0%** on sequential
   planning, arXiv abstract; per-variant range **-39-70%** per the Google Research blog).
   *Build implication:* directly hardens AutoFirm's routing predicate (SYNTHESIS L1.A1.2):
   the "low inter-dependency / breadth-first" condition is now evidence-backed by a 3-model-family study,
   not only by the Anthropic blog. Sequential/high-dependency work defaults to a single strong agent.
2. **Prefer COORDINATED over independent/"bag-of-agents" topologies** -- error amplification 17.2x
   (independent) vs 4.4x (centralized) per the Google Research blog. *Build implication:* corroborates rejecting decentralized mesh
   (source 01) and choosing the hierarchical orchestrator-worker backbone (02, 03); add an
   error-amplification resilience test to the A9 matrix.
3. **Cap fan-out near the saturation point (~3-4 agents per cluster)** -- *Build implication:* a concrete,
   evidence-backed default for AutoFirm's **span caps** (CLAUDE.md 4.1), re-validated on the golden set.
4. **Task->architecture routing is learnable (87% on unseen task configurations, Google Research
   blog)** -- supports building an explicit, testable routing component rather than ad-hoc orchestration.

## REJECT
- **"More agents are always better"** -- REJECT, with this study as the strongest single refutation:
  benefit saturates and reverses on sequential work. Reinforces source 04 (MAST) that bigger/more is not
  the fix.

## Role in the evidence base (why this source was added)
- The prior SYNTHESIS leaned on **source 02 (Anthropic blog, Low-Moderate tier)** for two load-bearing
  *Important*-criticality claims: "multi-agent wins by spreading reasoning / token usage dominates cost"
  and the ~15x cost framing. Per DEPTH-RUBRIC 1-2, an Important claim needs >=2 independent sources and
  should not rest on a Low-tier blog. This source adds an **independent, multi-model, methods-transparent**
  corroboration, raising the body-of-evidence tier and removing the single-weak-source exposure.

## Build implication (concrete)
- Encode the routing predicate as: parallelize IFF (breadth-first AND low-dependency AND >1 context AND
  gain > cost bar); else single agent -- now cited to {02, 04, 12}. Set default span cap ~3-4 per cluster
  (re-tune on golden set). Add error-amplification + sequential-degradation tests to A9. Feeds L2.A1 /
  L2.ORG / L2.A9.
