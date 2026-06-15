# BEST-PARTS — Non-dilutive & debt capital (SBIR/STTR, RBF, venture debt)

## ADOPT

- **Adopt the full non-equity menu as first-class options in the source ranker**, so AutoFirm does
  not default to dilutive equity:
  - **Grants (SBIR/STTR):** non-dilutive, milestone/R&D-gated, slow, eligibility-constrained (US
    small business, qualifying R&D). Model as a "free" capital source with eligibility gates + a
    timeline cost.
  - **RBF:** non-dilutive, repayment = % of recurring revenue, fast (weeks), preserves cap table;
    best for predictable-recurring-revenue clients (SaaS, subscription, marketplace take-rate).
  - **Venture debt:** low-dilution (warrants ~0.1-1.0%), fixed term + interest, requires traction +
    VC backing; used to **extend runway between equity rounds**.
- **Adopt dilution-tolerance + revenue-profile + stage as the selection axes** among these (e.g.
  recurring-revenue client favoring cap-table preservation -> RBF; deep-tech pre-revenue US startup
  -> SBIR first; VC-backed Series A needing runway -> venture debt).

## REJECT

- **Reject treating grants as a primary/reliable funding line.** SBIR is competitive, slow, capped,
  and eligibility-restricted (US, R&D, small business) — it cannot fund most operating needs and
  excludes many B12 industries (e.g. restaurants, generic services). Surface it only when eligible.
- **Reject the vendor RBF/venture-debt quantitative claims as authoritative** (Low GRADE tier): use
  the *mechanics* (corroborated across sources) but flag exact cost/dilution numbers as indicative
  until validated against a higher-tier source.

## Concrete build implication

- **Component:** extend `financing_source_ranker` (source 03) with grant/RBF/venture-debt candidates,
  each with an **eligibility predicate** (e.g. `is_sbir_eligible(country, is_small_business,
  has_qualifying_RnD)`, `has_predictable_recurring_revenue` for RBF, `has_vc_backing AND
  has_traction` for venture debt) and a cost/dilution/timeline profile.
- **Contract:** SBIR award caps stored with effective date (statutory, re-fetchable), never hard-coded
  silently. Fail-closed on eligibility: if eligibility is unknown, the option is NOT recommended
  (CLAUDE.md §5.6 fail-closed).
- **Test:** run the 8 B12 panel rows — assert a US deep-tech SaaS sees SBIR + RBF + venture debt,
  while a B2C restaurant correctly sees neither SBIR nor RBF (generality + no-overfit,
  CLAUDE.md §3.9).
