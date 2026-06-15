# SUMMARY — Fornell, Johnson, Anderson, Cha & Bryant (1996), "The American Customer Satisfaction Index: Nature, Purpose, and Findings"

## Full citation
- **Title:** The American Customer Satisfaction Index: Nature, Purpose, and Findings
- **Authors:** Claes Fornell; Michael D. Johnson; Eugene W. Anderson; Jaesung Cha; Barbara Everitt Bryant
- **Year:** 1996 (October, Vol. 60, No. 4)
- **Venue:** *Journal of Marketing* (American Marketing Association), pp. 7–18
- **DOI:** 10.1177/002224299606000403
- **URL:** https://journals.sagepub.com/doi/10.1177/002224299606000403 ; open mirror: https://ecommons.cornell.edu (Cornell eCommons)
- **Lineage:** ACSI (founded 1994 by Fornell) is modelled on the Swedish Customer Satisfaction Barometer (SCSB, 1989).

## Ontology question informed
- **L1.B9.1** — the rigorous, peer-reviewed CSAT measurement model.

## What the source claims (faithful)
- ACSI is a **cause-and-effect (causal) structural model** with latent constructs:
  - **Antecedents (drivers):** customer expectations, perceived quality, perceived value.
  - **Centre:** customer satisfaction (ACSI index).
  - **Consequences:** customer complaints and customer loyalty (retention, price tolerance).
- The ACSI index is a **weighted average of multiple survey items** (not a single question), with the model estimated by **partial least squares (PLS)** path modelling.
- The published ACSI is **reported on a 0–100 scale.** A common normalisation across three items (satisfaction, expectancy/confirmation, performance vs. ideal, each 1–10) is:
  `ACSI = ((mean(Q1) + mean(Q2) + mean(Q3)) − 3) / 27 × 100`  (maps the 3..30 raw sum onto 0..100).
- Methodologically distinguishes satisfaction from its antecedents; satisfaction is a latent variable inferred from several indicators, improving reliability over single-item CSAT.

## Source-quality grade (GRADE-adapted)
- **Tier: High.** Peer-reviewed *Journal of Marketing*; the foundational, widely-replicated national index; transparent econometric methodology (PLS).
- **Up-rate** for: longevity, national-scale data (~180,000 respondents/yr in operation), cross-industry replication.

## Reproducibility note
Model structure (3 antecedents → satisfaction → 2 consequences), PLS estimation, and 0–100 scaling are documented in the primary paper and the ACSI methodology report (https://www.reginfo.gov/public/do/DownloadDocument?objectID=36702901). The normalisation formula is reproducible from the three-item raw-score transform.
