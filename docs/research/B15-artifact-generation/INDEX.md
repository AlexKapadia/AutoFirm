# B15 — Professional Artifact-Generation Capability — INDEX

Branch covering ontology questions **L1.B15.1** (Excel/financial models), **L1.B15.2** (PowerPoint
decks), **L1.B15.3** (documents). Status: **seeded — pending QA/CRO PASS**.

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

Synthesis: `SYNTHESIS.md` (surveyed space + integrated engine recommendation for L2.B15).

## Alternative space surveyed (coverage map)
- **Excel standards:** FAST (adopt) · Operis (reject-as-sole) · SSRB · ad-hoc (reject).
- **Excel libs:** XlsxWriter (gen) · openpyxl (read/audit) · pandas.to_excel (reject for model) · raw OOXML (escape hatch).
- **Deck craft:** Minto · Zelazny · Tufte · IBCS SUCCESS (all adopt, IBCS integrates).
- **Deck lib:** python-pptx (+ custom master + raw-XML).
- **Documents:** python-docx (editable) · Typst (fixed PDF, adopt) · Pandoc+LaTeX/xelatex (fallback) · ReportLab/WeasyPrint (alt) · pdflatex (reject).
- **Substrate:** OOXML/OPC (all); legacy binary (reject).

## Open items for QA / next pass
- Hatmaker (04) exact per-measure formulae not machine-extractable this pass — deferred, not fabricated; AutoFirm to define its own auditable transparency metrics grounded in FAST.
- Operis and SSRB have no single open canonical URL; relied on Grossman & Ozluk (01) as the corroborating primary survey — a second independent Operis/SSRB primary would strengthen B15.1 to full ≥3-source depth on the "three convergent standards" claim.
