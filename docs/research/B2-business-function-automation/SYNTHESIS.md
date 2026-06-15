# SYNTHESIS — B2: Taxonomy of automatable business functions (incl. customer support)

Branch B2 answers three L1 questions. This file surveys the full alternative space, grades it,
and gives AutoFirm a concrete, cited recommendation. Per-source detail lives in `NN-slug/`.

---

## L1.B2.1 — Canonical value-chain / function taxonomy: ALTERNATIVE SPACE SURVEYED

| Taxonomy | Scope | Levels | Adopt/Reject for AutoFirm | Source |
|---|---|---|---|---|
| **Porter Value Chain** (5 primary + 4 support) | Any firm, *strategic* | 1 | **ADOPT as L1 spine** | 01 (High) |
| **Business Model Canvas** (9 blocks) | Any firm, *business logic* | 1 | **ADOPT as the parameterizing config** | 02 (High) |
| **APQC PCF** (12 categories → 5 levels, 100s of processes) | Any firm, *operational* | 5 | **ADOPT as the executable L2–L4 detail** | 03 (Mod-High) |
| **eTOM** (3 areas → 5 levels) | Telecom | 5 | **ADOPT as an industry OVERLAY only** | 04 (Mod) |
| **SCOR** (Plan/Source/Make/Deliver/Return → 4 levels) | Supply chain | 4 | **ADOPT as an industry OVERLAY only** | 04 (Mod) |

**Recommendation (cited).** A **three-layer stacked taxonomy**, not a single framework:
1. **Strategic spine = Porter's 9 generic activities** (01) — industry-agnostic, assigns agent
   divisions, allows-empty activities so digital firms aren't forced into a manufacturing flow.
2. **Business-logic config = the 9 BMC blocks** (02) — a typed `BusinessModelSpec` that
   *parameterizes* every downstream playbook (who/what/how-paid) per client.
3. **Operational detail = APQC PCF, version-pinned** (03) — the executable Category→Group→Process
   →Activity→Task tree that work is actually delegated and scored at; **eTOM/SCOR/industry-PCFs
   are pluggable overlays** selected by NAICS/GICS (04, ties L1.B12.2).
This stack is general by construction (every framework here is explicitly cross-firm) and avoids
single-industry overfit (DEPTH-RUBRIC §6). **Customer support** appears natively as Porter
*Service* → APQC *Manage Customer Service* (Cat. 5) → feeds the B9 playbook.

---

## L1.B2.2 — Business Model Canvas as a function map: RESOLVED
The 9 BMC blocks (02) are AutoFirm's **per-client parameterization layer**, complementary to (not
competing with) the activity taxonomy. Mapping to downstream playbooks: Revenue Streams→B5;
Customer Segments+Channels→B7; Customer Relationships→B9; Cost Structure→B5/B6; Key Activities→
the subset of Porter activities flagged "strategically key" so agent effort concentrates there.
Cross-block consistency is validated fail-closed (a VP change must propagate to CS/CH/RS).

---

## L1.B2.3 — Which functions automate, to what degree: ALTERNATIVE SPACE + EVIDENCE BAND

| Study | Unit | Method | Headline | Lesson for AutoFirm | Src/tier |
|---|---|---|---|---|---|
| **Autor-Levy-Murnane 2003** | tasks | routine×(cog/manual) 2×2 | computers substitute routine, complement non-routine; explains ~60% of 1970-98 college-demand shift | the *axes* + substitute/complement principle | 08 High |
| **Frey-Osborne 2017** | occupations | Gaussian-process classifier, 702 occs, 9 O*NET vars / 3 bottlenecks | **47%** US employment high-risk (>0.7) | the 3 bottleneck axes (perception/manip, creative, social) as a *hard-to-automate* rubric | 05 High |
| **Arntz/OECD 2016** | tasks (PIAAC) | task-content, 21 countries | only **9%** highly automatable | **automate TASKS, not JOBS**; report the 9–47% method band | 07 High |
| **McKinsey MGI 2017** | ~2,000 activities | 18 capabilities/5 groups; 7 activity types | ~**50%** of activities automatable; **<5%** of jobs fully; **~60%** of roles ≥30% automatable; predictable-physical 81 / data-processing 69 / data-collection 64 % | activity-level feasibility priors + the 3 design constants | 06 Mod-High |
| **Eloundou et al. 2023** | tasks | E0/E1/E2 rubric, α/β/ζ, human+GPT-4 | **80%** of workers ≥10% of tasks exposed; **19%** ≥50%; up to **~49%** with LLM tooling | the LLM-era scorer; E2 = "build software on the LLM" = AutoFirm's value-add | 09 High |

**Recommendation (cited): a LAYERED automatability scorer per APQC Task** — never per job (07):
1. **Deterministic first cut** — ALM 2×2 (08): routine→auto, non-routine→augment/HITL.
2. **Hard-to-automate gate** — Frey-Osborne 3 bottlenecks (05): high Social/Creative score → HITL.
3. **Feasibility prior** — McKinsey activity-type % (06): data-processing 69 / data-collection 64 /
   predictable-physical 81 / managing 9 / expertise & stakeholder <20.
4. **LLM-era override** — Eloundou E0/E1/E2 + α/β/ζ (09): raises cognitive/language scores the
   pre-LLM studies understate; E2 tasks emit a per-client "tooling-to-build" backlog.
5. **Business/compliance gate** — every "technically automatable" verdict passes a cost (B5) +
   legal (B10) + fail-closed (CLAUDE §5.6) filter before auto-execution. *Technical ≠ should.*

**Design constants AutoFirm adopts (for `evidence/`):** target *activities not jobs*; assume
**<5% full automation** (human-augmenting by default); plan to the **~60%-of-roles-have-≥30%**
envelope; report automation coverage as the **α/β/ζ band**, never a single vanity number.

---

## Generality (B12) & build implications
The whole stack is industry-parameterized: Porter+BMC+APQC are cross-industry; eTOM/SCOR/industry-
PCFs are overlays selected by industry code; the automatability scorer operates on task *properties*
(routine-ness, bottleneck axes, capability needs, LLM exposure), not industry labels — so it
generalizes across all 8 B12 panel rows. Concrete components this branch drives (for L2.B2):
`function_decomposition/{value_chain_activity_taxonomy, business_model_spec, process_taxonomy/,
industry_overlays/}` and `automatability/{routine_classifier, bottleneck_scoring,
feasibility_priors, llm_exposure}`.

## Open items for QA / downstream
- All absolute automation %s predate or are early-LLM; the *methods/axes* are durable, the
  *levels* must be re-derived against current agent capability (flagged in every relevant BEST-PARTS).
- APQC PCF verbatim content is IP-encumbered — use as reference mapping, pin the version (B10 note).
