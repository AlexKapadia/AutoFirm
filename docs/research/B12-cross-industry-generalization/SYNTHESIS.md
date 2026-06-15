# SYNTHESIS — B12 Cross-Industry Generalization (L1.B12.1 + L1.B12.2)

> Branch B12: what makes a business playbook GENERAL vs industry-specific (the invariants), and how
> NAICS/GICS parameterize playbooks; proven against the fixed industry panel.
> Single-writer dir; every claim cited to the per-source folders here.

## 1. The two L1 questions, answered

**L1.B12.1 — The invariants (general vs industry-specific).**
A playbook is "general" when it is expressed as an **invariant process spine + a parameterized
override layer**, and ALL industry-specific content lives ONLY in the override layer. This is not a
guess — it is the convergent finding of three independent, decades-proven reference-model traditions:
- **APQC PCF** (src 04): explicitly splits stable upper levels (Category → Process Group → Process,
  the cross-industry invariant) from variable lower levels (Activity → Task, which "often vary among
  industries and organizations"). Its **13 Categories** are the validated cross-industry spine.
- **C-EPC / Rosemann & van der Aalst 2007** (src 05, peer-reviewed *Information Systems* 32(1)):
  formalizes ONE configurable reference model → many individualized variants via marked
  **variation points** (functions/connectors set ON/OFF/OPT), with **configuration requirements**
  (lawfulness predicates) + **guidelines** (defaults), and the crucial **design-time (per class)
  vs run-time (per case)** decision split.
- **SCOR / ASCM** (src 07): an operations exemplar — ALL supply chains reduce to ~6 universal top
  processes (Plan/Source/Make/Deliver/Return/Enable) configured per instance, proving a TINY spine
  can cover every industry.
- **Fettke, Loos & Zwicker 2006** (src 06, peer-reviewed LNCS 3812): defines a reference model by
  two properties — **generic (universal/reusable)** + **recommendation (best-practice)** — and
  flags that generality rests on a **similarity assumption** that must be EMPIRICALLY validated, not
  assumed. This is the citation that turns "prove it on the panel" from a preference into a
  methodological requirement.

**L1.B12.2 — NAICS/GICS as parameterization.**
Use BOTH, on different axes, because they classify on different principles:
- **NAICS** (src 01/02, official tri-national standard): **production/supply-oriented** —
  "producing units that use similar production processes should be grouped together." 20 sectors;
  2→6 digit hierarchy (Sector/Subsector/Industry Group/NAICS Industry/National Industry); 5-digit
  level is internationally comparable, 6th is national. → Keys **operations/supply/delivery**
  playbooks (B11, B4.3) and supports longest-prefix fallback.
- **GICS** (src 03, MSCI/S&P standard): **demand/market-oriented** — companies classified by
  **principal business activity (revenue-primary)** with earnings + market perception; 11 sectors /
  25 industry groups / 74 industries / 163 sub-industries; 8-digit code; annual review. → Keys
  **market-/investor-facing** playbooks (fundraising B6, pricing posture B5).

## 2. Full alternative space surveyed (DEPTH-RUBRIC §4)

Industry-classification schemes considered, with ADOPT/REJECT/DEFER:
| Scheme | Principle | Decision |
|---|---|---|
| **NAICS** | production/supply | **ADOPT** — primary ops key; always present; intl at 5-digit |
| **GICS** | revenue/market | **ADOPT** (optional enrichment) — market/finance-facing key |
| **SIC** (legacy) | mixed, pre-1997 | **REJECT** — superseded by NAICS; US Census migrated off it |
| **ISIC** (UN) | production | **DEFER** — NAICS aligns to ISIC 2-digit; use as intl bridge if needed |
| **NACE** (EU) | production | **DEFER** — ISIC-derived; map from NAICS for EU companies later |
| **Business-model axes** (B2B/B2C, regulated?, physical/digital) | demand/operating | **ADOPT** — the panel's own columns; primary GTM key (NAICS is silent on these) |

Generalization-MECHANISM space considered:
| Mechanism | Decision | Why |
|---|---|---|
| One playbook per industry (N bespoke) | **REJECT** | unmaintainable; overfits; no shared invariant |
| Single rigid universal playbook (no variation) | **REJECT** | ignores real industry variance; fails panel |
| **Invariant spine + configurable variation points** | **ADOPT** | APQC+C-EPC+SCOR converge; testable; lawful |
| ML/learned playbook generation | **DEFER** | no evidence base yet; deterministic spine is the regulator-defensible core (CLAUDE.md §3.5) |

## 3. Concrete recommendation for AutoFirm (the build implication)

1. **`IndustryProfile` contract** = `{ naics_code(2-6, required), gics_code(optional),
   business_model_axes{b2b_b2c, regulated_tier, physical_digital} }`. One canonical assignment per
   axis (GICS single-classification discipline, src 03).
2. **`PlaybookSpine`** = APQC's 13 categories × process-groups × processes, with **stable element
   IDs** (src 04). Shared identically by ALL industries. Operations sub-spine adopts SCOR top
   processes (src 07). This is the **invariant** — any industry content leaking into the spine = FAIL.
3. **Variation points** (src 05): each spine step carries `{mode: ON|OFF|OPT, requires: Predicate[],
   guideline_default, metrics: KPI[]}`. `derive_playbook(profile)` is **design-time** configuration:
   longest-prefix NAICS/GICS resolution → select variants → ENFORCE every requirement predicate
   **fail-closed** (refuse unlawful variants, e.g. heavy-regulated with compliance OFF) → apply
   guideline defaults. Run-time routing is a separate later concern.
4. **Generality is PROVEN, not asserted (src 06):** the L2.B12 acceptance test runs `derive_playbook`
   across ALL 8 fixed-panel rows; each must yield a non-empty, lawful, sensible variant with
   industry-appropriate KPIs. Any panel row failing = not-general = FAIL (discharges the similarity
   assumption empirically). Property/fuzz tests over random profiles confirm no unlawful variant
   escapes (determinism + fail-closed evidence, CLAUDE.md §3.6).

## 4. Fixed-panel NAICS/GICS mapping (the golden set, indicative)
| # | Panel industry | NAICS (indicative) | GICS sector (indicative) | phys/dig |
|---|---|---|---|---|
| 1 | B2B SaaS | 5112 / 5415 | Information Technology | digital |
| 2 | Professional services | 5416 | Industrials / IT services | services |
| 3 | Discrete manufacturing | 31-33 | Industrials | physical |
| 4 | E-commerce / DTC | 4541 | Consumer Discretionary | phys+dig |
| 5 | Two-sided marketplace | 5415 / 454 | Comm. Services / Cons. Disc. | digital |
| 6 | Fintech / payments | 522 / 5223 | Financials | digital |
| 7 | Healthcare / digital health | 621 / 62 | Health Care | phys+dig |
| 8 | Restaurant / food service | 7225 | Consumer Discretionary | physical |

(Codes are indicative starting points for the resolver/test, not authoritative assignments.)

## 5. Source quality + corroboration
- L1.B12.1 invariant thesis: corroborated by **4 independent sources** (APQC, C-EPC, SCOR,
  Fettke/Loos) across 3 traditions — well above the ≥2 "important" bar; 2 are peer-reviewed (High).
- L1.B12.2 parameterization: NAICS corroborated by **2 independent High-tier govt agencies**
  (Census + StatCan); GICS by MSCI/S&P primary + secondaries. Meets the bar.
- All formulae/structure (NAICS digit levels, GICS counts, SCOR processes, C-EPC semantics) quoted
  with locators in the per-source SUMMARY files; counts and the production principle were
  spot-verified against the primary PDFs.

## 6. Open items / DEFER to L2
- ISIC/NACE international mapping (DEFER) — needed when AutoFirm operates non-North-American
  companies; NAICS 5-digit is the intl bridge for now.
- Exact KPI sets per industry (SCOR-style) — to be populated in L2.B11 override packs.
- Whether a learned layer earns a place over the deterministic spine — DEFER to L2.B12 evidence
  (branch-per-experiment), per CLAUDE.md §3.4–3.5.
