# 01 — Panko, *What We Know About Spreadsheet Errors*

- **Author / org:** Raymond R. Panko, University of Hawaii (Shidler College of Business).
- **Year:** 1998, revised 2008 (Journal of End User Computing / EuSpRIG). arXiv:0802.3457.
- **Link:** https://arxiv.org/pdf/0802.3457 ; canonical: http://panko.shidler.hawaii.edu/SSR/Mypapers/whatknow.htm
- **Tier:** High — the foundational peer-reviewed survey of spreadsheet error research.

## Faithful structured summary

The single most-cited evidence that **human producers cannot be trusted to verify their own
quantitative artifacts**, and that **inspection (review) is hard and incomplete**.

Key findings (figures as reported in Panko's published survey / abstract):
- **Prevalence:** the widely-quoted figure is that as many as **~90% of operational spreadsheets
  contain at least one error**.
- **Cell Error Rate (CER):** field audits report CERs of **0.4% to 6.9%**; lab studies find
  uncorrected errors in **>=~1% of formula cells**. A small per-cell rate compounds across a large
  model into near-certain model-level error.
- **Detection by inspection is incomplete:** across **nine experiments, >1,000 participants**, the
  **average error-detection rate in spreadsheet inspection is ~60%.** Subjects working **alone catch
  only about half of all errors**, even experienced developers.
- **Error type matters:** code inspection reaches **~90% detection only for mechanical typing/
  pointing errors in *short* formulas**; for **logic errors, mechanical errors in long formulas, and
  omission errors detection is far lower** (one study of 14 errors: three had detection <10%, half
  <40%).
- **Overconfidence / the "confidence gap":** developers dramatically **underestimate their own error
  rate** (the perceived-vs-actual gap B15 cited as ~18% perceived vs ~86% actual).

## Best parts to take (for our gate) and why

1. **Independent review is mandatory.** Self-review's ceiling (~50%, overconfident) is the empirical
   justification for the generator/evaluator split. Acceptance never comes from the builder.
2. **Mechanical recomputation beats human inspection exactly where humans fail** (long formulas,
   logic, omission). Our numeric-recomputation and accounting-identity checks must be deterministic
   recomputation, not "an agent eyeballs it."
3. **Omission is a first-class defect class** humans miss most → `FAST_LINT` statement-completeness.
4. **Quantify against this baseline:** report the gate's detection rate against human ~60% / solo
   ~50% in `evidence/`.
