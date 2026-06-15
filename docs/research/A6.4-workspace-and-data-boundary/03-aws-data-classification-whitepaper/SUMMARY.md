# SUMMARY — AWS Data Classification: Models and Schemes

## Full citation
- **Title:** *Data Classification — Models and Schemes* (AWS Whitepaper)
- **Author/Org:** Amazon Web Services
- **Year:** Whitepaper (marked "historical reference"); content reflects schemes incl. EO 13526 and
  NIST FIPS 199 / SP 800-60
- **Venue/Publisher:** AWS Whitepapers
- **URL:** https://docs.aws.amazon.com/whitepapers/latest/data-classification/data-classification-models-and-schemes.html

## Question(s) it informs
- **L1.A6.4** — the menu of classification schemes (the *full alternative space* for "how many
  tiers, and what are they") and the recommendation to use the **minimal** number of tiers; maps
  classification → required controls (encryption) and deployment isolation.

## GRADE tier
- **Tier: Low–Moderate** (vendor whitepaper) but it faithfully reproduces **primary** government
  schemes (NIST, EO 13526, UK Govt) and a published book taxonomy (CISSP). Used for the
  *scheme-menu* and *minimal-tiers* recommendation; the NIST low/moderate/high it reproduces
  corroborates source 02.

## Key claims (with exact tables/numbers)
1. **Government vs commercial split:** government schemes are standardized (laws/EO); commercial
   schemes "are less standardized and depend on the respective organizational need."
2. **Commercial schemes range from a 2-tier (public/confidential) up to a 5-tier model.**
   The CISSP 5-tier (Table 1): *Sensitive, Confidential, Private, Proprietary, Public* — with
   *Public* = "the least sensitive data… would cause the least harm if disclosed," and *Sensitive*
   = "the most limited access… do the most damage… should it be disclosed."
3. **Enterprise 3-tier example (Table 3):** *Tier 3 Highly Strategic* (trade secrets, M&A, pricing,
   product designs — "severe or catastrophic legal, financial or reputational damage"); *Tier 2
   Restricted* (contracts, sales/marketing account data, HR records, legally-protected data);
   *Tier 1 Protected* (CRM, vendor bank/payment details, internal-use info).
4. **NIST categorization reproduced:** Low = "Limited adverse effect"; Moderate = "Serious adverse
   effect"; High = "Severe or catastrophic adverse effect" (corroborates source 02 verbatim).
5. **AWS recommendation (verbatim intent):** *"start with a three-tiered data classification
   approach"* and *"use the minimal number of tiers that make sense for the organization"*; use
   **secondary labels** rather than adding tiers for complex environments.
6. **Controls follow classification:** "Depending on the classification of the data, they will need
   to apply the relevant security controls (such as encryption)" and choose deployment isolation
   (public vs private/hybrid cloud) per tier.
7. **Quantitative datapoints:** FY2015 — U.S. federal agencies categorized **88%** of systems as
   low/moderate; UK (2013) categorized **~90%** of data as *Official* (the base tier).

## Up/down-rate reasoning
- Down-rated to Low–Moderate as a vendor doc marked "historical reference"; **up-rated** for the
  reproduced primary schemes and for cross-corroborating source 02's NIST definitions.

## Reproducibility note
All tables/quotes are on the linked AWS page (Tables 1–4 + the AWS recommendation section).
