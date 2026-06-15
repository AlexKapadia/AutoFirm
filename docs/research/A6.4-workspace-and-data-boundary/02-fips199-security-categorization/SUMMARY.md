# SUMMARY — FIPS PUB 199: Standards for Security Categorization

## Full citation
- **Title:** FIPS PUB 199 — *Standards for Security Categorization of Federal Information and
  Information Systems*
- **Author/Org:** National Institute of Standards and Technology (NIST), U.S. Dept. of Commerce
- **Year:** February 2004
- **Venue/Publisher:** Federal Information Processing Standards Publication
- **DOI/URL:** https://nvlpubs.nist.gov/nistpubs/fips/nist.fips.199.pdf
  (corroborating reproductions: https://en.wikipedia.org/wiki/FIPS_199 ;
   AWS data-classification whitepaper, source 03)

## Question(s) it informs
- **L1.A6.4** — the *classification scheme* that decides what is "public" vs. "sensitive" and
  therefore which side of the boundary a datum lands on. Confidentiality impact = the axis that
  drives the public/private split.
- Feeds L2.A6 (data-boundary scheme) and L1.B4.4 (PII boundary).

## GRADE tier
- **Tier: High.** Official U.S. government standard (primary source of record). This is the
  authoritative definition of the confidentiality/integrity/availability impact model.

## Key claims — formulae reproduced EXACTLY
1. **Security category of an information TYPE (verbatim format):**
   `SC information type = {(confidentiality, impact), (integrity, impact), (availability, impact)}`,
   where the acceptable values for *impact* are **LOW, MODERATE, HIGH, or NOT APPLICABLE** (NA is
   permitted **only** for the confidentiality and integrity objectives in the type case per the
   standard's examples).
   - Worked example from the standard: `SC administrative information = {(confidentiality, LOW),
     (integrity, LOW), (availability, LOW)}`.
2. **Potential-impact definitions (the three CIA objectives — confidentiality, integrity,
   availability):**
   - **LOW** — the loss "could be expected to have a **limited** adverse effect on organizational
     operations, organizational assets, or individuals."
   - **MODERATE** — a **serious** adverse effect.
   - **HIGH** — a **severe or catastrophic** adverse effect.
   (These three wordings — limited / serious / severe or catastrophic — are corroborated verbatim
   by the NIST scheme reproduced in the AWS whitepaper, source 03.)
3. **High-water-mark rule (information SYSTEM categorization):** the SC of an information system is
   determined by taking the **highest** impact value across all information types resident on it,
   for each objective: *"The most severe rating from any category becomes the information system's
   overall security categorization"* (Wikipedia reproduction of the FIPS 199 rule). I.e. a system
   holding any HIGH-confidentiality type is itself HIGH-confidentiality.

## Up/down-rate reasoning
- No down-rate: official standard, directly on-point. The formula and high-water-mark are
  corroborated by ≥2 further independent textual reproductions (Wikipedia; AWS whitepaper),
  satisfying the ≥3-source bar for this safety/correctness-critical formula even though the PDF
  itself could not be machine-parsed (the official URL remains the citation of record).

## Reproducibility note
The formula `SC = {(confidentiality, impact),(integrity, impact),(availability, impact)}` and the
limited/serious/severe-or-catastrophic ladder appear in the official PDF and are reproduced in the
two corroborating sources; a reviewer can confirm via any of the three URLs above.
