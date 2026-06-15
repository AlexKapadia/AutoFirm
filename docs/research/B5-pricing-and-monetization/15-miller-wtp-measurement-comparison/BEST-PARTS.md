# BEST-PARTS — Miller et al. (2011) WTP-measurement comparison — what AutoFirm adopts

> Adopt/reject tied to cited evidence (DEPTH-RUBRIC §4-5). Closes the WTP-method survey gap
> (incentive-compatible elicitation + hypothetical bias) flagged in the AMBER review.

## ADOPT
- **A1. Hypothetical-bias correction on all stated-WTP inputs.** Because OE/CBC overstate WTP
  (Miller et al. 2011), AutoFirm's WTP layer **never** feeds a raw stated-WTP number straight into
  the price optimizer. *Build implication:* PSM (05) and Gabor-Granger/conjoint (06) outputs carry a
  **stated-preference flag** and a conservative **bias-discount** (or are bounded by the EVC ceiling),
  so the engine fails safe toward not overpricing. New invariant candidate for SYNTHESIS.
- **A2. Prefer incentive-aligned methods when a real-purchase context exists.** When AutoFirm can run
  a real or incentive-aligned test (e.g. live A/B pricing, ICBC), prefer it over purely hypothetical
  surveys - it is the only family that passed the REAL benchmark. *Build implication:* the WTP-method
  selector ranks BDM/ICBC/live-test above OE/standard-CBC; method choice is an explicit, logged
  decision (explainability §3.11).
- **A3. BDM as the reference incentive-compatible mechanism.** Adopt Becker-DeGroot-Marschak (1964)
  as the documented incentive-compatible elicitation pattern AutoFirm can deploy where a real
  transaction can close the loop. *Build implication:* available as a WTP-elicitation option in the
  toolkit; truthful-reporting property cited in its module docstring.
- **A4. Decision-relevance as the acceptance test.** Judge a WTP estimate by "would it change the
  recommended price?" (decision-oriented metric), not raw statistical fit. *Build implication:*
  WTP-layer evidence charts report decision-relevant deltas (price recommended under each method),
  feeding evidence/ (§3.10), not just point estimates.

## REJECT / DEFER
- **R1. REJECT trusting raw open-ended / non-incentive-aligned stated WTP as a price target.**
  Evidence: it fails the REAL benchmark and overstates (Miller et al. 2011). Use only as a loose
  range input, always bounded by EVC.
- **D1. DEFER full ICBC/hierarchical-Bayes conjoint estimation internals** to L2.B5-advanced (already
  excluded in SYNTHESIS scope boundary); here only the *method-selection rule* is fixed.

## Test / evidence hooks
- WTP inputs tagged stated vs incentive-aligned; stated-only inputs are bias-discounted/bounded by EVC.
- Method-selector test: given a real-purchase context, BDM/ICBC outrank OE/CBC (ordering assertion).
- Citation test: WTP-method module references Miller et al. (2011) DOI 10.1509/jmkr.48.1.172 and
  BDM (1964) DOI 10.1002/bs.3830090304.
