# SUMMARY — Legality of accessing public data: hiQ v. LinkedIn & Van Buren v. United States

## Full citations
1. **hiQ Labs, Inc. v. LinkedIn Corp.**, 31 F.4th 1180 (9th Cir. 2022) (on remand from the U.S. Supreme Court, *LinkedIn v. hiQ*, 141 S. Ct. 2752 (2021), vacating & remanding 938 F.3d 985 (9th Cir. 2019) in light of *Van Buren*). Decided **18 April 2022**.
   - Wikipedia overview: https://en.wikipedia.org/wiki/HiQ_Labs_v._LinkedIn
   - Practitioner analyses (corroborating): Morgan Lewis, Goodwin, Fenwick, Jenner & Block (URLs in BEST-PARTS).
2. **Van Buren v. United States**, 593 U.S. ___, **141 S. Ct. 1648 (2021)** (decided 3 June 2021; opinion by Barrett, J., 6-3).
   - Slip opinion (primary): https://www.supremecourt.gov/opinions/20pdf/19-783_k53l.pdf
   - Congressional Research Service summary (LSB10616): https://www.congress.gov/crs-product/LSB10616
   - Wikipedia: https://en.wikipedia.org/wiki/Van_Buren_v._United_States

## Questions informed
- **L1.B4.4** Public-data sourcing + PII boundary — the legal basis (US, 9th Cir. / SCOTUS) for AutoFirm accessing publicly-available data, and where the hard line sits.

## GRADE tier
- **High** for the holdings (one is a U.S. Supreme Court decision, the other a published Court of Appeals opinion — primary legal authority, top tier). Practitioner law-firm alerts are Low-tier color that corroborate the holding; the holdings themselves are quoted from the courts.

## Key claims (exact holdings)

1. **Van Buren (SCOTUS, 2021): narrow reading of "exceeds authorized access" under the CFAA.** The Court held 6-3 that "an individual 'exceeds authorized access' when he accesses a computer with authorization but then obtains information located in particular areas of the computer -- such as files, folders, or databases -- that are off-limits to him." Misusing data one is *entitled* to access (e.g. for an improper purpose) is **not** a CFAA violation. The Court adopted the **"gates-up-or-down"** approach: liability turns on whether you were authorized to access the area at all, not on why you accessed it. (Facts: a police sergeant ran a license-plate lookup in a database he was authorized to use, for a bribe — held NOT to "exceed authorized access.")

2. **hiQ v. LinkedIn (9th Cir., 2022): scraping public data likely does not violate the CFAA.** On remand applying *Van Buren*, the Ninth Circuit reaffirmed its preliminary-injunction holding: "scraping such public information likely does not constitute accessing a computer 'without authorization' under the CFAA." Reasoning: "one cannot 'access without authorization' a website for which no authorization is required in the first place" — i.e. publicly-available web data has the gate "up" for everyone, so the CFAA's "without authorization" prong is not triggered.

3. **The boundary (critical for AutoFirm):**
   - The CFAA ruling concerns **public** data with **no authentication gate**. It does **not** bless (a) bypassing a login/auth wall, (b) breaching a contract / Terms of Service (a separate, non-CFAA cause of action — and indeed hiQ ultimately settled and agreed to a permanent injunction over the LinkedIn user agreement, December 2022), or (c) scraping personal data in violation of privacy laws (GDPR/CCPA).
   - So: CFAA does not criminalize scraping truly public data, BUT ToS/contract law, copyright, and data-protection law remain independent constraints.

## Reproducibility note
Van Buren is quotable from the SCOTUS slip opinion (No. 19-783) and summarized in CRS LSB10616; the hiQ 2022 holding is in 31 F.4th 1180. The "gates-up-or-down" framing is from the Van Buren majority opinion. A reviewer can pull both primary opinions to confirm.
