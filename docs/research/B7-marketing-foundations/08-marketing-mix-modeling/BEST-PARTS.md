# BEST-PARTS — Marketing Mix Modeling

## ADOPT
- **MMM as AutoFirm's aggregate budget-allocation + ROI layer**, complementing attribution (path-level) and incrementality (causal point-tests). MMM answers "how should total budget split across channels," is **privacy-robust** (aggregate -> respects the PII boundary), and works for offline channels attribution can't see. **Build implication:** an `mmm` module fitting an adstock+saturation regression on aggregate client spend/sales; outputs per-channel contribution, ROI, and an optimized allocation.
- **Adstock A_t = X_t + lambda*A_{t-1} and Hill saturation** as correctness-critical transforms (reproduced exactly). **Build implication:** unit-tested deterministic functions; >=3 corroborating sources met (Broadbent + Hanssens + Jin). Test on hand-computable inputs for zero numerical error.
- **Experiment-calibrated MMM as the gold standard.** **Build implication:** MMM priors/coefficients are calibrated against incrementality tests (folder 07) — the three measurement layers reinforce each other rather than competing.

## REJECT
- **Reject MMM as a fine-grained tactical/creative optimizer** — it is aggregate and low-frequency; use attribution for that. Reject naive linear MMM without adstock+saturation (mis-specified per Hanssens/Jin).
- Reject over-trusting MMM coefficients under heavy channel multicollinearity without regularization/experiment calibration.

## Why
MMM gives AutoFirm a privacy-robust, industry-general, evidence-calibrated budget-allocation engine that closes the gap attribution and experiments leave (offline channels, total-budget optimization), forming the third leg of a triangulated, audit-defensible measurement stack.
