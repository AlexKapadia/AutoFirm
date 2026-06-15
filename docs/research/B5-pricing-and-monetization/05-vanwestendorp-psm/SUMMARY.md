# SUMMARY — Van Westendorp Price Sensitivity Meter (PSM)

## Full citation
- **Primary:** van Westendorp, P. H. (1976). "NSS Price Sensitivity Meter (PSM) -- A New Approach to
  Study Consumer Perception of Prices." *Proceedings of the 29th ESOMAR Congress*, Venice,
  5-9 September 1976, pp. 139-167.
  https://www.scirp.org/reference/referencespapers?referenceid=212633
- **Corroborating peer-reviewed:** "The Van Westendorp Price-Sensitivity Meter As A Direct Measure
  Of Willingness-To-Pay." https://www.researchgate.net/publication/304658564
- **Corroborating (method/implementation):** Alletsee, M. *pricesensitivitymeter* R package (CRAN),
  reference implementation. https://cran.r-project.org/web/packages/pricesensitivitymeter/pricesensitivitymeter.pdf
- **Year:** 1976 (primary).
- **Venue:** ESOMAR Congress proceedings (recognized market-research professional venue).

## Ontology question(s) informed
L1.B5.1 (willingness-to-pay measurement -- stated-preference, range-finding). Feeds L2.B5 WTP layer.

## GRADE tier
**Moderate.** The 1976 ESOMAR paper is the primary source; widely-used professional method with a
peer-reviewed validation and an open reference implementation (CRAN) -> independently corroborated.
Down-rated from High because PSM is a *stated-preference* (hypothetical) method whose absolute price
points are known to be approximate, not a controlled-experiment WTP measure.

## Key claims and EXACT method (faithful)
1. **Four questions (the PSM instrument):** for a described product, respondents give a price at
   which it is:
   - **(TC) Too cheap** -- "so low you would question its quality" (too-cheap line),
   - **(C) Cheap / a bargain** -- "a bargain, a great buy for the money,"
   - **(E) Expensive** -- "getting expensive, but you still might consider it,"
   - **(TE) Too expensive** -- "so expensive you would not consider buying it."
2. **Analysis:** plot four **cumulative** distributions over price. Derived points (exact
   definitions):
   - **Point of Marginal Cheapness (PMC):** intersection of "too cheap" and "expensive" curves =
     **lower bound** of acceptable price range.
   - **Point of Marginal Expensiveness (PME):** intersection of "too expensive" and "cheap" curves =
     **upper bound** of acceptable price range.
   - **Indifference Price Point (IPP):** intersection of "expensive" and "cheap" (i.e. "not cheap"
     and "not expensive") curves -- the price at which equal proportions see it as cheap vs.
     expensive; often the median market price / typical price paid.
   - **Optimal Price Point (OPP):** intersection of "too cheap" and "too expensive" curves -- the
     price minimizing the proportion who reject the product as either too cheap or too expensive.
3. **Output:** an **acceptable price range [PMC, PME]** plus IPP/OPP as candidate points -- a
   *range-finder*, not a single optimal revenue-maximizing price.

## Reproducibility note
The four questions and the four derived intersection points are reproducible from the 1976 ESOMAR
paper and exactly implemented in the CRAN `pricesensitivitymeter` package (open source) -- a
reviewer can re-derive PMC/PME/IPP/OPP from raw survey responses. The peer-reviewed WTP-validation
paper provides independent corroboration. Three independent sources for the method definition.
