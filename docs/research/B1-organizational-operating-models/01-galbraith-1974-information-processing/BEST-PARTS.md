# BEST-PARTS — Galbraith (1974)

## What AutoFirm ADOPTS

1. **OIPT as the governing law of the dynamic-org engine.** AutoFirm's org engine should treat
   "task uncertainty -> required information processing" as a first-class design variable. When a
   client build or a research wave has high uncertainty, the engine must *consciously choose* one
   of the four mechanisms rather than silently overload the orchestrator.
   - **Build implication:** the **L2.ORG** spawn/re-scope engine carries a per-unit
     `task_uncertainty` estimate and a `coordination_mechanism in {slack, self_contained,
     vertical_IS, lateral}` decision, logged to the audit trail.

2. **"Self-contained tasks" = the scoped-subagent pattern.** Galbraith's strategy of restructuring
   around outputs to cut interdependence is *exactly* CLAUDE.md's "scoped subagents that return
   compact results." Decomposing the goal so each subagent owns a self-contained slice
   minimizes cross-agent coordination — the cheapest way to handle uncertainty.
   - **Build implication:** the decomposition step should explicitly *maximize self-containment*
     (minimize shared state between sibling subagents) as a measurable objective.

3. **"Lateral relations" = typed agent-to-agent contracts, not chatter.** When self-containment is
   impossible, prefer structured lateral coordination (typed message contracts, an integrating/
   reconciliation agent) over flooding the vertical channel (the orchestrator's context window).
   - **Build implication:** drives the A2 communication-contract design and the orchestrator's
     "fan-out then fan-in" reconciliation step.

4. **"Vertical information systems" = the audit log + state externalization.** Investing in formal
   vertical information systems maps to AutoFirm's append-only audit log and git/task-list state
   externalization (A3.3, A6) — the formal channel that lets the apex (orchestrator) decide.

## What AutoFirm REJECTS / treats with caution
- **Reject "slack resources" as a default.** Galbraith names it the lazy default (just add buffer).
  For an agent company, unbounded slack = wasted tokens/compute and slower runs. Use it only as an
  explicit, bounded choice (e.g. retry budgets), never as the silent fallback.
- **Reject the assumption that more vertical reporting scales.** OIPT predicts the vertical channel
  saturates; this is the theoretical justification for delegating off the orchestrator's context
  rather than reporting everything up (directly supports the §3.1 "protect your context" rule).

## Quantification for evidence/
- Metric: **coordination overhead** = fraction of orchestrator context spent on inter-agent
  reconciliation vs. productive decomposition. OIPT predicts this rises with task uncertainty;
  AutoFirm's evidence charts can plot overhead vs. measured task-uncertainty proxy to show the
  engine picks the right mechanism (a falsifiable, testable prediction).
