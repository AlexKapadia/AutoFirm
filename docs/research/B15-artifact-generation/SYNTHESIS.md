# SYNTHESIS — B15 Professional Artifact Generation (L1.B15.1 / .2 / .3)

> Feeds **L2.B15** (the AutoFirm artifact-generation engine) and L3.BUSINESS. Runs under the
> **L1.A6.4** workspace/data boundary (writes into the private workspace, never the public repo);
> model logic ties to **L1.B4.1** (3-statement/DCF). One-folder-per-source library lives alongside.

## 1. The question
How are best-in-class business artifacts — (1) Excel financial models, (2) PowerPoint decks,
(3) long-form documents — *actually* produced, so AutoFirm agents generate **genuinely excellent,
non-templated** deliverables, with **live formulas (not dead values)**, **message-titled
storylines**, and **no AI-slop look**?

## 2. Surveyed alternative space (with ADOPT/REJECT)

### 2.1 Excel / financial models (L1.B15.1)
**Model-build STANDARDS surveyed:** FAST (03) · **ICAEW Twenty Principles + Financial Modelling
Code (13)** · Operis · SSRB/Best-Practice (Grossman & Ozluk, 01) · ad-hoc/no-standard (rejected —
Panko 02 + Powell/Lawson/Baker 14 show ~90% of unmanaged spreadsheets contain errors).
- **ADOPT: FAST** as the default style contract (openly published, governed, machine-encodable),
  taking the **convergent core the standards share** — separate Inputs/Calculations/Outputs;
  one consistent formula per row; no embedded constants; consistent semantic colour-coding;
  short readable formulas; driver-based flexibility. **The convergence is now corroborated by ≥3
  independent bodies:** ICAEW (13), an independent chartered-accountancy standards body, authors the
  *same* structural rules (P10 separate inputs/workings/outputs · P12 consistent formulae · P13
  short/simple · P14 no embedded constants · P15 calculate-once-then-reference) AND formally
  recognizes FAST — closing the prior single-corroborator gap (FAST 03 + Grossman&Ozluk 01 + ICAEW
  13).
- **ADOPT additional ICAEW machine-checkable rules:** documentation sheet (P7), built-in
  integrity-check rows (P19), version/provenance on save (P17).
- **REJECT** committing to Operis's heavy named-range idiom as the only style (hurts
  machine-generation readability); **REJECT** ad-hoc generation outright.

**GENERATION libraries surveyed:** XlsxWriter · openpyxl · pandas.to_excel · raw OOXML (05/12).
- **ADOPT: XlsxWriter** to *generate* (fast, richest formatting/charts), **openpyxl** to *read/audit*,
  **live = formulas not values**, and a **mandatory LibreOffice-headless recalc/verify** step
  (neither lib computes formula results — cached values are blank until opened).
- **REJECT: pandas.to_excel** for the model body (dumps dead values, destroys FAST structure).

### 2.2 PowerPoint / decks (L1.B15.2)
**Storyline/craft standards surveyed:** Minto Pyramid (06) · Zelazny message-to-chart (08) · Tufte
data-ink/chartjunk (07) · IBCS SUCCESS (09) · **Kosslyn cognitive-science principles (15)**.
- **ADOPT Kosslyn's 8 principles as the cognitive "why" under the practitioner rules** — each deck
  rule now carries a craft authority *and* a perception/memory mechanism (Capacity Limitations ↔
  one-message-per-slide/MECE; Salience+Discriminability ↔ IBCS/Tufte contrast; Informative Changes ↔
  Tufte data-ink/no-decoration; Compatibility ↔ Zelazny message→chart; Perceptual Organization ↔
  grouping). Lifts B15.2 above practitioner-book-only corroboration.
- **ADOPT all four, integrated by IBCS SUCCESS** as the master rubric:
  - **Minto** -> answer-first storyline tree + **action/message titles** (full-sentence claims).
  - **Zelazny** -> deterministic **message-type -> chart-family** selector (component->pie,
    item->bar, time->column, frequency->histogram, correlation->scatter).
  - **Tufte** -> **maximize-data-ink / chartjunk lint** (no 3D, no heavy gridlines, no decoration).
  - **IBCS SUCCESS (7 rules)** -> scoring rubric + **semantic notation** (UNIFY: fixed visual
    vocabulary for actual/plan/forecast/variance) + **CHECK** (no misleading axes).
- **REJECT:** topic-label titles, data-first ordering, default theme Accent 1-6 palette, 3D charts,
  many-slice pie charts, kitchen-sink multi-message exhibits.

**GENERATION library:** python-pptx (10) + custom company master/template (design tokens) +
raw-OOXML escape hatch (12) for premium formatting beyond library defaults.

### 2.3 Documents (L1.B15.3)
**Pipelines surveyed:** python-docx · Pandoc(Markdown->LaTeX->PDF, xelatex) · LaTeX · Typst ·
ReportLab · WeasyPrint (11).
- **ADOPT a ROUTER by deliverable type:** editable Word (memos/contracts the client edits) ->
  **python-docx + custom .docx template**; high-typography fixed PDF reports -> **Markdown ->
  Typst** (millisecond compiles, scripting built for templated report generation, LaTeX-quality
  typography), **fallback Pandoc + LaTeX/xelatex** for journal .cls / heavy math.
- **ADOPT Markdown/structured-data as canonical authoring** (content vs rendering split).
- **REJECT:** python-docx for high-typography fixed PDFs (no footnotes/headers-footers, weak
  tables); pdflatex (use xelatex); raw HTML without a print-typeset step.

### 2.4 Common substrate (all three)
**OOXML / ECMA-376 / ISO/IEC 29500** (12): all outputs are OPC ZIP packages of XML parts; the
**raw-XML escape hatch** is the standards-backed path to premium, non-templated formatting;
**generate only OOXML** (.xlsx/.pptx/.docx), never legacy binary.

## 3. The integrated engine (build implication for L2.B15)

Pipeline (data + per-company design tokens + IBCS semantic notation flow in at the top):

1. **financial_model_builder** (XlsxWriter, FAST contract, live formulas)
   -> LibreOffice-headless recalc/verify
   -> **spreadsheet_audit_gate** (openpyxl): fast_lint + Panko error-class checks
   (mechanical/logic/omission) + accounting-identity checks (A = L + E, exact) + transparency_score.
2. **deck_storyline_planner** (Minto tree, MECE, action titles)
   -> **chart_type_selector** (Zelazny) -> **chart_styler** (Tufte + IBCS)
   -> **deck_renderer** (python-pptx + custom master + raw-XML hatch)
   -> **success_rubric** evaluator (IBCS 7) + visual_integrity_lint.
3. **document_builder** (router): editable .docx -> python-docx + template; fixed PDF -> Typst
   (fallback Pandoc + xelatex).
4. **ALL** -> file_opens_clean (valid OOXML/PDF, no repair) -> private workspace (L1.A6.4).

**Generator/evaluator split (Panko's confidence gap, 02):** acceptance NEVER comes from the
builder's self-assessment (humans estimate 18% error vs actual 86%); an **independent evaluator
agent** grades against the rubric/audit gate before delivery (CLAUDE §4.9).

## 4. Tests with teeth (CLAUDE §3.6) this research mandates
- **Spreadsheet:** orphan-constant detector; row-formula consistency; statement completeness
  (omission defence); **accounting identities exact to the unit** (zero numerical error, §3.11);
  determinism (same inputs -> identical recalculated cached values); mutation: inject mechanical/
  logic/omission faults, confirm the audit gate KILLS each.
- **Deck:** title-is-assertion; title-readthrough coherence; MECE grouping; message-type->chart-type
  match (reject mismatches); chartjunk lint (no 3D/heavy gridlines/default Accent palette);
  IBCS SUCCESS 7-rule pass; visual-integrity (no truncated/misleading axes).
- **Document:** opens clean; correct headers/footers/page numbers; template fonts applied (not
  defaults); deterministic render.
- **All:** file_opens_clean (valid OOXML/PDF, no repair prompt via LibreOffice headless).

## 5. Quantified efficacy for `evidence/` (CLAUDE §3.10)
Per generated artifact: spreadsheet **error-class kill rate** (target ~100% on injected faults),
**transparency_score** (FAST/Hatmaker), **data-ink-ratio proxy** per chart, **IBCS SUCCESS rule
pass-rate**, recalc-determinism pass. Plotting/recalc deps go in an **analysis-only** manifest,
never the runtime one (CLAUDE §3.10).

## 6. Generality (not overfit — CLAUDE §3.9)
Every rule is **standard-based and parameterized**, not fitted to one company: FAST/IBCS/Minto/
Zelazny/Tufte are industry-agnostic; design tokens + IBCS semantic notation are **per-company
config**, not hard-coded. The engine must produce a sensible artifact for **every** row of the
fixed industry panel (QUESTION-ONTOLOGY B12), proven by tests over diverse inputs.

## 7. Dependencies & data boundary
Depends on **L1.B4.1** (financial-model logic) and writes exclusively into the **private workspace**
per **L1.A6.4 / CLAUDE §3.12** — generated client artifacts (which may embed company-sensitive data)
are NEVER committed to the public repo or used as public-data validation fixtures. Synthetic-only
for any sensitive content in tests.

## 8. Source quality summary
High (primary): FAST Standard (03), **ICAEW Twenty Principles + Financial Modelling Code (13)**,
OOXML/ISO 29500 (12), Tufte (07), Zelazny (08), IBCS (09), Minto (06), Panko taxonomy (02),
**Powell/Lawson/Baker empirical study (14)**, **Kosslyn cognitive-science principles (15)**.
Moderate: Grossman & Ozluk (01), Hatmaker (04), library docs (05, 10, 11). No claim rests on a
single Very-low source. **Every safety/correctness-critical and architecture-level claim now meets
the DEPTH-RUBRIC §1 source minimum from INDEPENDENT bodies:**
- **Spreadsheet-error prevalence / audit-mandate (correctness-critical, ≥3):** Panko (02) +
  Powell/Lawson/Baker (14, Dartmouth SERP) + Grossman&Ozluk (01) — three independent research
  groups.
- **Convergent model-build standard (architecture, ≥3):** FAST (03) + Grossman&Ozluk (01) + ICAEW
  (13) — independent standards bodies; ICAEW also officially recognizes FAST.
- **Deck austerity / structure (≥2, now cross-discipline):** Tufte (07) + IBCS (09) + Kosslyn (15)
  for chart austerity; Minto (06) + IBCS-STRUCTURE + Kosslyn Capacity-Limitations (15) for
  one-message storyline; Zelazny (08) + Kosslyn Compatibility (15) for message→chart matching.
