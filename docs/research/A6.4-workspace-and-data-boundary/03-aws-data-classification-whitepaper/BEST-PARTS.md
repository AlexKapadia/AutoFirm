# BEST-PARTS — AWS Data Classification → AutoFirm

## ADOPT
1. **Use the MINIMAL tier count.** Per AWS's explicit recommendation ("three-tiered… minimal number
   of tiers"), AutoFirm should NOT invent a 5-tier scheme. Adopt **two operational tiers that drive
   the git boundary** — `PUBLIC` (version-controlled) and `PRIVATE` (gitignored + governed store) —
   optionally with **secondary labels** (`pii`, `finance`, `deal-doc`, `client`) for handling/
   retention, exactly as AWS recommends labels-over-tiers. **Build implication:** boundary logic
   stays simple/auditable (one bit decides commit-ability); labels add nuance without complexity.
2. **Map classification → controls.** AWS: controls (encryption) and deployment isolation follow the
   tier. AutoFirm: `PRIVATE` ⇒ encryption-at-rest (source 09) + data-layer tenant isolation
   (source 10) + never-deploy-to-public; `PUBLIC` ⇒ ordinary VCS.
3. **Anchor the "what counts as sensitive" list with the enterprise Table 3 examples:** trade
   secrets, M&A, pricing, product designs, signed contracts, sales account data, HR/employee
   records, vendor bank/payment details, CRM. These are exactly the artifacts AutoFirm generates
   for client companies (B15) → all default to `PRIVATE`. Directly satisfies CLAUDE.md §3.12.

## REJECT / QUALIFY
- **Reject the national-security tiers (Confidential/Secret/Top-Secret, EO 13526)** — wrong domain;
  AutoFirm is commercial. Keep them only as illustration of "confidentiality-only" schemes.
- **Qualify the "historical reference" status:** cite the *primary* schemes it reproduces (NIST,
  CISSP) rather than the whitepaper alone for any relied-upon definition.

## Concrete build implication
- **Component:** `classification-policy.yaml` enumerating the default-PRIVATE artifact list (from
  Table 3) + the secondary-label vocabulary.
- **Contract:** `{tier: PUBLIC|PRIVATE, labels: [...]}`; default-deny → unknown artifact = PRIVATE.
- **Test:** every artifact type AutoFirm produces (financial model, deck, contract, CRM export)
  asserts `tier == PRIVATE` by default; only explicitly-marked code/templates are PUBLIC.
