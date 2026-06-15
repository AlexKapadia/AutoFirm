# SUMMARY — Impact of Errors in Operational Spreadsheets (Powell, Lawson & Baker)

## Full citation
- **Title:** *Impact of Errors in Operational Spreadsheets*.
- **Authors:** Stephen G. Powell, Barry Lawson, Kenneth R. Baker (Tuck School of Business,
  Dartmouth — Spreadsheet Engineering Research Project, SERP).
- **Year:** 2008 (submitted Jan 2008; EuSpRIG 2007 proceedings; journal version 2009).
- **Venue:** EuSpRIG 2007 Proceedings, pp. 57–68 (ISBN 978-905617-58-6); journal version
  *Decision Support Systems* (Elsevier), DOI 10.1016/j.dss.2009.02.002 (S0167923609000335).
- **URL/DOI:** https://arxiv.org/abs/0801.0715 ; https://arxiv.org/pdf/0801.0715 ;
  http://mba.tuck.dartmouth.edu/spreadsheet/product_pubs_files/impact.pdf ;
  https://www.sciencedirect.com/science/article/abs/pii/S0167923609000335
- **Companion (auditing protocol):** Powell, Baker & Lawson, *An Auditing Protocol for Spreadsheet
  Models*, 2007 (https://arxiv.org/abs/0801.0715 family; ResearchGate 222826446).

## Questions informed
- **L1.B15.1** (independent empirical corroboration of spreadsheet-error prevalence, the error
  taxonomy, and the tool-vs-human auditing evidence — distinct authors/org from Panko).

## GRADE tier
**High** — peer-reviewed empirical field study (journal + EuSpRIG), real operational spreadsheets,
fully documented method. Independent of Panko (different research group, the Dartmouth SERP), so it
*corroborates rather than re-cites* the prevalence/taxonomy findings. Up-rated: consistent, large
effect replicated across an independent corpus.

## Key claims (faithful, exact numbers + locators)
1. **Prior corpus (50 spreadsheets):** "we found errors in **0.8% to 1.8% of all formula cells**,
   depending on how errors are defined" (abstract) — an independent cell-error-rate band consistent
   with Panko's low-single-digit CER.
2. **Impact study (25 operational spreadsheets, 5 organizations):** **381 potential errors**
   identified, of which **117 (31%) were confirmed as errors by the developers**. Finding: "many
   errors have no quantitative impact… those that have an impact often affect unimportant portions…
   the remaining errors do sometimes have substantial impacts on key aspects." (Largest single
   confirmed error impact cited in the SERP work: on the order of **US$100 million**.)
3. **Tool-vs-human auditing (auditing-protocol companion):** an inspection protocol that runs two
   automated error-inspection programs first, then human inspection of remaining formulas; the
   automated tools caught all but **~17.8%** of the errors found — i.e. **automated tooling
   outperformed unaided human inspection** at finding errors.
4. **Taxonomy stance:** Powell/Baker/Lawson explicitly hold there is **"no one single correct
   categorization"** of spreadsheet errors, and refine prior schemes particularly on **omission**
   errors and **hard-coding** — directly relevant to the omission/hard-coding checks the audit gate
   must run.

## Reproducibility note
Numbers (50-sheet 0.8–1.8% band; 25-sheet 381→117/31% confirmed; ~17.8% missed by tools) are
quoted from the arXiv abstract and the documented EuSpRIG/journal study. The US$100M figure is the
widely-cited SERP largest-impact case; treated as supporting, not load-bearing. A reviewer
re-derives corroboration by comparing this group's prevalence/CER and taxonomy against Panko (02)
and Grossman & Ozluk (01) — three independent groups, same qualitative conclusion.
