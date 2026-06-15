# SYNTHESIS — B7 Marketing Foundations (L1.B7.1)

**Question:** Marketing foundations — STP, 4Ps, channels, attribution; brand vs. performance.
**Scope:** Layer-1 literature only. Feeds L2.B7 (automated marketing playbook) and the
marketing-to-sales handoff into L2.B8. 11 sources, one folder each.

---

## 1. Full alternative space surveyed (ADOPT/REJECT/DEFER)

Marketing foundations split into STRATEGY (who/what/where you compete) and MEASUREMENT
(did it work).

### A. Segmentation / Targeting / Positioning
| Option | Decision | Source |
|---|---|---|
| Mass / product-differentiation | ADOPT for low-heterogeneity markets | Smith 1956 (01) |
| Market segmentation (tailored mixes) | ADOPT as default for heterogeneous markets | Smith (01); Kotler (03) |
| STP sequence (segment, target, position) | ADOPT as mandatory ordered pipeline | Kotler (03) |
| Positioning = single ownable attribute | ADOPT (message discipline) | Trout/Ries (04) |
| Availability/penetration growth school | ADOPT as the GROWTH engine | Sharp/Ehrenberg-Bass (09) |

**Tension resolved:** STP/positioning (narrow targeting, differentiation) vs. Ehrenberg-Bass
(broad reach, penetration). Resolution: STP/positioning decides the REACH BOUNDARY and MESSAGE
(which segments are addressable, critical for B2B/regulated/niche rows); availability/penetration
is the GROWTH MECHANISM within that boundary. Layered, not contradictory.

### B. The Mix
| Option | Decision | Source |
|---|---|---|
| 4Ps (Product/Price/Place/Promotion) | ADOPT as canonical mix schema | McCarthy 1960 (02) |
| 7Ps (+People/Process/Physical Evidence) | ADOPT conditionally for services/regulated | (02) |
| 4Cs (customer-centric reframe) | ADOPT as a QA/critique lens | (02) |
| 5Es / P-proliferations | REJECT as primary structure (overfit risk) | (02) |

### C. Channels
| Option | Decision | Source |
|---|---|---|
| Paid / Owned / Earned (POE) | ADOPT as channel taxonomy | Forrester 2009 (11) |
| POGLE / Shared extensions | DEFER (POE core sufficient now) | (11) |
| IMC integration principle | ADOPT as a coherence design rule | Schultz 1993 (11) |

### D. Measurement / Attribution (most contested)
| Option | Decision | Source |
|---|---|---|
| Heuristic (last/first/linear/time-decay/U) | REJECT as decision basis; KEEP as baselines | (05),(06) |
| Markov removal-effect (sequence-aware) | ADOPT as default MTA | Anderl 2016 (05) |
| Shapley value (set-based) | ADOPT as corroborating cross-check | Shapley/Dalessandro (06) |
| MMM (adstock+saturation econometric) | ADOPT as budget-allocation layer | Hanssens/Broadbent/Jin (08) |
| Incrementality / geo-experiments | ADOPT as gold-standard causal gate | Vaver 2011; Gordon 2019 (07) |

**Hard line (fail-closed):** attribution is correlational, not causal. Gordon et al. (2019,
Marketing Science) show observational methods can be badly biased vs. RCT ground truth. Material
budget reallocations require incrementality evidence, triangulated with MMM.

### E. Brand vs. Performance
| Option | Decision | Source |
|---|---|---|
| Brand-build (slow-decay) + Activation (fast-decay) dual model | ADOPT | Binet-Field 2013 (10) |
| ~60:40 brand:activation split | ADOPT as industry-parameterized PRIOR, never a constant | (10) |
| Short-term-ROI-only optimization | REJECT (short-termism failure) | (10) |

---

## 2. Recommendation for AutoFirm (build implication)

The L2.B7 marketing playbook is a gated DAG separating STRATEGY, EXECUTION, and a triangulated
MEASUREMENT stack:

    STRATEGY                      EXECUTION                  MEASUREMENT (triangulated)
    1 heterogeneity check (01)    5 4Ps/7Ps mix (02)         A attribution Markov+Shapley (05,06)
      segment vs differentiate    6 POE channel select (11)    correlational, daily
    2 segmentation (01,03)        7 brand/activation split   B MMM adstock+saturation (08)
      + 5 effectiveness criteria    60:40 prior, industry-     budget-level, privacy-robust
    3 targeting score (03)          adjusted (10)            C incrementality geo-RCT (07)
    4 positioning 1 attribute                                  causal, decision-grade GATE
      vs competitors (04)
    GROWTH ENGINE (cross-cutting): mental + physical availability / penetration (09)

**Typed contracts** (clean cross-branch boundaries, no duplication):
- Segment { id, defining_vars, size, distinct_needs } gated by Kotler 5 criteria.
- PositioningStatement { segment, category_frame, single_attribute, competitors, point_of_difference }.
- MarketingMix (4P/7P): Price links to L1.B5.1; Place links to L1.B11.1 (reuse, do not redefine).
- Channel { id, poe_type, control, trust, cost_model, latency }.
- BudgetPlan { brand_pool, activation_pool, split_rationale }, split a function of industry/stage.
- AttributionResult { method, per_channel_credit } for Markov and Shapley + MMMResult + LiftTest.

**Fail-closed governance:** budget shifts above a spend threshold are BLOCKED unless backed by
incrementality/MMM evidence, not attribution alone (Gordon 2019). Decisions are explainable
(CLAUDE.md 3.11) and deterministic-where-exact (removal-effect, Shapley, adstock, Hill formulae
unit-tested to zero numerical error, CLAUDE.md 3.6).

---

## 3. Generality across the fixed industry panel (anti-overfit, CLAUDE.md 3.9)

| Panel row | STP emphasis | Mix | Brand:Activation prior | Measurement |
|---|---|---|---|---|
| 1 B2B SaaS | narrow target, strong positioning | 7P | activation-heavier (~50:50) | MTA + incrementality |
| 2 Prof. services | tight niche, expertise positioning | 7P | brand/reputation-heavier | MMM + earned |
| 3 Discrete mfg | account targeting | 4P/7P | activation-heavy, long cycle | MMM, geo-lift |
| 4 E-comm/DTC | behavioral segments | 4P | ~50:50, scale to brand | full MTA + geo-lift |
| 5 Marketplace | two-sided segments | 7P | balanced, both sides | incrementality per side |
| 6 Fintech | regulated targeting | 7P | trust/brand-heavy + compliance | MMM + RCT (privacy-safe) |
| 7 Healthcare | regulated, narrow | 7P | trust/brand-heavy | privacy-robust MMM/geo |
| 8 Restaurant | geo/local segments | 7P | local brand + activation | geo-lift natural fit |

The split, the mix (4P vs 7P), and dominant measurement method are parameterized, not fixed,
proving generalization. A hard-coded 60:40 or single attribution method would FAIL the gate.

---

## 4. Evidence-showcase hooks (CLAUDE.md 3.10)
- Attribution-method comparison: last-click vs Markov vs Shapley credit on synthetic ground-truth.
- Adstock/saturation response curves per channel (proves diminishing returns).
- Brand-vs-activation decay curves (long-slow vs short-fast) by industry.
- Determinism + zero-numerical-error tests on the four core formulae.

---

## 5. Source-count / rubric compliance
- Attribution (correctness-critical): Markov (05) + Shapley/Dalessandro (06) + Gordon-2019 (07) +
  MMM (08) = at least 3 independent primary/peer-reviewed. PASS.
- Brand:activation split: Binet-Field (10) + Ehrenberg-Bass reach evidence (09) = 2 independent.
  PASS (treated as a PRIOR not a constant, generality preserved).
- STP/4Ps/channels: primary origins (Smith 01, McCarthy/Borden 02, Kotler 03, Trout/Ries 04,
  Forrester 11) each corroborated by at least 1 independent source. PASS.
- High-tier anchors: Anderl 2016 (IJRM), Gordon 2019 (Marketing Science), Ehrenberg 1990
  (J. Marketing), Brodersen 2015 (Ann. Applied Stats), Shapley 1953.

**Open items for QA:** (a) spot-fetch-verify Dalessandro 2012 DOI and Vaver-Koehler 2011 URL;
(b) quantify the IMC multiplier per-client rather than asserting it; (c) confirm exact page for
Binet-Field 60:40 in the 2013 IPA monograph (figure varies by category; captured as a prior).
