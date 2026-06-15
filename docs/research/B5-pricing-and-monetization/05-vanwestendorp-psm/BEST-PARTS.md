# BEST PARTS — Van Westendorp PSM

## ADOPT
- **PSM as AutoFirm's range-finding WTP method when survey data is available.** Build implication:
  a deterministic `psm(responses) -> {PMC, PME, IPP, OPP, acceptable_range}` module computing the
  four cumulative curves and their intersections exactly (zero-numerical-error path; mirror the
  CRAN reference implementation, mutation-tested). Used to bound the value-based price (source 02
  EVC) from the demand side.
- **The four intersection points as explainable pricing anchors.** PMC/PME/IPP/OPP give the pricing
  output human-readable, defensible bounds ("acceptable range $X-$Y; indifference price $Z") that
  feed the value-communication artifact and the explanation requirement (CLAUDE sec 3.11).
- **Range-then-refine pattern.** Use PSM to set the acceptable range, then Gabor-Granger/conjoint
  (source 06) to find the revenue-optimal point within it -- the standard combined workflow.

## REJECT / DEFER
- **Reject PSM as a sole revenue optimizer.** It finds an *acceptable range*, not a
  revenue-maximizing price, and ignores volume/elasticity. Never output a PSM point as the final
  price without an elasticity/revenue check (source 06, 07).
- **Reject over-reliance on stated-preference numbers.** Hypothetical WTP is biased upward/noisy;
  PSM points must be cross-checked against real transaction data where available (L1.B4.4 public
  data) and treated as priors, not ground truth.
- **Defer** the extended/modified PSM with purchase-intent (Newton-Miller-Smith) revenue
  estimation -> optional L2.B5 enhancement.

## Build implication (concrete)
Adds a **WTP-measurement module** (`psm`) to L2.B5 producing an acceptable price range with explicit
PMC/PME/IPP/OPP anchors. Deterministic, exactly reproducible against the CRAN reference. Feeds the
price-level stage as a demand-side bound; the engine asserts the proposed price lies within
[PMC, PME] (or flags a justified exception), an explainable invariant.
