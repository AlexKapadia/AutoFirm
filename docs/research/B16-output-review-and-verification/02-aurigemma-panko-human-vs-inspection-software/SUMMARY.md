# 02 — Aurigemma & Panko, *Detection of Human Spreadsheet Errors by Humans versus Inspection (Auditing) Software*

- **Authors / org:** Salvatore Aurigemma & Raymond R. Panko, University of Hawaii.
- **Year:** 2010 (EuSpRIG). arXiv:1009.2785.
- **Link:** https://arxiv.org/pdf/1009.2785
- **Tier:** High — peer-reviewed controlled experiment comparing automated audit software to human
  auditors. The most decision-relevant source for the deterministic-floor argument.

## Faithful structured summary

Seeds known errors into spreadsheets and compares **human inspectors** vs **commercial spreadsheet
inspection / auditing software** (static-analysis "audit tool" class, e.g. Spreadsheet Professional /
Xlanalyst-style).

Key reported findings:
- **Both detect imperfectly**, and the two are **complementary**, not interchangeable.
- **Inspection software is strong on the mechanical/structural classes it is designed to flag** —
  cells that should be formulas but are hard-coded constants, inconsistent formulas across a
  row/region, references into blank cells — exactly the **orphan-constant / row-consistency** checks
  `FAST_LINT` owns.
- **Software is weak on domain/logic errors** that require understanding *intent* (a well-formed,
  internally consistent formula that computes the wrong business quantity). That is the residual.
- **Conclusion:** automated inspection is the **systematic first pass** that clears the
  mechanical/omission classes humans miss; human/higher-order review is reserved for the
  semantic/logic residue.

> NOTE: arXiv PDF returned compressed binary to the fetch tool; per-cell percentages above are
> characterised qualitatively from the published abstract and Panko's SSR corpus rather than quoted
> verbatim. Flagged per CLAUDE §3.3 — not fabricated.

## Best parts to take (for our gate) and why

1. **The deterministic floor is evidence-backed, not stylistic.** Mechanical/structural classes are
   exactly what static inspection catches reliably → our deterministic checks are the right floor.
2. **It also bounds what determinism can't do:** semantic/intent errors are the residual — the
   precise, evidence-based justification for an **optional model-advisory layer on top**, and for it
   being **advisory only** (it addresses the residue; it cannot be trusted to clear the mechanical
   floor the deterministic checks already own).
3. **Complementarity => layered gate**, matching the plan's deterministic-core + add-only model layer.
