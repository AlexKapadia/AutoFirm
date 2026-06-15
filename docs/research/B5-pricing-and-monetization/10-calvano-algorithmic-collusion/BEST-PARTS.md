# BEST PARTS — Algorithmic Pricing Collusion (the safety guardrail)

## ADOPT (as a hard constraint, not a method)
- **An anti-collusion / antitrust guardrail on ANY learned or competitor-reactive pricing.** This is
  the single most important *safety* takeaway in B5. Build implication: AutoFirm's dynamic-pricing
  module is **forbidden from training reactive RL/Q-learning policies on competitor prices** without
  an explicit antitrust-compliance gate (B10) and human-in-the-loop approval (A7 HITL). Fail-closed:
  if a pricing policy's behavior cannot be shown NOT to converge on supracompetitive coordination,
  it is refused (CLAUDE sec 5.6).
- **Prefer deterministic, explainable pricing over black-box learned pricing (CLAUDE sec 3.5).**
  This source is the evidence that deterministic guardrails must dominate: a learned soft layer is
  permitted only if (a) it is explainable, (b) it provably does not learn collusive strategies, and
  (c) it clears the legal gate. Drives the "deterministic core + optional, gated ML" architecture.
- **Audit + monitoring of pricing behavior.** Build implication: every autonomous price change is
  logged to the append-only audit log (A6) with its driver; a monitor flags price trajectories
  consistent with tacit coordination (sustained supracompetitive levels + punishment patterns) for
  human review. Ties to A6 governance-aware telemetry.

## REJECT
- **Reject autonomous competitor-price-reactive learning agents as a product feature.** They are an
  antitrust and reputational liability per AER 2020 and its replications -- exactly the kind of
  "autonomous coordination without communication" regulators target. Reject by default.
- **Reject any pricing approach AutoFirm cannot explain to a regulator** (no black-box price that
  can't be justified rule-by-rule) -- CLAUDE sec 3.11.

## Build implication (concrete)
Imposes a **fail-closed antitrust guardrail + audit/monitoring** on the L2.B5 dynamic-pricing module
and a hard architectural bias toward deterministic, explainable pricing (CLAUDE sec 3.5). Any ML
layer must pass: explainability + provable-non-collusion + B10 legal clearance + A7 HITL, else it is
refused. This is a binding cross-branch constraint (B5 x A6 x A7 x B10), not optional.
