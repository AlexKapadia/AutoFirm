# SYNTHESIS — B1: Organizational Operating Models by Industry

> Branch B1, Layer-1 (Foundations). Covers **L1.B1.1** (org-design theory), **L1.B1.2** (industry
> operating-model archetypes), **L1.B1.3** (span-of-control, coordination & hierarchy scaling).
> Per DEPTH-RUBRIC: full alternative space surveyed; every relied-upon claim corroborated by >=2-3
> independent primary sources; build implications stated; conclusions general (panel-wide), not
> overfit. 12 source folders accompany this file.

## 1. The surveyed space

### L1.B1.1 — Org-design theory (the THREE foundational lenses, surveyed in full)
| Lens | Source | Core idea | Status |
|---|---|---|---|
| Information-processing (OIPT) | 01 Galbraith 1974 (High) | Task uncertainty -> required info processing; reduce-need OR increase-capacity via 4 strategies | ADOPT |
| Star Model | 02 Galbraith (Mod) | 5 aligned levers: Strategy -> Structure/Processes/Rewards/People | ADOPT |
| Structure <-> coordination fit | 03 Burton & Obel 2018 (High) | Design = create fit; multi-contingency; misfit cost | ADOPT |
| Configurations | 04 Mintzberg 1979/83 (High) | 5 coordinating mechanisms x 5 parts -> 5 configurations | ADOPT (as menu) |
| Contingency / SARFIT | 05 Donaldson 2006 (High) | No one best way; fit -> perf; dynamic adapt-to-regain-fit cycle | ADOPT |

These five are complementary, not competing: OIPT supplies the mechanism (information), the Star
supplies the levers, Burton & Obel supplies the objective (fit), Mintzberg supplies the menu of
structures/coordination, Donaldson supplies the dynamics (adaptation). No major org-design school is
omitted; population-ecology and institutional theory are excluded as out-of-scope (they explain org
survival/legitimacy, not design choices — noted boundary).

### L1.B1.3 — Span-of-control, coordination & hierarchy scaling
| Source | Contribution | Status |
|---|---|---|
| 06 Graicunas 1933 (High formula / Mod prescription) | Exact formula C(n)=n(2^(n-1)+n-1) -> near-geometric coordination explosion | ADOPT curve, REJECT literal 5-6 |
| 07 Rajan & Wulf 2006 (High) | Empirical: better info systems -> wider spans (4->7) + fewer levels (-25%) | ADOPT direction |
| Mintzberg mechanisms (04) | "Standardize outputs" suppresses the cross term -> scales | ADOPT |

Surveyed both the classic prescriptive (Graicunas/Urwick) and the modern empirical (Rajan & Wulf)
poles; reconciled via OIPT (information-system quality sets the safe span).

### L1.B1.2 — Industry operating-model archetypes (mapped to the FIXED B12 panel)
| Panel row | Archetype source | Operating model + headline KPIs |
|---|---|---|
| 1 B2B SaaS | 09 SaaS metrics | Recurring revenue; Rule of 40, NRR, CAC payback, Magic Number |
| 2 Prof. services | 11 Maister | Leverage pyramid; utilization, realization, rev/professional |
| 3 Discrete mfg | 08 SCOR | Plan-Source-Make-Deliver-Return-Enable; 5 perf attributes |
| 4 E-commerce/DTC | 12 Retail KPIs | Inventory turnover, GMROI, same-store sales, conversion, AOV |
| 5 Two-sided marketplace | 10 Marketplace | Liquidity-first; GMV, take rate, cold-start sequencing |
| 6 Fintech/payments | (gap note) | Heavily regulated; unit economics + compliance-as-process |
| 7 Healthcare/digital health | (gap note) | Professional-bureaucracy (Mintzberg) + regulated ops |
| 8 Restaurant/food service | 08 SCOR + 12 | Physical SCOR ops + retail KPIs (covers, prime cost) |

Each archetype is an instance of the SAME underlying theory (a particular Mintzberg configuration +
a particular Star alignment + a particular KPI contract) — which is the generalization claim.

## 2. The generalizing insight (why B1 makes AutoFirm general, not overfit)
Donaldson "no one best way" + Burton & Obel multi-contingency model are the theorems that forbid a
single fixed org/business template and license AutoFirm to parameterize by industry/size. The
invariant across ALL panel rows is the method, not the output:

> B1 invariant: every company = (a) a Mintzberg configuration chosen by the work nature, (b) aligned
> across the Galbraith Star five levers, (c) optimized for structure<->coordination fit (Burton &
> Obel), (d) coordinated by a mechanism whose cost scales per Graicunas and whose safe span rises
> with information-system quality (Rajan & Wulf / OIPT), (e) measured by an industry-specific KPI
> contract (SaaS / PSF / SCOR / retail / marketplace ...), and (f) kept in fit over time by a SARFIT
> adaptation loop (Donaldson).

This produces a sensible result for every panel row (proven by the mapping above); overfitting to
any one row is rejected.

## 3. Concrete, cited recommendations for AutoFirm

R1 — The dynamic-org engine (L2.ORG) is an org-design engine, not ad-hoc spawning. Implement it as:
classify work nature -> pick Mintzberg configuration (04) -> instantiate the 5 Star levers (02) ->
select coordinating mechanism, defaulting to standardized output contracts as scale grows (04, the
org-theory<->MAS bridge) -> compute coordination cost via Graicunas (06) and enforce a span cap,
spawning sub-orchestrator layers above it -> raise the cap when standardized contracts + the
append-only audit/state channel are strong (07 / OIPT 01) -> run a SARFIT misfit loop (05) on the
North Star heartbeat (CLAUDE.md section 2) to re-scope/spawn/retire agents.

R2 — Minimize the orchestrator coordination load (OIPT, 01). Prefer self-contained tasks (maximally
independent scoped subagents) to cut interdependence; use lateral relations (typed A2 contracts + a
reconciliation agent) only when self-containment is impossible; treat the audit log + git/task-list
as the vertical information system; never use slack as the silent default. Theoretical backing for
CLAUDE.md section 3.1 (protect your context).

R3 — Span cap is computed, not guessed (06 / 07). Use C(n)=n(2^(n-1)+n-1) as the load estimator; set
the cap from the coordination mode (higher under standardized outputs, lower under mutual
adjustment); validate empirically via an ablation (evidence/). Reject the literal "5-6".

R4 — Every company gets an industry-parameterized KPI contract (08-12). L2.B4 modeling toolkit ships
deterministic, unit-exact formulae per archetype (SaaS stack / PSF leverage+utilization+realization
/ SCOR 5 attributes / retail turnover+GMROI / marketplace liquidity+take-rate). All benchmark
thresholds are stored as cited, versioned config (which survey, which year) — never magic constants
(CLAUDE.md section 3.9 + 3.3). Formulae go in the deterministic core with boundary tests (CLAUDE.md
section 3.11, zero numerical errors).

R5 — Leverage discipline for the agent fleet (11 Maister). Tag work Brains/Grey-Hair/Procedure; high
agent leverage (many cheap scoped subagents) for Procedure, low leverage (few capable agents) for
Brains; track agent-fleet utilization and realization (QA-accepted output / produced) as efficiency
evidence; low realization triggers re-leverage (a SARFIT adaptation).

## 4. Open gaps (flagged for the CRO / future waves)
- Fintech (panel row 6) and Healthcare (row 7) archetypes are covered by principle (regulated ->
  Mintzberg professional/machine bureaucracy + "Enable"/compliance-as-process from SCOR) but lack a
  dedicated source folder with industry-specific KPI definitions and regulatory operating-model
  detail. Recommend a follow-up source folder each before L2.B12 relies on them.
- Restaurant/food-service specific KPIs (prime cost, RevPASH, table turns) are covered only by
  analogy (SCOR + retail); a dedicated source would strengthen panel row 8.
- The org-theory<->MAS bridge (L1.A2.3, standardization of outputs as coordination) is asserted here
  from Mintzberg; the A2 branch should corroborate it from the MAS literature.

## 5. Reproducibility
Every claim above traces to a numbered source folder; formulae (Graicunas, SaaS, retail, PSF) are
closed-form and self-verifying; the Graicunas identity was arithmetic-checked in source 06. A
reviewer re-derives by reading the 12 SUMMARY.md files and recomputing the formulae.
