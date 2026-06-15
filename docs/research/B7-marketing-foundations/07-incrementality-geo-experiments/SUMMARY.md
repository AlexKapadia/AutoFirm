# SUMMARY — Incrementality: Geo-Experiments & the RCT-vs-Observational Gap

**Question(s) informed:** L1.B7.1 (attribution -> causal measurement; the gold-standard layer above correlational attribution).

## Full citations
- **Geo-experiment methodology (primary, Google):** Vaver, J. & Koehler, J. (2011). "Measuring Ad Effectiveness Using Geo Experiments." Google Inc. research paper. https://research.google/pubs/measuring-ad-effectiveness-using-geo-experiments/
- **Geo causal time-series (primary, Google):** Brodersen, K.H., Gallusser, F., Koehler, J., Remy, N., Scott, S.L. (2015). "Inferring Causal Impact Using Bayesian Structural Time-Series Models." *Annals of Applied Statistics*, 9(1), 247-274. https://doi.org/10.1214/14-AOAS788 (the "CausalImpact" method).
- **RCT vs observational ad effects (primary, peer-reviewed):** Gordon, B.R., Zettelmeyer, F., Bhargava, N., Chapsky, D. (2019). "A Comparison of Approaches to Advertising Measurement: Evidence from Big Field Experiments at Facebook." *Marketing Science*, 38(2), 193-225. https://doi.org/10.1287/mksc.2018.1135
- **Universal App Campaign geo case study:** "Advertising Incrementality Measurement using Controlled Geo-Experiments" (Google), ResearchGate 344372807.

## GRADE tier
- Gordon et al. 2019: **High** (peer-reviewed *Marketing Science*, large-scale field experiments at Facebook — landmark study).
- Brodersen et al. 2015: **High** (peer-reviewed *Annals of Applied Statistics*).
- Vaver & Koehler 2011: **Moderate->High** (industry primary research, Google; widely cited methodology).

## Core content (faithful summary)
- **Incrementality** = the *causal* lift in outcomes attributable to a marketing activity vs. a counterfactual where it did not run. The gold standard is a **randomized controlled trial (RCT)**: randomly split audience/geos into exposed (test) and held-out (control); the lift = test outcome - control outcome.
- **Geo-experiments / geo-lift:** randomize at the **geographic region** level (instead of individuals) — overcomes user-level privacy / cookie loss. Analyzed with difference-in-differences or Bayesian structural time-series (CausalImpact).
- **Gordon et al. (2019) key finding:** comparing RCT ground truth against common **observational** methods (incl. attribution-style and propensity/regression adjustment) on the SAME Facebook campaigns, **observational methods often produced substantially biased lift estimates** — sometimes off by a factor of several, and in some cases the wrong sign — because of selection effects (ad delivery is not random). Conclusion: observational attribution is an unreliable substitute for experiments for causal ROI.

## Key claims (locators)
1. Observational ad-effect estimates can **deviate materially** from experimental ground truth; the bias is large and not consistently directional (Gordon et al. 2019, Marketing Science 38(2)).
2. Geo-experiments give unbiased causal lift when individual randomization is infeasible (Vaver & Koehler 2011).
3. CausalImpact estimates counterfactual via a Bayesian structural time-series model fit on control series (Brodersen et al. 2015).

## Reproducibility note
Geo-lift designs reproducible with open tools (Google `CausalImpact` R package; geo-experiment frameworks). Gordon et al.'s bias finding is reproducible as a methodology lesson, not a single number to copy.
