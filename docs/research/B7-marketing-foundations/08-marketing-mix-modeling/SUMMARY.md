# SUMMARY — Marketing Mix Modeling (MMM): Econometric Channel Measurement

**Question(s) informed:** L1.B7.1 (attribution/measurement — aggregate econometric layer; budget allocation across channels).

## Full citations
- **Foundational text (primary):** Hanssens, D.M., Parsons, L.J., Schultz, R.L. (2001/2003). *Market Response Models: Econometric and Time Series Analysis*, 2nd ed. Kluwer/Springer.
- **Adstock (primary origin):** Broadbent, S. (1979). "One Way TV Advertisements Work." *Journal of the Market Research Society*, 21(3), 139-166. (Geometric adstock / advertising carryover.)
- **Modern Bayesian MMM (primary, Google):** Jin, Y., Wang, Y., Sun, Y., Chan, D., Koehler, J. (2017). "Bayesian Methods for Media Mix Modeling with Carryover and Shape Effects." Google research. https://research.google/pubs/bayesian-methods-for-media-mix-modeling-with-carryover-and-shape-effects/
- **MMM survey (preprint):** "Packaging Up Media Mix Modeling." arXiv:2403.14674. https://arxiv.org/pdf/2403.14674

## GRADE tier
- Hanssens et al. (Market Response Models): **High** (the standard scholarly reference for marketing econometrics).
- Broadbent 1979: **Moderate->High** (peer-reviewed JMRS; primary origin of adstock).
- Jin et al. 2017: **Moderate->High** (industry primary; basis of Google's LightweightMMM / Meridian).

## Core content (faithful summary)
MMM is a **top-down econometric regression** of an outcome (sales/revenue) on marketing spend by channel plus controls (price, seasonality, distribution, macro), to estimate each channel's **contribution, elasticity, and ROI/ROAS**, and to optimize budget allocation. Two non-linear transforms are essential:

1. **Adstock (carryover/lag).** Geometric adstock (Broadbent 1979): A_t = X_t + lambda * A_{t-1}, with retention rate 0 <= lambda < 1, where X_t is spend/GRPs at time t and A_t the adstocked value. Captures advertising's delayed and decaying effect.
2. **Saturation / shape (diminishing returns).** A concave (e.g. Hill or logistic) transform so marginal ROAS declines as spend rises. Hill: response = X^a / (X^a + g^a) (slope a, half-saturation g). Captures that each extra dollar yields less.

A typical specification: sales_t = base + SUM_c beta_c * Saturate(Adstock(spend_{c,t})) + controls + error. Coefficients beta_c -> channel contribution & ROI; the fitted response curves -> the optimal allocation.

## Key claims (locators)
1. Advertising effects are **dynamic (carryover)** and **non-linear (saturating)** — linear models without adstock+saturation are mis-specified (Hanssens et al.; Jin et al. 2017).
2. MMM is **privacy-robust** (aggregate, no user-level data) — it survived the cookie deprecation that broke user-level MTA.
3. MMM suffers **multicollinearity** across correlated channels and needs careful identification; Bayesian priors + experiment-calibration (incrementality, folder 07) improve identifiability (Jin et al. 2017; modern practice).

## Reproducibility note
Adstock and Hill-saturation formulae reproduced above in standard notation; MMM reproducible with open libraries (Google Meridian/LightweightMMM, Meta Robyn, PyMC-Marketing). Calibration to geo-experiments is current best practice.
