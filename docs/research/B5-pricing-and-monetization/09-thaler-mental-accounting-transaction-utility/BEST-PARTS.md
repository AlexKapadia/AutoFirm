# BEST PARTS — Mental Accounting / Prospect Theory in Pricing

## ADOPT
- **Reference-price + loss-aversion logic in the price-CHANGE engine.** Because a price increase
  above a customer's reference price is coded as a ~2x-amplified loss, AutoFirm's price-change /
  increase recommendations must account for reference dependence. Build implication: a
  `price_change_advisor` that flags increases crossing reference thresholds, recommends staged/
  smaller increments, and pairs increases with value-communication (justify the new reference).
  Ties to Simon-Kucher's finding (source 12) that firms capture only ~half of attempted increases.
- **Transaction-utility ("good deal") framing as a lever in value communication.** Setting/anchoring
  a credible reference price so the offer reads as positive transaction utility raises WTP. Build
  implication: the value-communication artifact (from sources 01/02) explicitly states the reference
  (e.g. NBA/EVC ceiling) so the offer price registers as a "deal" -- using the buyer's own EVC as the
  honest anchor (NOT a fabricated "was" price -> B10 legal gate).
- **Gain-framing of discounts / loss-framing avoidance for surcharges.** Present added charges as
  forgone discounts where lawful; frame multi-year/bundle savings as gains. Build implication:
  framing rules in the presentation layer (source 08), parameterized and legally gated.
- **Bundling/unbundling guided by mental accounting.** Thaler's principles (segregate gains,
  integrate losses) inform bundle vs. itemized pricing decisions -> a `bundling_advisor`.

## REJECT / DEFER
- **Reject manipulative or deceptive reference anchors.** Fabricated reference/"was" prices exploit
  transaction utility deceptively and are often illegal -> B10 fail-closed gate. Anchors must be
  truthful (real NBA, list, or prior price).
- **Defer** quantitative loss-aversion-calibrated demand models (parameterizing lambda per segment)
  -> L2.B5 advanced behavioral module; use the qualitative principles first.

## Build implication (concrete)
Adds a **behavioral pricing-dynamics layer**: `price_change_advisor` (reference-aware, loss-aversion-
calibrated increase logic) + framing/bundling rules in value communication. This is where pricing
*over time* (increases, discounts, bundles) is handled, complementing the static-optimum core
(sources 02/06/07). All anchors truthful (legal/fail-closed); the "why" of every recommendation is
explainable (CLAUDE sec 3.11) -- e.g. "increase capped at X% to stay within reference tolerance."
