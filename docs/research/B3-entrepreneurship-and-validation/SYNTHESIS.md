# SYNTHESIS — B3: Entrepreneurship & Opportunity Validation (L1.B3.1, L1.B3.2)

Branch B3 answers two Layer-1 foundation questions for AutoFirm's company-building doctrine:
- **L1.B3.1** — opportunity-discovery & validation theory (Lean Startup, Customer Development, JTBD):
  empirical support and critiques.
- **L1.B3.2** — market sizing & TAM/SAM/SOM methodology.

This synthesis surveys the FULL method space, judges each option (adopt/reject/defer), and lands a
concrete, cited recommendation for the L2.B3 opportunity-validation playbook.

---

## 1. The surveyed alternative space (L1.B3.1)

| Method | School / origin | What it gives | Evidence tier | Verdict |
|---|---|---|---|---|
| **Customer Development** (Blank, src 04) | originating process | DISCOVER->VALIDATE->CREATE->BUILD; search-vs-execution | Low (book), up-corroborated | **ADOPT** (lifecycle spine) |
| **Lean Startup / hypothesis-driven** (Eisenmann-Ries, src 03) | formalization | Build-Measure-Learn, MVP, pivot, validated learning, bias mitigation | Low-Mod (note) | **ADOPT** (test loop) |
| **Scientific approach (RCT-validated)** (Camuffo, src 01/02) | causal evidence | falsifiable hypotheses + disciplined tests improve decision quality | **High (RCT x2)** | **ADOPT** (the causal core) |
| **JTBD — Jobs as Progress** (Christensen, src 05) | demand-side theory | defines the JOB to solve; functional/social/emotional | Low-Mod (HBR) | **ADOPT** (discovery framing) |
| **JTBD — Jobs as Activity / ODI** (Ulwick, src 06) | measurable method | desired-outcome statements + opportunity-score formula | Low-Mod (HBR+corrob.) | **ADOPT** (prioritization math) |
| **Effectuation** (Frederiksen & Brem 2017, via src 08) | decision logic | experimentation over long-range planning under uncertainty | Moderate (peer SLR) | **ADOPT as rationale** for the iterate loop |
| **Failure-pattern analysis** (Eisenmann, src 07) | critique/risk taxonomy | six failure patterns; the "false start" critique | Moderate | **ADOPT** (risk gate) |
| **Discovery-Driven Planning** (McGrath-MacMillan) | plan-as-you-learn | assumption-driven planning under uncertainty | (noted, not deep-sourced) | **DEFER** to L2.B3 |
| **Pure stage-gate / write-the-plan-first** | traditional | upfront business plan, then execute | — | **REJECT** (contradicts the evidence: build-the-wrong-thing risk, src 04/07) |

**What is excluded (scope boundary):** detailed MVP *typologies* (concierge, Wizard-of-Oz,
smoke-test), effectuation-vs-causation theory depth, and Discovery-Driven Planning math are noted but
deferred to L2.B3 design; the org-transition (Blank step 4) belongs to B1/L2.ORG.

### The load-bearing empirical finding
The **only RCT-grade causal evidence** in the space is Camuffo et al. (sources 01/02): teaching
founders a **scientific / hypothesis-testing approach** makes them **terminate dead ideas sooner**
and **pivot more (but in a disciplined, nonlinear way — a few evidence-backed pivots, not thrashing)**,
with a **significant revenue effect (EUR 6,999.327 more, p=.030)** at scale (759 firms / 4 RCTs).
Everything else in the space (Lean Startup, Customer Development, JTBD) is widely adopted but, per
multiple SLRs (source 08; Frederiksen & Brem 2017; Ghezzi 2019), **thinly validated and
digital-skewed.** Therefore AutoFirm's effectiveness claim rests on the RCTs; the other frameworks
supply *structure*, not *proof*.

---

## 2. The surveyed alternative space (L1.B3.2 — market sizing)

| Method | Formula / basis | Verdict |
|---|---|---|
| **Bottom-up** | `Market Size = ACV x N_potential_customers` | **ADOPT (default, deterministic)** |
| **Top-down** | industry total x filters (geo/segment/adoption) | **REJECT as primary** (inflation risk); allow as cross-check |
| **Value-theory** | value-created x capturable-share | **DEFER** (use when no comparable market) |
| **TAM/SAM/SOM nesting** | SOM subset SAM subset TAM | **ADOPT** (typed contract w/ assumptions+sources) |

Bottom-up is multiply documented as the credible method investors trust; top-down is "chronically
inflated." AutoFirm computes both and **flags divergence** as a credibility risk (auditable, no magic
constants — SS3.9).

---

## 3. Concrete recommendation for L2.B3 (the playbook to build)

AutoFirm's opportunity-validation playbook is a **HYBRID deterministic engine** (CLAUDE SS3.5):

1. **DISCOVER (job-first).** Frame the opportunity as a `JobToBeDone` (Progress school, src 05):
   job statement + circumstance + functional/social/emotional dimensions + current alternatives.
   Discovery is a HARD GATE before any build (the "false start" fix, src 07 — fail-closed, SS5.6).
2. **QUANTIFY.** Decompose the job into desired-outcome statements and rank with the **exact ODI
   opportunity score** `Opportunity = Importance + max(Importance - Satisfaction, 0)` (src 06) —
   a pure, unit-tested, deterministic function (SS3.6).
3. **SIZE.** Compute `MarketSizing{tam, sam, som}` bottom-up (`ACV x N_customers`, src 10) with
   assumptions + public-data sources recorded; cross-check top-down; flag divergence.
4. **HYPOTHESIZE + TEST (the causal core).** Emit a `HypothesisLedger` of falsifiable business-model
   hypotheses, each with a pre-committed pass/fail threshold; run **Build-Measure-Learn** loops
   (src 03) — the *scientific approach* the RCTs validate (src 01/02).
5. **DECIDE (fail-closed verdicts).** Deterministic verdict in {CONTINUE, PIVOT, TERMINATE}; default
   to TERMINATE when hypotheses are disconfirmed (the RCT's key behavioral win). Cap pivots: after K
   evidence-backed pivots without convergence -> TERMINATE/re-scope (the nonlinear finding, src 02).
6. **RISK-CHECK.** Score the six Eisenmann failure patterns (src 07) as explicit risk flags
   (esp. False Promises: early-adopter SOM != mainstream SAM).

**Generality mandate (SS3.9, SS4.5):** because the literature is digital-skewed (src 08), the entire
playbook MUST be proven on the **fixed industry panel** (SaaS, services, manufacturing, e-commerce,
marketplace, fintech, healthcare, food service). Heavy-regulated rows (fintech, healthcare) get
stricter validation gates (boundary conditions, src 03). Overfitting to SaaS = instant FAIL.

**Determinism & explainability:** every score (opportunity, market size) is a pure function tested to
the unit; every verdict states which hypothesis fired and which threshold was crossed (SS3.11).

---

## 4. Data contracts this branch hands to L2.B3
- `JobToBeDone` (narrative progress + measurable desired outcomes; tags its JTBD interpretation, src 09)
- `OpportunityScore` (exact ODI formula; pure function)
- `MarketSizing{tam,sam,som,method,assumptions[],sources[]}` (bottom-up default + top-down cross-check)
- `HypothesisLedger` (falsifiable hypotheses + pre-committed thresholds)
- `ValidationVerdict ∈ {CONTINUE, PIVOT, TERMINATE}` (fail-closed; pivot-capped)
- `FailurePatternRiskCheck` (six-pattern risk flags)

## 5. Evidence/ targets (quantified, for the showcase)
- % of seeded non-viable ideas correctly TERMINATED (validates the RCT mechanism).
- Pivot discipline: bounded, moderate pivot count on the panel (no thrashing — src 02 nonlinearity).
- Opportunity-score determinism: identical inputs -> identical rank, exact to the decimal.
- Market-size determinism: identical inputs -> identical TAM/SAM/SOM to the unit; top-down/bottom-up
  divergence flagged.
- Citable payoff: disciplined validation -> significant performance effect (EUR 6,999.327, p=.030,
  src 02) — cited as motivation, never hard-coded.
