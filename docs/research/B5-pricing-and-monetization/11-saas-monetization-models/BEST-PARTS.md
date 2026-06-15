# BEST PARTS — SaaS / Digital Monetization Models

## ADOPT
- **The monetization-model menu as AutoFirm's digital-pricing option space.** Build implication: a
  `MonetizationModel` enum {flat, tiered, per_seat, usage_based, feature_based, hybrid, outcome_based}
  + freemium as an orthogonal acquisition flag. A `select_model(company_profile)` recommender maps
  each company to a model (or hybrid), parameterized by the B12 panel so it generalizes (e.g. B2B
  SaaS -> per-seat or hybrid; AI/infra -> usage-based; marketplace -> take-rate/commission).
- **"Pick the value metric" as the central, explainable design decision.** Build implication: the
  engine must explicitly choose and justify the *pricing unit* (seat/API call/outcome) by which it
  best tracks delivered value (ties to EVC, source 02). The output states "priced per X because value
  scales with X" -- the explanation requirement (CLAUDE sec 3.11).
- **Tiered GBB design via second-degree-discrimination + conjoint.** Build implication: tier design
  reuses the incentive-compatibility check (source 03) and the conjoint/MNL demand simulator
  (source 06) to set tier features + prices for self-selection. No magic 3-tier default -- tier count
  and fences are derived, not assumed.
- **Hybrid (base + usage) = two-part tariff as a default for variable-usage products** (microeconomic
  grounding, source 03). Adopt as a first-class structure.
- **Freemium as a gated acquisition strategy, not a price.** Apply only where network effects /
  word-of-mouth justify it (Niculescu & Wu 2014); model the free->paid conversion in LTV/CAC
  (L1.B4.2).

## REJECT / DEFER
- **Reject per-seat where value is not seat-correlated** (AI/usage products) -- vendor sources note
  it "breaks" there; use usage/outcome instead. Generality safeguard: model choice is conditioned on
  value driver, not defaulted.
- **Reject outcome-based pricing without a verifiable, attributable outcome metric** (measurement &
  attribution risk) -> defer to L2.B5 advanced + B10 (contractual definition of "outcome").
- **Defer** detailed billing/metering implementation (rating engines) -> B11/B14 (delivery).

## Build implication (concrete)
Provides the **monetization-model selector + value-metric chooser** for L2.B5's digital branch,
reusing the second-degree-discrimination (source 03) and conjoint (source 06) machinery for tier
design. Industry-parameterized over the B12 panel (the digital rows: SaaS, fintech, marketplace,
digital health) so "any company" pricing is proven, not asserted (CLAUDE sec 3.9 / sec 4.5).
