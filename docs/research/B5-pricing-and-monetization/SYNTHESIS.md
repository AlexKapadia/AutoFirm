# SYNTHESIS — B5 Pricing & Monetization (L1.B5.1)

> Surveyed alternative space + cited, build-relevant recommendation for AutoFirm's pricing engine
> (feeds L2.B5). Every claim traces to a source folder (NN-slug) in this directory.

## 1. The full alternative space surveyed (with ADOPT/REJECT/DEFER)

**A. Pricing ORIENTATION (the strategy root)** -- sources 01, 12, 14 (peer-reviewed anchor)
- **Cost-plus** = cost + margin. ADOPT as floor only; REJECT as target (least profitable; cost
  does not determine WTP -- 01, corroborated 12).
- **Competition-based** = price relative to rivals. ADOPT as an anchor/sanity check; never the
  sole basis (commoditizes, ignores value).
- **Value-based** = price to economic/perceived value. ADOPT as the default target (01, 02,
  evidence 12).

**B. Value QUANTIFICATION** -- sources 02, 13 (primary origin), 14 (peer-reviewed)
- EVC = Reference Value + Differentiation Value - Switching/Implementation Costs. ADOPT as the
  canonical WTP-ceiling calculator (deterministic core). Primary-anchored to Forbis & Mehta (1981,
  the EVC origin) + Monroe + Hinterhuber (2004) -- three independent sources for the formula.
- **Hinterhuber six-step method (14):** objectives -> analyze elements -> economic-value analysis ->
  manage/communicate value -> range of profitable prices -> implement. ADOPT as the peer-reviewed
  ordering backbone of the pricing pipeline; output a price **band** [floor, EVC], not a false point.

**C. SEGMENTATION / DISCRIMINATION** -- source 03 (High)
- 1st-degree (personalized): ADOPT as unattainable ceiling/benchmark, and for B2B negotiated.
- 2nd-degree (versioning/tiers/usage menus, two-part tariff): ADOPT -- backbone of tiered/hybrid SaaS.
- 3rd-degree (segment-based): ADOPT with a hard fence + legal gate; REJECT impermissible bases.

**D. WTP MEASUREMENT** -- sources 05, 06, 07, 15
- Van Westendorp PSM: ADOPT for range-finding (PMC/PME/IPP/OPP).
- Gabor-Granger / conjoint (MNL): ADOPT for revenue-optimal point + elasticity within the range.
- Price-elasticity + Lerner inverse-elasticity rule (P-MC)/P = 1/|e|: ADOPT as the
  elasticity-to-price optimizer; mean elasticity -2.62 (n=1,851) as a prior only (07).
- **Incentive-compatible elicitation (BDM/ICBC) + hypothetical-bias control (15, High, JMR 2011):**
  stated-preference methods (open-ended, plain conjoint) **overstate** WTP; only incentive-aligned
  methods (BDM, ICBC) passed a REAL-purchase benchmark. ADOPT: tag stated-WTP inputs, bias-discount
  or bound them by EVC, and prefer incentive-aligned/live tests where a real purchase can close the loop.

**E. DYNAMIC / REVENUE MANAGEMENT** -- source 04 (High)
- Forecast -> optimize -> price triad; Littlewood/protection levels for capacity-constrained firms.
  ADOPT, gated by an industry-suitability classifier (only where RM theory applies).

**F. BEHAVIORAL / PSYCHOLOGICAL** -- sources 08, 09
- Charm/9-ending: ADOPT as an optional, B2C-only, validation-flagged presentation layer
  (context-dependent; PLOS ONE 2022 null recorded).
- Mental accounting / prospect theory (reference price, loss aversion lambda approx 2,
  transaction utility): ADOPT for the price-change/framing/bundling layer (truthful anchors only).

**G. MONETIZATION MODEL (digital)** -- source 11
- {flat, tiered/GBB, per-seat, usage-based, feature-based, hybrid (=two-part tariff), outcome-based}
  + freemium as an acquisition flag. ADOPT the menu; choose the value metric explicitly per client.

**H. ALGORITHMIC-PRICING RISK (binding safety constraint)** -- source 10 (High, AER 2020)
- Learned/competitor-reactive RL pricing converges on supracompetitive collusion without
  communication. REJECT autonomous reactive-learning pricing by default; impose a fail-closed
  antitrust guardrail + audit + HITL on any ML pricing layer.

**Explicitly EXCLUDED (scope boundary):** auction/mechanism-design pricing internals
(Mussa-Rosen/Maskin-Riley optimal nonlinear tariffs), network/choice-based RM, hierarchical-Bayes
conjoint estimation, full ICBC estimation internals (the *method-selection rule* IS covered, 15) ->
deferred to L2.B5-advanced or B11/B14.

## 2. Recommended architecture for AutoFirm's pricing engine (L2.B5 preview)

A deterministic, explainable core with optional, gated layers (CLAUDE sec 3.5):

```
select orientation (01,12)  ->  value model: EVC ceiling (02)  ->  segmentation/fences (03)
        |                                                                   |
        v                                                                   v
  monetization model + value metric (11)                          WTP layer: PSM range (05)
        |                                                          -> Gabor-Granger/conjoint
        v                                                             optimal + elasticity (06)
  PRICE-LEVEL ENGINE  <-------- Lerner / revenue-max optimizer (07) <------- (bounded by EVC & PSM)
        |
        +-- price-change/framing/bundling layer (reference-aware, 09)         [optional]
        +-- presentation/charm layer (B2C-only, validation-flagged, 08)       [optional]
        +-- dynamic pricing (04)  ONLY IF industry-suitable AND clears
            anti-collusion + legal + HITL guardrail (10, B10, A7)             [gated]
        |
        v
  OUTPUT: {strategy, segments+fences, model+value_metric, price/structure,
           value_communication artifact, profit-leverage business case (12),
           per-rule explanation (CLAUDE sec 3.11)}
```

**Invariants / fail-closed gates (CLAUDE sec 5.6):**
1. A price level is never emitted without a value model (cascade order, 01).
2. Proposed price <= EVC ceiling (02) and within [PMC, PME] (05) unless a justified exception.
3. Every tier/segment scheme passes a fence/arbitrage + incentive-compatibility check (03, 11).
4. Any discrimination basis clears the B10 legal gate; impermissible bases refused (03, 08, 09).
5. Any learned/reactive pricing clears anti-collusion + legal + HITL or is refused (10).
6. All deterministic arithmetic (EVC, Lerner, PSM points, profit leverage) is exact, zero-error,
   mutation-tested ~100% (CLAUDE sec 3.6/3.11).
7. Stated-preference WTP (open-ended/plain conjoint) is never used as a raw price target -- it is
   bias-discounted or bounded by EVC; incentive-aligned methods (BDM/ICBC/live test) preferred (15).

## 3. Generality across the B12 industry panel (no overfitting, CLAUDE sec 3.9/4.5)

| Panel row | Likely model | Dynamic pricing? | Notes |
|---|---|---|---|
| B2B SaaS | per-seat or hybrid (two-part tariff) | usually NO | value-based; tiers via 2nd-degree |
| Prof. services | value-based / outcome | NO | EVC per engagement |
| Discrete mfg | cost-plus floor + value diff | capacity-RM where constrained | Littlewood for finite capacity |
| E-commerce / DTC | competition + charm (B2C) | YES (retail markdown) | presentation layer applies |
| Marketplace | take-rate / commission | YES (two-sided) | two-sided pricing, watch collusion |
| Fintech / payments | usage/interchange + tiers | partial | heavy legal gate (B10) |
| Healthcare | value-based + regulated tariffs | NO | regulated; legal gate dominant |
| Restaurant / food | cost-plus floor + RM on capacity | YES (yield on seats/times) | Littlewood; charm on menu (B2C) |

The engine is parameterized (orientation, model, value metric, elasticity prior, dynamic-pricing
suitability, legal constraints) per row -- proven against ALL rows, not fitted to one.

## 4. Source-count / rigor check (DEPTH-RUBRIC sec 1)
- Safety-critical claims (segmentation/fence correctness 03; algorithmic-collusion risk 10; EVC &
  Lerner formulae): EVC now backed by **3 independent sources** -- Forbis & Mehta (1981 primary
  origin, 13), Monroe (13), and Hinterhuber (2004 peer-reviewed, 14) -- alongside the worked example
  (02); Lerner via 06/07. Segmentation 03 + collusion 10 each High-tier peer-reviewed.
- Orientation (value-based default) now has a **peer-reviewed anchor** (Hinterhuber 2004, IMM, 14),
  not just practitioner sources (01, 12).
- Important claims (WTP methods 05/06; elasticity magnitude 07; monetization taxonomy 11): >= 2
  independent, with peer-reviewed anchors. WTP-trustworthiness now anchored by Miller et al. (2011
  JMR, 15) + BDM (1964).
- Contradicting evidence retained, not hidden (08 PLOS ONE null; 12 magnitude caveat; 15 shows
  stated-WTP overstatement / hypothetical bias).
- Full alternative space surveyed (A-H, incl. incentive-compatible WTP elicitation via 15) with
  explicit ADOPT/REJECT/DEFER and exclusions stated.

## 5. Reproducibility
Every formula (EVC, Lerner (P-MC)/P=1/|e|, MNL choice prob, PSM intersections, profit leverage) is
reproducible from the cited primaries (sources 02,03,04,05,06,07,09,12,13,14). QA can re-fetch the
AER abstract (10), the JMR -2.62 figure (07), the ESOMAR PSM definition (05), the *Business Horizons*
24(3):32-42 EVC origin (13, Forbis & Mehta 1981), the IMM 33(8):765-778 six-step method (14,
Hinterhuber 2004), and the JMR 48(1):172-184 WTP-method comparison (15, Miller et al. 2011) to verify.
