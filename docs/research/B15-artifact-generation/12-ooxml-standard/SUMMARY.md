# SUMMARY — Office Open XML (ECMA-376 / ISO/IEC 29500)

## Full citation
- **Title:** *Office Open XML File Formats* — ECMA-376; ISO/IEC 29500:2008 (and later editions).
- **Author/Org:** Ecma International (TC45); subsequently ISO/IEC JTC 1/SC 34. Format originated by Microsoft.
- **Year:** Standardized Dec 2006 (ECMA-376) then ISO/IEC 29500:2008; editions through 2016.
- **Venue:** Ecma International / ISO/IEC (official international standard).
- **URL/DOI:** https://ecma-international.org/publications-and-standards/standards/ecma-376/ ; ISO/IEC 29500 ; LoC format registry FDD000398.

## Questions informed
- **L1.B15.1, L1.B15.2, L1.B15.3** (the common file-format substrate under all three artifact types — .xlsx, .pptx, .docx).

## GRADE tier
**High.** Official international standard (primary source of record). Not down-rated.

## Key claims (faithful)
1. OOXML is a **zipped, XML-based** family of formats for spreadsheets, presentations, and word-processing documents — standardized first as **ECMA-376**, then **ISO/IEC 29500:2008**.
2. **Three principal schemas:** **WordprocessingML** (.docx), **SpreadsheetML** (.xlsx), **PresentationML** (.pptx).
3. Documents are stored in **Open Packaging Conventions (OPC)** packages — a ZIP container of XML parts plus a manifest of relationships between them.
4. The ISO/IEC standard is structured in parts; **Part 2 (Open Packaging Conventions)** is reused by other formats (XPS, Design Web Format).
5. Implication: every Python lib (openpyxl, XlsxWriter, python-pptx, python-docx) ultimately reads/writes OPC ZIP packages of OOXML parts; features a library does not expose can be reached by **manipulating the underlying Open XML directly**.

## Reproducibility note
ECMA-376 / ISO/IEC 29500 status, the three schemas, and OPC ZIP packaging are stated in the official Ecma/ISO registries and the Library of Congress format registry (FDD000398). Cross-checked 2026-06-15.
