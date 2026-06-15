# BEST-PARTS — NAICS 2017 Manual

## ADOPT

1. **NAICS as the canonical industry-parameterization key for AutoFirm playbooks.** Every company
   AutoFirm builds/operates gets a NAICS code (2–6 digit). Playbooks are parameterized by the
   **prefix length**: sector (2-digit) selects the coarse playbook variant; subsector/industry
   (3–5 digit) selects finer overrides. This gives a *graceful-degradation* lookup: if no
   6-digit override exists, fall back to 5 → 4 → 3 → 2 → cross-industry default. Build implication:
   a `IndustryProfile` data contract keyed by NAICS code with prefix-fallback resolution.

2. **Production-process similarity as the right grouping axis for OPERATIONS playbooks.** NAICS
   groups by *how* output is produced (inputs→process→outputs), which maps directly to the
   parts of a business playbook that vary by physical/digital production (B11 operations,
   B4.3 capacity/throughput). Adopt NAICS for the **supply/delivery/operations** dimension.

3. **The 5-digit international level as the stable parameter; 6th digit as optional override.**
   AutoFirm should key playbooks at the 5-digit (internationally comparable) level by default so
   the parameterization is not US-locked, treating the 6th digit as a rarely-needed national
   override. This keeps "any company in any country" generalizable.

4. **The fixed-panel mapping is testable.** Each row of the QUESTION-ONTOLOGY B12 fixed industry
   panel maps to a NAICS code (e.g. B2B SaaS → 5112/5415 software; manufacturing → 31–33; e-commerce
   → 4541; restaurant → 7225; fintech → 522/523; healthcare → 62). A generalization test asserts a
   sensible playbook resolves for every panel NAICS prefix.

## REJECT / use with caution

1. **REJECT NAICS as the *primary* key for go-to-market playbooks.** NAICS is supply/production-
   oriented, NOT demand- or customer-oriented. Marketing/sales/pricing playbooks (B5/B7/B8) vary by
   *who the customer is* (B2B vs B2C, buyer journey) more than by production process. Use NAICS for
   ops; use a separate **business-model/GTM dimension** (B2B/B2C, regulated?, physical/digital — the
   panel's own columns) for GTM. Rationale: NAICS's single production principle (claim 1) explicitly
   excludes demand-side grouping.

2. **REJECT treating NAICS codes as fine-grained behavioral predictors.** A 6-digit code identifies
   a production category, not a strategy; do not hard-code playbook *content* per 6-digit code
   (overfitting risk, DEPTH-RUBRIC §6). Keep the variation as *parameters/overrides on a general
   playbook*, never as 1,000+ bespoke playbooks.

## Build implication (concrete)
- Contract: `IndustryProfile { naics_code: str(2-6), gics_code: optional, business_model_axes: {b2b_b2c, regulated_tier, physical_digital} }`.
- Resolver: `resolve_playbook_variant(naics_code)` does longest-prefix match against a variant table,
  falling back to the cross-industry default — proving generality, not enumeration.
- Test: for all 8 fixed-panel NAICS prefixes, `resolve_playbook_variant` returns non-null and the
  ops parameters differ sensibly (physical vs digital), feeding the B12 generalization golden set.
