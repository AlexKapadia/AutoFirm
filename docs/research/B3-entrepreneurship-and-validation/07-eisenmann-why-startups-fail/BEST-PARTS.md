# BEST-PARTS — Eisenmann, Why Start-ups Fail (HBR 2021)

## ADOPT
1. **Enforce discovery-BEFORE-build as a hard gate (the false-start fix).** AutoFirm's validation
   playbook must NOT let the build capability (B13/B14) engage until a customer-needs/job discovery
   step has passed. This is a fail-closed sequencing rule (CLAUDE SS5.6): no discovery evidence ->
   refuse to build. Directly prevents the #1 documented lean-startup misapplication.
2. **Turn the six patterns into a risk-checklist the validation engine scores.** Each pattern becomes
   an explicit risk hypothesis evaluated per company (e.g. False Promises -> "is early-adopter signal
   representative of the mainstream SAM?"; Speed Traps -> "does the model survive without
   hypergrowth?"). Build implication: a `FailurePatternRiskCheck` that flags any pattern firing,
   feeding an auditable risk report (SS3.11).
3. **"Early adopters != mainstream" hardens the SAM/SOM logic (source 10).** Validation must
   distinguish the earlyvangelist beachhead (SOM proxy) from the broader SAM, and flag premature
   extrapolation — a known failure mode, now an explicit test.

## REJECT / DEFER
- **Do NOT treat the six patterns as a scoring formula with weights** — they are qualitative risk
  flags, not quantified probabilities; presenting them as precise probabilities would be overfitting
  to a non-causal taxonomy. Use as flags + rationale, not as a number.
- **Defer the scaling-stage patterns (Speed Traps, Help Wanted, Cascading Miracles)** to the
  operate/fundraise phases (B6/B11); they fire post-validation. Note them here, wire them there.

## Build implication
Two concrete deliverables for L2.B3: (1) a hard **discovery-gate** before the build phases; (2) a
**failure-pattern risk-check** that runs across the fixed industry panel and emits an explainable
risk report. Both are fail-closed and generalize across industries.
