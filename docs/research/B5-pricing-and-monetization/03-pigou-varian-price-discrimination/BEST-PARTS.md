# BEST PARTS — Price Discrimination Theory

## ADOPT
- **The three-degree taxonomy as AutoFirm's segmentation/monetization design space.** Every pricing
  recommendation maps to one (or a hybrid) of: 1st-degree (personalized/negotiated, B2B
  enterprise), 2nd-degree (versioning/tiers/usage menus -- self-selection), 3rd-degree
  (segment-based: student/region/SMB-vs-enterprise discounts). Build implication: a
  `discrimination_strategy` selector in the L2.B5 engine, with the **arbitrage-prevention
  ("fence") check** as a hard gate -- a tier/segment scheme without an enforceable fence is a
  defect (buyers would arbitrage to the cheapest price).
- **Second-degree self-selection as the backbone of tiered/usage SaaS pricing.** Versioning and
  Good-Better-Best tiers (source 11) are second-degree discrimination; design the menu so each
  segment's incentive-compatible choice is the intended one. Build implication: tier design must
  pass an incentive-compatibility check (no tier dominates another for its target segment).
- **Two-part tariff as the canonical hybrid pricing structure.** Base fee + usage = the
  microeconomically-grounded form of SaaS "subscription + consumption" hybrids (source 11). Adopt
  as a first-class price-structure option.
- **First-degree as the unattainable ceiling, not a target.** Use it as the theoretical
  profit-maximum benchmark to measure how much surplus a chosen scheme leaves on the table.

## REJECT / DEFER
- **Reject discrimination schemes that violate legal/fairness constraints.** Third-degree on
  protected characteristics (and many forms of personalized/algorithmic price discrimination) raise
  legal and reputational risk -> must run under the B10 legal/compliance gate and A7 fail-closed.
  Reject any scheme the legal playbook cannot clear.
- **Defer** full nonlinear-optimal-tariff mechanism design (Mussa-Rosen / Maskin-Riley) -> L2.B5
  advanced module; the three-degree taxonomy + two-part tariff cover the common cases first.

## Build implication (concrete)
Adds the **segmentation/fencing layer** to the L2.B5 engine: `{discrimination_degree, segments,
fences, incentive_compatibility_check, legal_clearance}`. The fence/arbitrage check and the
legal-clearance gate are fail-closed invariants (CLAUDE sec 5.6) -- AutoFirm never ships a price
schedule whose segments can arbitrage or whose discrimination basis is legally impermissible.
