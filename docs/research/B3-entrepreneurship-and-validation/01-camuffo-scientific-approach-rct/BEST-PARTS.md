# BEST-PARTS — Camuffo et al. (2020) RCT

## ADOPT
1. **Make "frame the idea as falsifiable hypotheses, then test them" the spine of AutoFirm's
   opportunity-validation playbook (L2.B3).** This is the ONE intervention with RCT-grade causal
   evidence that it improves entrepreneurial decision quality. AutoFirm's validation agent should,
   for any new company, emit an explicit **hypothesis ledger**: a typed list of business-model
   hypotheses (value prop, customer segment, channel, willingness-to-pay) each with a falsification
   test and a pre-committed pass/fail threshold. Build implication: a `HypothesisLedger` data
   contract feeding the validation engine.
2. **Reward early TERMINATION, not just pivots.** The RCT shows the value is in *killing dead ideas
   sooner*. AutoFirm must make "recommend terminate" a first-class, non-penalized verdict of the
   validation playbook (a fail-closed default: if hypotheses are disconfirmed, the deterministic
   recommendation is STOP). This directly counters the over-persistence bias the paper documents.
3. **Pre-commit decision thresholds BEFORE testing** (the scientific framing). Encode go/pivot/stop
   thresholds as data set at hypothesis-creation time, so the verdict is deterministic and auditable
   - not rationalized after the fact. Feeds CLAUDE.md SS3.11 (explain every decision) and SS3.6
   (determinism tests: same evidence -> same verdict).

## REJECT / DEFER
- **Do NOT promise a revenue uplift from validation alone.** The revenue effect here is noisy; the
  robust effect is *decision quality*. AutoFirm's evidence charts must report validation as
  improving go/no-go calibration, NOT as a guaranteed revenue multiplier (avoids overfitting/overclaim).
- **Defer the "always 10 sessions" dosage** - that is an education-context artifact, not a platform
  parameter. AutoFirm runs continuous automated testing, not a fixed course.

## Quantified targets for evidence/
- Validation playbook must demonstrate, on the fixed industry panel, that disconfirming evidence
  produces a STOP/pivot verdict (measurable: % of seeded non-viable ideas correctly terminated).
- Determinism: identical hypothesis ledger + identical evidence -> identical verdict across N runs.
