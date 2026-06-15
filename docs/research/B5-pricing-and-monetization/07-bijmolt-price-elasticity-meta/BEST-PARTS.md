# BEST PARTS — Price Elasticity Meta-Analysis

## ADOPT
- **The Lerner / inverse-elasticity rule as AutoFirm's elasticity-to-price optimizer.** Build
  implication: a deterministic `optimal_price(marginal_cost, elasticity) = MC * |e|/(|e|-1)` module
  (constant-elasticity case), and a more general numerical revenue/profit maximizer over an
  estimated demand curve (from Gabor-Granger/conjoint, source 06). Zero-numerical-error path;
  property-tested (e.g. optimal markup increases as |e| -> 1+). This is the microeconomic engine
  that turns a measured elasticity into a profit-maximizing price.
- **The -2.62 mean elasticity as an evidence-backed default PRIOR (never a magic constant).** When a
  client has no measured elasticity yet, AutoFirm seeds the optimizer with a category-appropriate
  prior from the meta-analytic distribution, clearly labelled as a prior to be replaced by measured
  data. Build implication: an `elasticity_prior(category, lifecycle_stage, promo_vs_regular)`
  lookup, parameterized by the documented determinants (B12 industry parameterization), NOT a single
  global constant. Generality safeguard: the prior is a starting estimate with stated uncertainty,
  overwritten once real data exists.
- **The elasticity determinants as the parameterization axes** for the B12 industry panel: brand,
  category, lifecycle stage, promo-vs-regular all shift elasticity -> the pricing playbook reads
  these per company so it generalizes across the panel rather than overfitting one industry.

## REJECT / DEFER
- **Reject applying a single global elasticity to all products/industries.** The meta-analysis shows
  elasticity varies 1-2 orders of magnitude by context; a one-number model is the overfitting trap
  CLAUDE sec 3.9 forbids. Always condition on determinants and replace priors with measured data.
- **Reject the Lerner rule where MC ~ 0 (pure digital goods).** For zero-marginal-cost SaaS the
  MC-based markup formula degenerates; switch to value-based (EVC, source 02) / WTP-curve revenue
  maximization (source 06) instead. Document this as the digital-goods branch.
- **Defer** cross-price/competitive-response elasticity (the 2019 JAMS meta) -> L2.B5 competitive
  module.

## Build implication (concrete)
Provides the **deterministic price-optimization core** (Lerner + numerical revenue maximizer) and an
**evidence-backed elasticity prior table** for cold-start, both feeding L2.B5's price-level stage.
The -2.62 figure and the determinant directions feed `evidence/` as the cited basis for priors.
