# SUMMARY — Programmatic Excel Generation: openpyxl vs XlsxWriter

## Full citation (primary docs)
- **openpyxl** — *openpyxl: A Python library to read/write Excel 2010 xlsx/xlsm files.* Official docs: https://openpyxl.readthedocs.io/ (maintained, OSS).
- **XlsxWriter** — *XlsxWriter: A Python module for creating Excel XLSX files.* John McNamara. Official docs: https://xlsxwriter.readthedocs.io/ ; https://xlsxwriter.com/ (OSS, BSD).
- Comparison cross-checked at https://xlsxwriter.com/xlsxwriter-vs-openpyxl/ and StringFest Analytics (independent).
- **Year:** both actively maintained as of 2026.

## Questions informed
- **L1.B15.1** (the programmatic-generation half — "live formulas, not dead values").

## GRADE tier
**Moderate–High** for library capability facts (official documentation = primary source for what the tool does; cross-corroborated by two independent comparisons). Directly verifiable against the libraries.

## Key claims (faithful)
1. **Both write live formulas as strings**, not dead values. Assigning a cell the text of a SUM formula writes a real formula; the value is computed by Excel/LibreOffice on open. Neither library has a calculation engine, so the cached value stays blank/0 until the file is opened — a critical correctness caveat.
2. **XlsxWriter** is **write-only** (cannot read/modify existing files); generally **faster** and more **feature-rich for creation** (rich formatting, charts, conditional formats, sparklines, data validation). Preferred when generating feature-rich files from scratch.
3. **openpyxl** can **read, write, and modify** existing .xlsx; better for editing existing files and reading formulas back; supports charts/formatting/multiple sheets but with fewer chart-customization options than XlsxWriter.
4. **pandas** uses either as an engine for to_excel — useful for bulk data dumps but not for engineered models (pandas writes values/tables, not a FAST-structured formula model).
5. **Neither computes formula results.** For a delivered model whose cached values must be correct (PDF render or downstream read), a recalculation step (LibreOffice headless convert, or Excel COM, or a pycel/formulas evaluator) is required.

## Reproducibility note
Write-only vs read/write, relative performance, and live-formula-as-string behaviour are stated in both libraries' official docs and corroborated by two independent comparison sources. The "no calc engine / cached value blank until opened" caveat is documented and widely reported. Cross-checked 2026-06-15.
