# BEST-PARTS — McKinsey MGI → AutoFirm

## ADOPT
- **The ACTIVITY-LEVEL automation map as AutoFirm's PRIMARY automatability evidence base.** This is
  the most build-ready quantitative source in B2: it scores at the same granularity (activities)
  that AutoFirm delegates at, and gives concrete, citable feasibility numbers per activity TYPE.
  **Build implication:** the `automatability/feasibility_priors.py` table seeds each APQC-leaf
  process with a prior automation feasibility drawn from its dominant activity type:
  data-processing-heavy processes (invoicing, reconciliation, reporting) → ~69%;
  data-collection (research, monitoring) → ~64%; managing/coaching → ~9%; stakeholder/expertise →
  <20%. AutoFirm front-loads the high-feasibility processes in any client build.
- **The 18-capabilities-in-5-groups model** is the right *feature space* for scoring — richer than
  Frey-Osborne's 9 variables and explicitly capability-based. AutoFirm should map each task to the
  capabilities it requires, then check those against current agent/LLM capability (source 09).
- **The three headline ratios are AutoFirm's GUIDING DESIGN CONSTANTS (and the answer to L1.B2.3):**
  (1) **~50% of activities** technically automatable → AutoFirm targets *activities*, not jobs;
  (2) **<5% of jobs fully automatable** → AutoFirm is a *human-augmenting* company-builder, design
  for HITL by default, not full replacement; (3) **~60% of roles have ≥30% automatable** →
  the realistic per-role automation envelope to plan against. These feed `evidence/` directly.

## REJECT / use-with-care
- **Reject "technical potential" as "should-automate".** MGI is explicit that technical feasibility
  ≠ adoption (cost, regulation, ethics, social acceptance gate it). AutoFirm must layer a
  *business-case + compliance* filter (B5 cost, B10 legal) on top of the feasibility prior before
  deciding to automate — fail-closed where regulation is involved (CLAUDE §5.6).
- **Use-with-care: the 2017 numbers predate LLMs.** MGI's low scores for "applying expertise"
  (<20%) and "stakeholder interactions" (<20%) are materially raised by generative AI — UPDATE
  these priors with source 09 (Eloundou) before relying on them; do not present 2017 figures as
  current for cognitive/language tasks.

## Concrete build implication
- Component: `automatability/feasibility_priors.py` — maps each APQC activity type → MGI feasibility prior, blended with the LLM-era exposure from source 09; `evidence/` charts the three headline ratios as the platform's design constants.
- Test it drives: an efficacy test asserting AutoFirm's planner allocates high-feasibility (data-processing) processes to full-auto agents and low-feasibility (managing/stakeholder) processes to HITL, and that the blended prior for cognitive tasks exceeds the bare 2017 MGI value (proving the LLM-era uplift was applied).
