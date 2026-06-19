# 03 — *Revisiting the Panko-Halverson Taxonomy of Spreadsheet Errors*

- **Author / org:** R. Panko (Halverson lineage), University of Hawaii.
- **Year:** 2008 (EuSpRIG). arXiv:0809.3613.
- **Link:** https://arxiv.org/pdf/0809.3613
- **Tier:** High — the standard defect taxonomy for spreadsheets/financial models.

## Faithful structured summary — the taxonomy our gate must cover

**Top-level split:** **Quantitative errors** (produces a wrong number) vs **Qualitative errors**
(poor structure/practice that *raises the risk* of future quantitative error — unclear layout, no
documentation).

**Quantitative error classes** (what the gate must DETECT):
1. **Mechanical errors** — execution slips where the developer knows the correct approach but
   mis-executes: typos, transpositions, **pointing/reference errors** (wrong cell referenced).
2. **Logic errors** — the reasoning/formula is wrong:
   - **Pure logic errors** — wrong algorithm/formula chosen.
   - **Eureka (domain) logic errors** — developer believes it solved but misunderstood the
     requirement; the formula is well-formed but computes the wrong thing.
3. **Omission errors** — something required is **left out** (a line item, a statement, a period).
   Empirically the **hardest class for humans to detect** (01).

**Qualitative errors** map onto FAST/ICAEW *practice* rules (separation of inputs/calcs/outputs,
consistent formulas, no embedded constants) — preventive structure, checkable by lint.

## Best parts to take (for our gate) and why

1. **Use this taxonomy as the gate's defect coverage matrix.** Every check traces to a class:
   - Mechanical -> `NUMERIC_RECOMPUTE` + `FAST_LINT` (orphan constant) + `SPEC_ROUND_TRIP`.
   - Pure logic -> partly `ACCOUNTING_IDENTITY` (A=L+E) + `SPEC_ROUND_TRIP`; residue -> model layer.
   - **Eureka/domain logic -> the residual** deterministic checks cannot catch -> the documented,
     evidence-gated reason a model-advisory layer may earn its place (per 02, 07).
   - Omission -> `FAST_LINT` statement/period completeness.
2. **Mutation-testing design (CLAUDE §3.6):** inject one fault **per taxonomy class** and require the
   gate to KILL each — the principled basis for the plan's §D.2 mutant list.
3. **Quantitative (must-block) vs qualitative (lint/advisory)** maps onto `CheckSeverity`
   BLOCKING vs ADVISORY.
