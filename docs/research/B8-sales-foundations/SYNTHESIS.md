# SYNTHESIS — B8 Sales Foundations (L1.B8.1: funnels, methodologies, B2B vs B2C motions)

> Owner: Research Analyst, B8. Feeds **L2.B8** (Automated sales playbook ← L1.B8.1, L1.B7.1
> marketing→sales handoff, L1.B12.*). All claims traced to the per-source folders in this dir.

## 1. The surveyed alternative space (full menu, not one convenient approach)

**(a) Stage / funnel models (how a sale is TRACKED):**
- AIDA & the hierarchy-of-effects family (think-feel-do) — source 01 (Iwamoto).
- The empirical critique: NO support for a fixed temporal stage hierarchy — source 02
  (Vakratsas & Ambler 1999, JM); replace single linear stage with a Cognition/Affect/Experience space.
- The modern non-linear B2B model: Gartner's **six looping "buying jobs"** — source 06.

**(b) Sales METHODOLOGIES (how a rep/agent BEHAVES):**
- **SPIN** (Situation/Problem/Implication/Need-payoff) — discovery-led, for large sales — source 03.
- **Challenger** (Teach/Tailor/Take-Control) — insight-led; beats relationship-building 40% vs 7%
  of star performers — source 04.
- **MEDDIC/MEDDPICC** — qualification checklist (8 fields) for complex deals — source 08.
- *(Also surveyed and noted in-folder: Solution Selling [Watts/Wang, 1970s], Sandler [1960s,
  consultative/pain-based], Miller-Heiman Strategic Selling [buying-influences/blue-sheet],
  Consultative Selling [trusted-advisor]. These are variations on the same two axes —
  discovery-led and qualification-led — and are subsumed by SPIN + MEDDPICC + Challenger for
  build purposes.)*
- The academic spine: **Adaptive Selling** (Weitz/Sujan/Sujan 1986, JM) — effectiveness = altering
  behaviour to the situation; the theory that says "don't pick ONE methodology" — source 09.

**(c) B2B vs B2C / GTM MOTIONS (the structural buyer + channel reality):**
- **B2B buying center / DMU** (Webster & Wind 1972; Robinson-Faris-Wind Buygrid) — multi-person,
  multi-phase, buy-class-modulated — source 05.
- **Omnichannel + rule-of-thirds** (McKinsey B2B Pulse) — ~10 channels; 1/3 in-person, 1/3 remote,
  1/3 self-serve, invariant across industry/size/value — source 07.
- **PLG ↔ PLS ↔ SLG motion spectrum** (Bush 2019, OpenView, McKinsey 2023) — no-touch ↔ hybrid ↔
  high-touch; PQL as the self-serve qualification signal — source 10.

## 2. The cross-cutting empirical conclusion
The strongest evidence (sources 02, 06, 07 — peer-reviewed + large industry surveys, mutually
corroborating) is that **the strict linear funnel does not describe how buyers actually decide.**
B2B buying is **non-linear, looping, multi-stakeholder (6–10 people), and largely rep-free
(~17% of buyer time with sales; 61–67% prefer self-serve for part of the journey).** The funnel
survives only as a **reporting/CRM convention**, not as a model of the buyer.

## 3. Concrete, cited recommendation for AutoFirm (the build implication)
AutoFirm's L2.B8 sales engine should be a **three-layer, adaptive, fail-closed system** — chosen
because adaptive selling (source 09, High-tier) is the most general and best-evidenced principle,
and every other source slots under it as a parameterized option:

**Layer A — MOTION selector (top).** A deterministic `SalesMotion ∈ {PLG, PLS, SLG}` chosen from
product type, ACV, buyer, regulation (sources 07, 10). Defaults across the B12 panel: B2B-SaaS→PLS,
manufacturing→SLG, DTC→PLG, fintech/healthcare→SLG-leaning hybrid. Always offer the rule-of-thirds
channel choice (source 07).

**Layer B — METHODOLOGY selector (middle).** A glass-box `MethodologySelector` implementing the
adaptive-selling "if situation X → strategy Y" contingency knowledge (source 09): within SLG/PLS,
(buy-class, deal value, DMU complexity) → run **SPIN discovery** (source 03) + **Challenger insight
brief** (source 04); for PLG, run **PQL scoring** (source 10) instead of human discovery.

**Layer C — STATE + QUALIFICATION model (data contract).** Each opportunity carries:
- a **BuyingCenter** (DMU roles: Initiator/User/Influencer/Buyer/Decider/Gatekeeper) — source 05;
- a **BuyingJobsState** (6 looping jobs, scored in parallel, NOT a linear stage) — source 06;
- a **C/A/E** signal vector (cognition/affect/experience) instead of a single funnel index — source 02;
- a **MEDDPICC** 8-field qualification record with evidence + confidence per field — source 08;
- plus a legacy **funnel stage** purely for CRM interop/reporting — source 01.

**Fail-closed gate (CLAUDE §5.6):** a deal cannot be auto-advanced/forecast "commit" unless the
critical MEDDPICC fields (Economic Buyer, Decision Process, Paper Process, Champion, Metrics) are
evidenced — missing → flag for human/agent review, never silently advance.

## 4. Generality argument (B12 panel — no overfitting)
Every component above is a **schema parameterized by context**, not a fixed example: the DMU roles,
the six jobs, the MEDDPICC fields, the C/A/E dimensions, and the motion spectrum are all
industry-invariant; only their *content* varies per industry. The McKinsey rule-of-thirds (source 07)
is explicitly reported invariant across industry/geography/size/deal-value — the single strongest
cited basis that ONE sales framework serves the entire "any company" panel. Adaptive selling
(source 09) supplies the theory: the right behaviour is a function of the situation — exactly the
parameterize-don't-overfit mandate.

## 5. Efficacy metrics for the evidence/ showcase (CLAUDE §3.10)
- Win-rate of well-qualified (MEDDPICC-complete) vs poorly-qualified deals on the golden set.
- Adaptation index (ADAPTS-derived, source 09): does the agent vary behaviour by situation vs run
  a canned script? Target: significant behavioural variance across motion/methodology.
- Motion-fit accuracy: does the selected motion match a panel-row ground truth across all 8 B12 rows?
- Forecast calibration: predicted vs actual close, by qualification completeness.

## 6. Source ledger (this directory)
01 AIDA origin (Iwamoto, CHARM) · 02 How Advertising Works (Vakratsas & Ambler 1999, JM, High) ·
03 SPIN (Rackham 1988) · 04 Challenger (Dixon & Adamson 2011) · 05 Org Buying Behavior
(Webster & Wind 1972, JM, High) · 06 Gartner Six Buying Jobs · 07 McKinsey B2B Pulse ·
08 MEDDIC/MEDDPICC · 09 Adaptive Selling (Weitz/Sujan/Sujan 1986, JM, High) · 10 PLG/PLS/SLG.

## 7. Coverage caveats / what was excluded (scope honesty)
- Excluded deep dives into individual legacy methodologies (Solution Selling, Sandler,
  Miller-Heiman, NEAT, GAP, Value Selling) as SEPARATE folders — surveyed and judged subsumed by
  SPIN+Challenger+MEDDPICC on the two axes (discovery-led, qualification-led); a dedicated folder
  can be added if L2.B8 needs finer granularity.
- Practitioner-tier sources (03,04,08,10) are cited for STRUCTURE/taxonomy, not claimed effect
  sizes; efficacy is to be proven on AutoFirm's own golden set, not asserted from vendor data.
- Compensation/territory/sales-ops mechanics and CRM tooling are deferred to L2.B8/B11 (operations).
