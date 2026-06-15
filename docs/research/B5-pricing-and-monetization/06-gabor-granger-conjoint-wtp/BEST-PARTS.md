# BEST PARTS — Gabor-Granger & Conjoint WTP

## ADOPT
- **Gabor-Granger as AutoFirm's revenue-curve optimizer for single existing products.** Build
  implication: a `gabor_granger(buy_responses) -> {demand_curve, revenue_curve, optimal_price,
  elasticity}` module. This is the step that converts the PSM acceptable range (source 05) into a
  *revenue-optimal point* -- closing the "range -> optimal" loop. Deterministic, exact-arithmetic.
- **Choice-based conjoint + MNL for multi-attribute / feature-bundle / tier pricing.** Build
  implication: a `conjoint_demand(part_worths, price_beta)` simulator that, given estimated
  utilities, predicts share/revenue for any tier configuration -- the engine that designs
  Good-Better-Best tiers (second-degree discrimination, source 03) so each tier maximizes total
  expected revenue and is incentive-compatible. The MNL formula is the deterministic core.
- **The range-then-optimize workflow as the canonical WTP pipeline:** PSM (range) -> Gabor-Granger
  or conjoint (optimize within range, get elasticity) -> EVC ceiling check (source 02). Adopt as the
  WTP-layer's ordered contract.

## REJECT / DEFER
- **Reject conjoint when no survey/choice data exists.** For early-stage clients with no customers,
  fall back to EVC (value-side, source 02) + analog/comparable pricing (competition-based) until
  data accrues. Never fabricate part-worths.
- **Reject treating stated-preference WTP as exact;** validate against real transaction/elasticity
  data (source 07) where available.
- **Defer** hierarchical-Bayes conjoint estimation internals -> L2.B5 advanced; aggregate MNL first.

## Build implication (concrete)
Completes the **WTP-layer pipeline** in L2.B5: `psm (range) -> gabor_granger/conjoint (optimal +
elasticity) -> evc (ceiling)`. The MNL choice model is the deterministic demand engine reused by
both tier design and dynamic pricing (source 04). Outputs an explainable optimal price + elasticity
that feed the evidence showcase (revenue curve PNG/HTML, CLAUDE sec 3.10).
