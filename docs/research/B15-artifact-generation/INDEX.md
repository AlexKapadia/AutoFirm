# B15 — Professional Artifact-Generation Capability — INDEX

Branch covering ontology questions **L1.B15.1** (Excel/financial models), **L1.B15.2** (PowerPoint
decks), **L1.B15.3** (documents). Status: **strengthened (AMBER→GREEN pass) — independent corroboration added for the two prior gap areas**.

| # | Source folder | Source (primary) | Tier | Questions |
|---|---|---|---|---|
| 01 | `01-grossman-spreadsheet-engineering-methodologies/` | Grossman & Ozluk, *Spreadsheets Grow Up* (2010, EuSpRIG/arXiv:1008.4174) | Moderate | B15.1 |
| 02 | `02-panko-spreadsheet-errors/` | Panko, *What We Know About Spreadsheet Errors* (1998; EuSpRIG arXiv:0802.3457) | High | B15.1 |
| 03 | `03-fast-standard/` | The FAST Standard (FAST Standard Organisation, fast-standard.org) | High (primary std) | B15.1 |
| 04 | `04-hatmaker-spreadsheet-transparency/` | Hatmaker, *Proposed Spreadsheet Transparency Definition and Measures* (2018, arXiv:1802.01628) | Moderate | B15.1 |
| 05 | `05-python-excel-libraries/` | openpyxl & XlsxWriter official docs | Mod–High | B15.1 |
| 06 | `06-minto-pyramid-principle/` | Minto, *The Pyramid Principle* (1987) | High (primary) | B15.2 |
| 07 | `07-tufte-data-ink/` | Tufte, *The Visual Display of Quantitative Information* (1983) | High (primary) | B15.2 |
| 08 | `08-zelazny-say-it-with-charts/` | Zelazny, *Say It With Charts* (4th ed. 2001) | High (primary) | B15.2 |
| 09 | `09-ibcs-success-standard/` | Hichert & Faisst / IBCS Association, *IBCS Standards* (v1.2) | High (primary std) | B15.2/.3 |
| 10 | `10-python-pptx/` | python-pptx official docs (Canny) | Mod–High | B15.2 |
| 11 | `11-document-generation-pipelines/` | python-docx, Pandoc, LaTeX (Lamport), Typst — official docs/refs | Mod–High | B15.3 |
| 12 | `12-ooxml-standard/` | OOXML — ECMA-376 / ISO/IEC 29500:2008 | High (primary std) | B15.1/.2/.3 |
| 13 | `13-icaew-twenty-principles-financial-modelling-code/` | ICAEW, *Twenty Principles for Good Spreadsheet Practice* (2nd ed. 2018 / 2024) + *Financial Modelling Code* (2019) | High (primary std) | B15.1 |
| 14 | `14-powell-lawson-baker-operational-spreadsheet-errors/` | Powell, Lawson & Baker, *Impact of Errors in Operational Spreadsheets* (2008; EuSpRIG / *Decision Support Systems*, arXiv:0801.0715) | High (peer-reviewed empirical) | B15.1 |
| 15 | `15-kosslyn-clear-and-to-the-point/` | Kosslyn, *Clear and to the Point: 8 Psychological Principles for Compelling PowerPoint* (OUP, 2007) | High (primary, cognitive science) | B15.2 |

Synthesis: `SYNTHESIS.md` (surveyed space + integrated engine recommendation for L2.B15).

## Alternative space surveyed (coverage map)
- **Excel standards:** FAST (adopt) · ICAEW Twenty Principles + Financial Modelling Code (adopt, independent convergent corroboration) · Operis (reject-as-sole) · SSRB · ad-hoc (reject).
- **Excel libs:** XlsxWriter (gen) · openpyxl (read/audit) · pandas.to_excel (reject for model) · raw OOXML (escape hatch).
- **Deck craft:** Minto · Zelazny · Tufte · IBCS SUCCESS (all adopt, IBCS integrates) · Kosslyn 8 cognitive-science principles (adopt, supplies the perception/memory "why").
- **Deck lib:** python-pptx (+ custom master + raw-XML).
- **Documents:** python-docx (editable) · Typst (fixed PDF, adopt) · Pandoc+LaTeX/xelatex (fallback) · ReportLab/WeasyPrint (alt) · pdflatex (reject).
- **Substrate:** OOXML/OPC (all); legacy binary (reject).

## Gap closures (this pass — addressing AMBER)
- **CLOSED — convergent-model-standard ≥3-source depth (B15.1):** added ICAEW Twenty Principles +
  Financial Modelling Code (13), an independent chartered-accountancy standards body whose P10/P12/
  P13/P14/P15 match the FAST core and which formally recognizes FAST. The "convergent standards"
  claim now rests on FAST (03) + Grossman&Ozluk (01) + ICAEW (13).
- **CLOSED — spreadsheet-error-prevalence correctness-critical ≥3-source depth (B15.1):** added
  Powell/Lawson/Baker (14), an independent peer-reviewed empirical study (Dartmouth SERP, EuSpRIG /
  Decision Support Systems), corroborating Panko (02) and Grossman&Ozluk (01) from a different
  research group, with tool-beats-human auditing evidence.
- **CLOSED — deck-craft cross-discipline corroboration (B15.2):** added Kosslyn (15, OUP), a
  cognitive-neuroscience treatment supplying the perception/memory mechanism under the practitioner
  deck rules (Minto/Zelazny/Tufte/IBCS) — lifting B15.2 above practitioner-book-only.

## Open items for QA / next pass
- Hatmaker (04) exact per-measure formulae not machine-extractable this pass — deferred, not
  fabricated; AutoFirm to define its own auditable transparency metrics grounded in FAST/ICAEW.
- Operis OAK and SSRB remain behind vendor/closed access; convergence is now corroborated via ICAEW
  (13) instead, so this is no longer a blocking single-source dependency.
