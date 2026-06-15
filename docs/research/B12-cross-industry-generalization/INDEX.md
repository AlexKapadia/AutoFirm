# INDEX — B12 Cross-Industry Generalization

Branch B12 (Layer 1). Questions: **L1.B12.1** (playbook invariants — general vs industry-specific)
and **L1.B12.2** (NAICS/GICS as parameterization). Status: **in-review** (researched to rubric;
awaiting senior + independent QA before CRO marks "answered").

| # | Source folder | Source | Tier | Questions |
|---|---|---|---|---|
| 01 | `01-naics-2017-manual/` | NAICS US 2017 Manual (OMB/Census, tri-national) | High | L1.B12.2 |
| 02 | `02-naics-conceptual-framework/` | NAICS conceptual framework (Census + StatCan) | High | L1.B12.2 |
| 03 | `03-gics-methodology-2024/` | GICS Methodology Aug-2024 (MSCI / S&P) | High | L1.B12.2 |
| 04 | `04-apqc-pcf-cross-industry/` | APQC Process Classification Framework (PCF), cross-industry | Moderate↑ | L1.B12.1 |
| 05 | `05-cepc-configurable-reference-models/` | C-EPC: Rosemann & van der Aalst 2007 (IS 32(1)); Recker et al. 2005 (ACIS) | High / Moderate | L1.B12.1 |
| 06 | `06-fettke-loos-reference-model-survey/` | Fettke, Loos & Zwicker 2006 (BPM Workshops, LNCS 3812) | High | L1.B12.1 |
| 07 | `07-scor-supply-chain-reference/` | SCOR / SCOR DS (ASCM) | Moderate↑ | L1.B12.1 |

Synthesis: `SYNTHESIS.md` (surveyed space + cited recommendation for AutoFirm).

Each folder contains `SUMMARY.md` (faithful, exactly-cited summary + GRADE tier) and `BEST-PARTS.md`
(adopt/reject + concrete build implication). All files ≤ 300 lines.
