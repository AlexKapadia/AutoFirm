# BEST-PARTS — Incrementality / geo-experiments

## ADOPT
- **Incrementality testing (RCT, falling back to geo-experiment) as AutoFirm's CAUSAL measurement layer**, sitting ABOVE attribution. Attribution (folders 05/06) allocates credit on observed paths; incrementality tests *prove* a channel caused lift before AutoFirm reallocates real client budget. **Build implication:** the marketing playbook has a 3-tier measurement stack: (1) attribution (fast, correlational, daily), (2) MMM (folder 08, mid-frequency, budget-level), (3) incrementality experiments (slow, causal, decision-grade). Budget shifts above a spend threshold REQUIRE an incrementality test — fail-closed if causal evidence is absent.
- **Geo-experiment as the default test design** because it is privacy-robust (no PII / cookie dependence) — aligns with AutoFirm's hard PII boundary (L1.B4.4, CLAUDE.md 3.12).
- **Gordon et al. (2019) as the governing evidence that observational != causal.** **Build implication:** any agent that proposes budget reallocation from attribution alone is blocked by a governance check demanding experimental corroboration for material decisions.

## REJECT
- **Reject deploying client budget on attribution-only ROI claims** — the peer-reviewed evidence (Gordon 2019) shows this can be badly wrong. This is a safety-of-spend control, not optional.
- Reject experiments where geo/audience cannot be cleanly held out (contamination) — degrade to MMM + clearly-labeled lower-confidence estimate.

## Why
This is the institution-grade backbone of marketing measurement: it prevents AutoFirm from confidently misallocating real money based on correlational attribution, satisfying the "100% secure / fail-closed / zero numerical-error decisions" bar.
