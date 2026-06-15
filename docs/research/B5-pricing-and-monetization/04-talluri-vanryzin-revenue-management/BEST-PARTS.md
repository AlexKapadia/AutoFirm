# BEST PARTS — Revenue Management / Dynamic Pricing (Talluri & van Ryzin)

## ADOPT
- **The forecasting -> optimization -> pricing triad as the dynamic-pricing module's architecture.**
  AutoFirm's dynamic-pricing playbook follows this pipeline: (1) demand/elasticity forecast
  (consumes L1.B4 modeling + source 07 elasticity), (2) optimization (revenue/profit objective
  under capacity & WTP constraints), (3) price/control output. Build implication: three ordered,
  independently-testable stages with typed contracts between them (CTO data contracts).
- **An applicability gate ("should this company use dynamic pricing at all?").** RM only pays off
  under demand heterogeneity + segmentability + perishable/capacity-constrained inventory +
  uncertainty. Build implication: a deterministic gate that classifies each company/industry
  (B12 panel) as RM-suitable or not -- e.g. airlines/hotels/marketplaces YES; flat-rate B2B SaaS
  with infinite digital capacity usually NO. Prevents overfitting dynamic pricing to industries it
  harms.
- **Littlewood's rule / protection-level logic for capacity-constrained clients** (restaurants,
  marketplaces with finite slots, manufacturing capacity in the B12 panel). Adopt as a deterministic,
  exactly-reproducible sub-module (zero-numerical-error, CLAUDE sec 3.11).
- **RM as "WTP extraction over time" framing** unifies dynamic pricing with the price-discrimination
  taxonomy (source 03): dynamic pricing is intertemporal price discrimination.

## REJECT / DEFER
- **Reject black-box RL/Q-learning dynamic pricing as a default.** Source 10 shows learned pricing
  algorithms can converge to (illegal) supracompetitive collusion and are non-auditable. Prefer
  deterministic, explainable optimization (CLAUDE sec 3.5 deterministic guardrails + optional ML
  only if it earns its place AND clears the collusion/legal check).
- **Defer** advanced network/choice-based RM (multi-leg, customer-choice models) -> L2.B5 advanced;
  single-resource dynamic pricing + Littlewood cover the panel's common cases first.

## Build implication (concrete)
Adds the **dynamic-pricing module** to L2.B5, gated by an industry-suitability classifier so it is
only applied where RM theory says it helps (generality, not overfit). Deterministic optimization
core; any ML layer must pass an explainability + anti-collusion + legal gate (sources 10, 03; B10).
