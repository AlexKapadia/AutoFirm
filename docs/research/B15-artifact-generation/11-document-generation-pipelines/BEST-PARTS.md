# BEST-PARTS — Document Generation Pipelines

## ADOPT
- **Route by deliverable type (no single tool):**
  - **Editable Word deliverables a client will edit** (memos, contracts, reports they revise) -> **python-docx** with a **custom company .docx template** (styles = design tokens). Native .docx, OOXML (source 12).
  - **High-typography fixed PDF reports** (IC memos, polished reports) -> author content in **Markdown**, render via **Pandoc + a custom LaTeX template** with **xelatex** (system fonts) — OR **Typst** for fast, scriptable, template-driven generation. Markdown source is clean, portable, version-controlled.
- **Typst as the default for programmatic, template-driven PDF reports** (millisecond compiles, scripting/code mode built for exactly this; LaTeX-quality typography) — best fit for AutoFirm's automated, iterated generation loop. **Keep LaTeX (via Pandoc)** as the fallback for journal .cls / heavy math.
- **Markdown as the canonical authoring/intermediate format** — separates *content* (versioned, diffable, agent-authored) from *rendering* (template), mirroring the deck storyline/render split (source 06).
- **Custom templates carry the brand layer** — anti-AI-slop typography (real type/spacing scale), not default Word/LaTeX defaults.

## REJECT
- **python-docx for high-typography fixed reports** — its missing headers/footers, footnotes, and weak complex tables make it wrong for polished PDF deliverables; use it only for editable .docx.
- **pdflatex default** — use xelatex/lualatex for Unicode + modern fonts (documented Pandoc gotcha).
- **Raw HTML-as-document** without a print-CSS/typeset step — fails the institution-grade typography bar.

## BUILD IMPLICATION
`document_builder` is a **router**: (editable .docx -> python-docx+template) | (fixed PDF report -> Markdown -> Typst, fallback Pandoc+xelatex). Content authored as Markdown/structured data; rendering via custom company templates (design tokens). DoD: opens clean, correct headers/footers/page numbers, template fonts applied (not defaults), deterministic render (same input -> byte-stable-enough PDF for diffing). Ties document structure/tone to the per-deliverable contract.
