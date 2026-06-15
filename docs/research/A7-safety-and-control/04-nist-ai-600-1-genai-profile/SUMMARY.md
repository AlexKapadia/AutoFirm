# SUMMARY — NIST AI RMF + Generative AI Profile (NIST AI 600-1)

## Full citation
- **Titles:** (a) Artificial Intelligence Risk Management Framework (AI RMF 1.0), **NIST AI 100-1**; (b) Artificial Intelligence Risk Management Framework: Generative Artificial Intelligence Profile, **NIST AI 600-1**.
- **Author/Org:** National Institute of Standards and Technology (NIST), U.S. Department of Commerce.
- **Years:** AI 100-1 released **2023-01-26**; AI 600-1 released **2024-07-26**.
- **Venue/Publisher:** NIST (U.S. federal standards body).
- **URL:** https://www.nist.gov/itl/ai-risk-management-framework ; AI 600-1 doc page https://digitalgovernmenthub.org/examples/nist-artificial-intelligence-risk-management-framework-generative-artificial-intelligence-profile/

## Questions informed
- **L1.A7.1** (primary) — authoritative GenAI risk taxonomy + governance functions. Secondary: A6 governance, A9 measurement.

## GRADE tier
**High.** Official U.S. government standard; the canonical risk-management reference, used as a primary anchor (DEPTH-RUBRIC §2 "official standard").

## Key claims (faithful, exact)
1. **Four core functions of the AI RMF (NIST AI 100-1):** **GOVERN, MAP, MEASURE, MANAGE.** GOVERN is cross-cutting.
2. **NIST AI 600-1 defines 12 risk categories unique to or exacerbated by generative AI** (the official list, exact names):
   1. CBRN Information or Capabilities
   2. Confabulation (hallucination of false/misleading content)
   3. Dangerous, Violent, or Hateful Content
   4. Data Privacy
   5. Environmental Impacts
   6. Harmful Bias and Homogenization
   7. Human-AI Configuration
   8. Information Integrity
   9. **Information Security** (explicitly includes **prompt injection** and model extraction)
   10. Intellectual Property
   11. Obscene, Degrading, and/or Abusive Content
   12. Value Chain and Component Integration (third-party model/dependency risk)
3. **Four risk-management considerations** the GenAI Profile's suggested actions are organized around: **Governance, Pre-deployment Testing, Content Provenance, Incident Disclosure** — each mapped to AI RMF subcategories (GOVERN/MAP/MEASURE/MANAGE).
4. **Information Security risk** is the row that contains prompt injection — directly relevant to L1.A7.1.
5. **Value Chain and Component Integration** captures supply-chain/third-party dependency risk (corroborates source 03 supply-chain class).

## Verification note
Core-function names and the AI 100-1/600-1 identifiers + dates fetched from nist.gov. The 12-risk list cross-checked across three independent secondary catalogues (Modulos docs, AI Safety Directory, AI Governance Institute) which agree on all 12 names; the canonical source of record is NIST AI 600-1 itself (the nist.gov page confirms its existence and date but does not enumerate the 12 on that landing page — the enumeration is in the PDF). Per DEPTH-RUBRIC §1, the 12-item list is corroborated by >=3 independent sources plus the official document existence.

## Reproducibility
Download NIST AI 600-1 PDF from nist.gov; risks are enumerated in the Risk section; the four considerations head the Suggested Actions section.
