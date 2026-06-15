# SUMMARY — Programmatic Document Generation Pipelines (DOCX / PDF / Markdown)

## Full citation (primary docs/standards)
- **python-docx** — *python-docx: create/update Word .docx files.* Steve Canny et al. https://python-docx.readthedocs.io/ (v1.2.0; OSS, MIT).
- **Pandoc** — *Pandoc: a universal document converter.* John MacFarlane. https://pandoc.org/MANUAL.html (Haskell; GPL).
- **LaTeX** — Leslie Lamport, *LaTeX: A Document Preparation System* (1986; 2nd ed. 1994), Addison-Wesley; built on Knuth's TeX. https://www.latex-project.org/
- **Typst** — *Typst: a markup-based typesetting system.* Typst GmbH. https://typst.app/docs/ ; https://github.com/typst/typst (introduced 2023; Apache-2.0).

## Questions informed
- **L1.B15.3** (professional long-form documents — memos, reports, contracts; structure + programmatic generation).

## GRADE tier
**Moderate–High** for capability facts (official docs/standards = primary; cross-corroborated by independent comparisons). LaTeX (Lamport book) and Pandoc manual are primary references of record.

## Key claims (faithful)
1. **python-docx:** supports paragraphs, runs, **paragraph/character/table/numbering styles**, tables, images, built-in fonts/colours. **Limitations:** weaker complex-table support, **no headers/footers** management, **no footnotes/endnotes**, no page-level operations, no format conversion; verbose for complex layouts. Best when documents follow strict, logic-heavy rules and integrate with Python data.
2. **Pandoc:** converts among Markdown, HTML, LaTeX, DOCX, PDF (via LaTeX), and more. Recommended workflow: author in Markdown, render to professional PDF via a **LaTeX template** (e.g. Eisvogel / Wandmalfarbe pandoc-latex-template). Use **xelatex** (or lualatex) rather than pdflatex for Unicode and modern system fonts. Keeps source clean, portable, version-controlled.
3. **LaTeX:** the primary high-quality typesetting engine; best where exact typography, math, or a journal .cls is required; slower compiles, steep syntax, cryptic errors.
4. **Typst (2023):** modern alternative — **compiles in milliseconds** (vs seconds-minutes for LaTeX), cleaner Markdown-like syntax, clearer errors, **matches LaTeX typography quality**; has a **scripting/code mode** explicitly tested for **automatic document generation from templates** (invoices, certificates, reports), with programmatic tables. LaTeX still wins for journal-specific .cls files and very heavy math edge cases.
5. **PDF rendering alternatives:** ReportLab (direct PDF, programmatic) and WeasyPrint (HTML/CSS -> PDF) are additional routes for HTML-first or fully-programmatic PDF; Markdown->LaTeX->PDF (Pandoc) and Typst are the cleaner report routes.

## Reproducibility note
python-docx capabilities/limitations (no headers-footers/footnotes; style support), the Pandoc Markdown->LaTeX/xelatex->PDF workflow + Eisvogel template, and Typst's millisecond compile / scripting-for-templating are stated in the respective official docs and corroborated by independent comparisons. Cross-checked 2026-06-15.
