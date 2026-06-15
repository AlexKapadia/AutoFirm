# SUMMARY — Gabor-Granger & Conjoint/Discrete-Choice WTP Measurement

## Full citation
- **Primary (Gabor-Granger):** Gabor, A. & Granger, C. W. J. (1966). "Price as an Indicator of
  Quality: Report on an Enquiry." *Economica* 33(129), 43-70. (and Gabor & Granger 1961, "On the
  Price Consciousness of Consumers," *Applied Statistics* 10(3), 170-188.)
- **Primary (conjoint / choice-based):** Green, P. E. & Srinivasan, V. (1978). "Conjoint Analysis in
  Consumer Research: Issues and Outlook." *Journal of Consumer Research* 5(2), 103-123. Choice-based
  conjoint roots in McFadden, D. (1974) discrete-choice / random-utility theory (Nobel 2000).
- **Corroborating (method comparison):** Conjointly product docs (Gabor-Granger; conjoint);
  Academia.edu "Pricing Research: Monadic Pricing Evaluations" survey.
  https://conjointly.com/products/gabor-granger/ ; https://conjointly.com/products/van-westendorp/
- **Year:** Gabor-Granger 1961/1966; Green-Srinivasan 1978; McFadden 1974.
- **Venue:** *Economica*, *Journal of Consumer Research*, *Applied Statistics* (peer-reviewed).

## Ontology question(s) informed
L1.B5.1 (WTP measurement -- demand-curve and trade-off methods). Feeds L2.B5 WTP/optimization layer.

## GRADE tier
**Moderate-High.** Green-Srinivasan and McFadden are High-tier peer-reviewed primaries; Gabor-Granger
is a peer-reviewed *Economica* primary. The vendor docs are Low-tier method explainers used only for
implementation detail, corroborated by the primaries.

## Key claims and EXACT method (faithful)
1. **Gabor-Granger:** present each respondent a series of single prices; ask buy/no-buy at each. The
   procedure searches for the **inflection point** where the respondent switches from "yes" to "no."
   Aggregating across respondents yields a **demand curve** (proportion willing to buy at each price)
   -> directly a **revenue curve** (price x proportion) whose maximum gives the **revenue-optimal
   price** and an estimate of **price elasticity** at each point.
2. **Conjoint / choice-based conjoint (CBC):** present product profiles (attributes incl. price) and
   have respondents choose; estimate **part-worth utilities** via a random-utility (logit) model.
   WTP for an attribute = (utility delta) / (marginal utility of price). Handles **multi-attribute /
   feature-bundle** pricing and simulates demand/share under any price configuration.
3. **Random-utility foundation (McFadden):** choice probability of option i = exp(V_i) / sum_j exp(V_j),
   where V_i is the deterministic utility (incl. -beta*price); beta recovers price sensitivity. This
   is the multinomial-logit demand model underlying CBC.
4. **Method fit (exact):** "Combining Van Westendorp for range-setting with Gabor-Granger or conjoint
   for precision yields the best results"; conjoint is "ideal for complex products" with feature
   trade-offs; Gabor-Granger best for a single existing product's demand/revenue curve.

## Reproducibility note
The MNL choice formula (McFadden 1974) and conjoint part-worth -> WTP derivation (Green-Srinivasan
1978) are standard, reproducible peer-reviewed results. The Gabor-Granger demand/revenue-curve
construction is reproducible from buy/no-buy data. Multiple independent peer-reviewed primaries ->
meets DEPTH-RUBRIC sec 1 for this important claim.
