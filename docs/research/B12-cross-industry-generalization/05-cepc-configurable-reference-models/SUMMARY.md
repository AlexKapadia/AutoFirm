# SUMMARY — Configurable Reference Process Models (C-EPC)

## Full citations (two linked primary works)
- **(A, empirical)** Recker, J., Rosemann, M. & van der Aalst, W. (2005). *On the User Perception
  of Configurable Reference Process Models - Initial Insights.* In B. Campbell, J. Underwood &
  D. Bunker (Eds.), *Proceedings of the 16th Australasian Conference on Information Systems (ACIS
  2005)*, Sydney, Australia, 29 Nov-2 Dec 2005. Queensland Univ. of Technology & Eindhoven Univ.
  of Technology. URL: https://eprints.qut.edu.au/2878/ (PDF: eprints.qut.edu.au/archive/00002878)
- **(B, foundational meta-model)** Rosemann, M. & van der Aalst, W.M.P. (2007). *A configurable
  reference modelling language.* *Information Systems*, 32(1), 1-23. Elsevier.
  DOI: 10.1016/j.is.2005.05.003 .
  URL: https://research.tue.nl/en/publications/a-configurable-reference-modelling-language-2

## Ontology questions informed
- **L1.B12.1** (PRIMARY) — the formal mechanism for making ONE general model serve many distinct
  organizations: configuration via marked variation points. This is the academic foundation for
  AutoFirm's "one playbook, parameterized per industry" thesis.

## GRADE tier
- (B) **Information Systems** (Elsevier) is a peer-reviewed top IS journal -> **High**.
- (A) ACIS conference paper -> **Moderate** (peer-reviewed venue, empirical study, smaller scope).
Two independent-enough artifacts (different venue/type) corroborating the C-EPC mechanism.

## Key claims with exact wording + locators

1. **Reference models must be configured, not rebuilt, per organization.** (A, Introduction):
   > "Enterprise Systems potentially lead to significant efficiency gains but require a
   > well-conducted configuration process. A configurable reference modelling language based on the
   > widely used EPC notation, which can be used to specify Configurable EPCs (C-EPCs), has been
   > developed to support the task of Enterprise Systems configuration."

2. **The C-EPC mechanism (configurable functions and connectors).** A C-EPC is an EPC in which
   selected **functions** and **connectors** are marked as **configurable** (variation points). A
   modeller derives an individualized model by **selecting a variant for each configurable
   element**: a configurable function may be set ON / OFF / OPT(ional); a configurable connector's
   logic (OR/XOR/AND) may be restricted/specialized. (B, meta-model.)

3. **Configuration requirements & guidelines (constraints).** The language adds
   **configuration requirements** (logical predicates over configuration choices that must hold,
   e.g. "if function A is OFF then connector C must be XOR") and **configuration guidelines**
   (recommended, non-mandatory choices). These keep every derived variant **lawful** (a valid EPC).

4. **Two decision scopes - the core insight.** (B) Traditional process languages "offer no
   opportunities to distinguish between decisions made for a single case when executing the process
   and decisions made in advance for numerous cases impacting bigger parts of the company."
   Configuration = decisions made **in advance, design-time, for many cases**; ordinary routing =
   **run-time, per-case**. C-EPC explicitly separates the two.

5. **Empirical finding (A).** Lab experiment comparing C-EPCs to regular EPCs (Method Adoption
   Model): C-EPCs "provide sufficient yet improvable conceptual support towards reference model
   configuration" - i.e. configurability is usable but the notation has ergonomic limits.

## Reproducibility note
(A) PDF is public on QUT ePrints (verified: cover sheet = Recker/Rosemann/van der Aalst 2005, ACIS
Sydney). (B) is the canonical journal version (Information Systems 32(1):1-23, 2007). The ON/OFF/OPT
function semantics and configuration-requirement/guideline constructs are defined in (B)'s meta-model.
