# SUMMARY — The Theory and Practice of Revenue Management (Talluri & van Ryzin)

## Full citation
- **Title:** *The Theory and Practice of Revenue Management*
- **Authors:** Kalyan T. Talluri, Garrett J. van Ryzin
- **Year:** 2004 (Springer, International Series in Operations Research & Management Science, Vol. 68).
- **Venue/Publisher:** Springer.
- **Corroborating peer-reviewed survey:** McGill, J. I. & van Ryzin, G. J. (1999).
  "Revenue Management: Research Overview and Prospects." *Transportation Science* 33(2), 233-256.
- **Pointers:** https://link.springer.com/10.1007/978-3-032-03558-5_20 ;
  https://www.researchgate.net/publication/233485534_The_Theory_and_Practice_of_Revenue_Management ;
  https://www.informs-sim.org/wsc09papers/013.pdf (Revenue Management: Models and Methods)

## Ontology question(s) informed
L1.B5.1 (dynamic pricing / revenue management). Feeds L2.B5 dynamic-pricing module.

## GRADE tier
**High.** Talluri & van Ryzin is the canonical, field-defining reference monograph in revenue
management (Springer ORMS series); McGill & van Ryzin (1999) is a peer-reviewed survey in
*Transportation Science*. Independent corroboration across both -> High confidence for the RM
taxonomy and core results.

## Key claims (faithful)
1. **Purpose of RM (exact framing):** "The principal intent of revenue management is to extract all
   unused willingness to pay from consumers of differentiated services and products." RM is applied
   price discrimination over time/inventory.
2. **Two branches of RM:**
   - **Quantity-based RM** (originally "yield management" in airlines): seat/inventory allocation
     and capacity controls -- booking-limit / nested protection-level controls (e.g. Littlewood's
     rule for two fare classes, EMSR-a/-b heuristics for multi-class).
   - **Price-based RM (dynamic pricing):** continuously adjusting price over a finite selling
     horizon against stochastic demand to maximize expected revenue from fixed/perishable capacity.
3. **Three pillars (exact):** RM "synthesiz[es] forecasting, optimization, and pricing into a
   cohesive framework." Demand forecasting feeds an optimization that sets prices/controls.
4. **Conditions for RM to apply:** demand heterogeneity in WTP; ability to segment/fence; perishable
   or capacity-constrained inventory; demand uncertainty; advance/variable purchase timing. RM is
   "now a highly developed scientific and professional practice in the airline industry," with
   growing adoption in hotels, retail, cloud, and other industries.
5. **Littlewood's rule (two-class, exact form, the foundational RM result):** accept a lower-fare
   booking only while remaining capacity exceeds the protection level for the higher fare; protect
   y* units for class 1 where P(D1 > y*) = p2 / p1 (sell to low fare p2 iff p2 >= p1 * P(D1 > y*)).

## Reproducibility note
The forecasting/optimization/pricing triad and the quantity- vs price-based branches are restated
identically in Talluri & van Ryzin (2004) and McGill & van Ryzin (1999). Littlewood's rule is a
standard reproducible RM result (Talluri & van Ryzin Ch. 2). Two independent High-tier sources ->
meets DEPTH-RUBRIC sec 1 for this important claim.
