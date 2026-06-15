# BEST PARTS — Economic Value to the Customer (EVC)

## ADOPT
- **EVC as AutoFirm's canonical WTP-ceiling calculator.** This is the single most build-relevant
  formula in B5. Build implication: a deterministic `compute_evc(reference_value,
  positive_diff_value, negative_diff_value, switching_costs) -> evc` function with exact arithmetic
  (CLAUDE sec 3.11 zero-numerical-error path). Tested with boundary cases (zero differentiation,
  negative net differentiation, switching cost > differentiation) and a property test that
  EVC monotonically increases in positive differentiation and decreases in switching cost.
- **The reference-value / differentiation / switching-cost decomposition as the value-model
  schema.** Every value-based price AutoFirm proposes carries an itemized EVC breakdown -> this is
  the `value_model` field referenced in source 01's output contract, and the input to the
  value-communication artifact (B15).
- **Value-sharing split as a tunable, evidence-backed parameter.** Price = reference_value +
  share * differentiation_value, with `share` in (0,1). Build implication: `share` is industry-
  parameterized (B12), never a magic constant; default justified by competitive intensity, not
  hardcoded.

## REJECT / DEFER
- **Reject treating EVC as the price.** EVC is the WTP *ceiling*, not the offer price -- pricing at
  full EVC leaves the customer no surplus and kills adoption (corroborated by source 03's
  first-degree-discrimination ideal being unattainable). The offer price is a share below EVC.
- **Defer the worked $-numbers** -- illustrative only; AutoFirm must compute EVC from each client's
  real public/operational data (L1.B4.4 public-data boundary), never reuse the chemical example.

## Build implication (concrete)
The EVC function is a **deterministic core module** of the L2.B5 engine with zero tolerance for
arithmetic error, mutation-tested to ~100% (CLAUDE sec 3.6). Its output feeds: (a) the price-level
stage (price = f(EVC, share)), (b) the value-communication artifact, and (c) the LTV/CAC tie-in
(L1.B4.2) since the captured share of EVC drives gross margin and therefore LTV.
