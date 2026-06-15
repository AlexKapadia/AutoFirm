# QA-REVIEW-001 — Peer-Review/QA Audit of the Research-Program Blueprint

> Reviewer: Peer-Review / QA Lead (independent gate, RESEARCH-ORG.md §3.5). Scope: the four
> `_program/` spec files audited against CLAUDE.md §2/§3.3/§3.6/§5.5/§5.7. This is a review of the
> **blueprint**, not of any answered question. Verdict at the bottom; veto power exercised via the
> required-fix list.

---

## Verdict (summary)

**AMBER — Layer 1 MAY PROCEED, with the Wave-1 fixes below folded in.**

The blueprint is unusually strong: independent QA with real FAIL power, GRADE-adapted source
grading, exact-citation rules with anti-fabrication FAIL conditions, roles-as-data with span caps
and audit events, and a two-half ontology that genuinely spans platform + business. It is not RED —
no structural flaw forces a rewrite. It is not GREEN — there are **concrete coverage holes and two
governance gaps** that would let shallow or conflicting work through if not closed. They are small,
local edits to the existing files, so they belong in Wave 1, not a re-architecture.

---

## Criterion 1 — Coverage of the QUESTION-ONTOLOGY — **AMBER**

Both halves are present and the cross-half dependency edges (L1.B1.1 → L2.A1/L2.ORG; A6/A7 → both
halves) are correct and load-bearing. Checking the explicitly-required topics:

- Customer support — **PRESENT** (B9, L1.B9.1, L2.B5..B11 names "customer support"). Good.
- Real-data financial/customer/operational modeling — **PRESENT** (B4 / L1.B4.1-3, L2.B4). Good.
- Pricing — PRESENT (B5). Fundraising — PRESENT (B6). Marketing — PRESENT (B7). Sales — PRESENT
  (B8). Legal/compliance — PRESENT (B10). Operations — PRESENT (B11). Good.
- Dependencies — mostly correct. The L2.B5..B11 collapse into one line is acceptable as shorthand
  but **hides per-function dependency edges** (see fix C1.3).

**HOLES (these are the AMBER drivers):**

- **C1.1 — Design & product capability for client companies is MISSING.** The prompt calls this out
  explicitly: AutoFirm is headless but must *build great products/UIs for its clients*. CLAUDE.md §2
  (CDO/Head of Design) and §3.14 / §4.9 mandate an institution-grade, non-vibe-coded UI capability
  with a live Playwright DoD. **Nothing in the ontology researches how AutoFirm builds client-facing
  product/UI/UX, design systems, or the live-E2E DoD.** This is a first-class capability gap, not a
  detail. Required: a new branch (proposed **B13 — Product & design capability for client builds**)
  with L1 questions (design-system/token theory, accessibility WCAG 2.2 AA, Core Web Vitals budgets,
  design-research/teardown method, UX heuristics) and an L2.B13 (the AutoFirm design-build +
  live-E2E playbook) feeding L3.BUSINESS. Add the dependency edge L1.B13 → L2.B13 → L3.BUSINESS.

- **C1.2 — Software-engineering / build-quality capability for client code is MISSING.** Branch A
  covers building *the platform itself*, and B covers *operating* companies, but there is no branch
  on how AutoFirm **engineers the actual software products it ships for clients** (testing-with-teeth
  applied to client code, CI/CD, code-org per §5.7, secure-SDLC for delivered software). This is
  distinct from A9 (platform eval) and B11 (ops). Required: extend B (proposed **B14 — Software
  delivery & engineering quality for client products**) or fold into B11 explicitly. Without it, the
  "build" half of "build, fund, market…" has no research backing.

- **C1.3 — Per-function L2 dependencies are under-specified.** `L2.B5..B11` as one node loses the
  real edges (e.g. pricing L2.B5 depends on L1.B4.2 customer/LTV *and* L1.B5.1; sales L2.B8 depends
  on marketing L1.B7.1). The dependency graph must enumerate each so QA can enforce the §6 "dependency
  not satisfied" FAIL. Required: expand the graph to list B5–B11 individually.

- **C1.4 — Data acquisition / "real public data" sourcing is under-covered.** CLAUDE.md §3.12 makes
  real-public-data validation a hard final gate, and B4 needs real financials/registries. There is no
  L1 question on **where/how AutoFirm legally obtains real public data** (filings, registries, public
  APIs, ToS/scraping legality, PII-exclusion guarantees). Required: add L1.B4.4 (public-data sourcing
  & the synthetic-only-for-sensitive boundary) feeding L2.B4 — this also operationalizes §3.12.

- **C1.5 — Cost / unit-economics of running the agent platform itself is missing.** Token/compute cost
  governance is a real correctness/viability constraint for an autonomous agent company. Minor but
  worth an L1 question under A or B6. Mark as nice-to-have for Wave 1, mandatory before L2.

---

## Criterion 2 — Depth bar (DEPTH-RUBRIC) — **GREEN (with two tightenings)**

This is the strongest file. It genuinely disqualifies vibe-coded work:

- Source minimums per *claim* (not per question), criticality-tiered (≥3/≥2/≥1), with an explicit
  **independence rule** (shared-underlying-study counts as one) and an **automatic FAIL on a single
  source for a critical claim**. This is graduate-level.
- GRADE-adapted tiers with mandatory written up/down-rate reasoning; Very-low (blog/marketing) can
  **never** be a sole basis. Correct.
- Exact-citation §3 is excellent: full attribution every time, formulae in source notation with
  locators, exact numbers+units+table/figure, quote-when-in-doubt, **anti-hallucination + QA
  spot-fetch** of a sample. Directly implements CLAUDE.md §3.3.
- §4 full-alternative-space survey with ADOPT/REJECT/DEFER + rationale, and "name what was excluded"
  — kills single-approach tunnel vision (CLAUDE.md §3.4-3.5).
- §6 instant-FAIL list and §7 PASS checklist are concrete and auditable.

**Tightenings (do not block Layer 1, fold into Wave 1):**

- **C2.1 — "Independent sources" needs an operational test.** The independence rule is stated but a
  reviewer needs a procedure (distinct first-author AND distinct funding/org AND not citing the same
  primary). Add one sentence so two arms of the same lab don't get double-counted.
- **C2.2 — No inter-rater / sampling rule for QA spot-fetch.** §3.5/§3 say QA spot-fetches "a sample"
  — undefined sample size. For a rubric claiming to beat the "<20% verify" finding, specify a minimum
  (e.g. ≥20% of sources, and 100% of safety/correctness-critical formulae). Otherwise "sample" is a
  loophole.

---

## Criterion 3 — Org soundness (RESEARCH-ORG) — **AMBER**

Enforced well: independent QA reporting to CRO with PASS/FAIL-AND-RETURN veto (§3.5); generator ≠
evaluator; append-only audit events on every spawn/retire/re-scope (§5); fail-closed on invariant
violation (orphan/cycle/span>7/dup-mandate/missing-audit-field refused, not fixed); roles-as-data
typed records; span cap ≤7 with Sub-Lead insertion; data-driven team scaling (§4 C=Depth×Breadth×
Criticality) with a mandatory second researcher on safety-critical questions; Org-Mgmt de-dup +
stall + load + invariant checks. This satisfies CLAUDE.md §2/§3.13/§5.6 substantially.

**GAPS (AMBER drivers):**

- **C3.1 — "NEVER two agents on the same artifact" is NOT explicitly guaranteed.** Org-Mgmt detects
  "two teams researching the same source/question" *after the fact* and merges. The prompt requires a
  hard, **pre-write, fail-closed lock**: an artifact (`docs/research/<branch>/<source>/`) may have
  exactly one assigned author at a time. Required: add an explicit **single-writer invariant /
  assignment lock** to §5 SPAWN/RE-SCOPE preconditions and to the Org-Mgmt invariant set — a SPAWN/
  assignment that targets an already-owned artifact is **refused**, not reconciled later. This is the
  single most important governance fix.

- **C3.2 — "Every agent role must study CLAUDE.md" is NOT stated.** The prompt requires it explicitly;
  the org file references CLAUDE.md sections but never makes "read and conform to CLAUDE.md" part of
  each role's mandate/onboarding contract. Required: add to §3 (or §1 principle 1) that **every role
  record carries a mandatory `must_study: [CLAUDE.md, DEPTH-RUBRIC.md, relevant ontology branch]`
  field**, checked at SPAWN (fail-closed: no role activates without it).

- **C3.3 — QA independence has a latent conflict at scale.** §3.5 says the reviewer must not be the
  author, but with ≥1 QA per ~6 in-flight questions, the file doesn't forbid a QA reviewer from also
  having authored *a different* question that the one under review *depends on*. Minor; add a
  no-self-dependency-review clause.

- **C3.4 — No defined escalation/SLA for a stalled FAIL loop.** §5.1 triggers cover backlog and
  FAIL-rate, but a single question that FAILs repeatedly (oscillation) has no circuit-breaker.
  Required: cap rework loops (e.g. after N FAILs, CRO arbitration is mandatory) so the iterate-to-
  perfection loop can't spin forever. Ties to RESEARCH-PROGRAM §4.

---

## Criterion 4 — Gaps / contradictions / overfit risk + Wave-1 soundness — **AMBER**

**Contradictions / inconsistencies found:**

- **C4.1 — Seed-branch claim vs. reality (minor).** RESEARCH-PROGRAM §6 lists four seed branches as
  "present": `agent-communication-and-flow/`, `claude-code-substrate/`, `evaluation-and-evidence/`,
  `integration-and-data-layer/`. On disk only `claude-code-substrate/` and
  `integration-and-data-layer/` actually contain source folders; the other two have no artifacts yet.
  Not fatal, but the spec asserts state that isn't true — fix the wording to "branches scaffolded /
  partially seeded" so the program doc isn't itself an unverified claim (the program must hold itself
  to its own faithfulness bar).

- **C4.2 — CLAUDE.md placeholders still un-substituted.** `<PROJECT_NAME>`, `<LINE_COVERAGE>`,
  `<BRANCH_COVERAGE>`, `<TEST_COMMAND>`, `<THREAT_MODEL_PATH>` are still tokens. The DEPTH-RUBRIC and
  ORG reference coverage/mutation gates that have **no numeric value**. This isn't the research org's
  file, but Layer 2 (which builds code) will hit undefined gates. Flag to CRO: resolve placeholders
  before any L2 build question runs. Does not block L1 literature work.

**Overfit risks (the §3.9 bar):**

- **C4.3 — Business half risks example-fitting.** DEPTH-RUBRIC §5 requires industry-parameterization
  and forbids fitting to one company — good. But the ontology gives no **enumerated industry test
  set** the generalization claim (L1.B12, L2.B12) is checked against. Without a fixed, diverse
  industry panel (e.g. SaaS, services, manufacturing, marketplace, healthcare, fintech) declared up
  front, "general" can be asserted without proof. Required (Wave 1, cheap): the Program Architect
  declares the industry panel as a golden set for B12, mirroring CLAUDE.md §4.5.

**Wave-1 plan / sequencing:**

- The layer gate (no L2 on un-PASSED L1; no L3 on un-PASSED L2) is sound and matches the dependency
  graph. Layer 1 is pure literature with no build decisions — correctly the right place to start.
- **C4.4 — Wave 1 should NOT silently inherit the coverage holes.** Layer 1 may proceed, but Wave 1's
  written plan must (a) add branches B13 (design/product) and B14 (software delivery) to the ontology
  *before* researchers are assigned, so Scouts hunt the full space; (b) include L1.B4.4 (public-data
  sourcing); (c) record the single-writer lock and must-study-CLAUDE.md fields in the role schema used
  to spawn the first teams. These are blueprint edits, achievable in hours, hence AMBER not RED.

---

## Prioritized required fixes (fold into Wave 1)

| # | Fix | File | Severity |
|---|---|---|---|
| 1 | Add **single-writer artifact lock** to SPAWN/RE-SCOPE preconditions + Org-Mgmt invariants (fail-closed; refuse, don't reconcile-later) | RESEARCH-ORG §5, §3.6 | **BLOCKER** |
| 2 | Add **B13 Product & Design capability** (L1 + L2.B13) for client builds; wire to L3.BUSINESS | QUESTION-ONTOLOGY | **BLOCKER** |
| 3 | Add **must_study: [CLAUDE.md, DEPTH-RUBRIC, branch]** field to every role record, checked at SPAWN | RESEARCH-ORG §1/§3 | **BLOCKER** |
| 4 | Add **B14 Software-delivery/engineering-quality** for client products (or explicit B11 extension) | QUESTION-ONTOLOGY | High |
| 5 | Add **L1.B4.4 public-data sourcing + PII-exclusion boundary** feeding L2.B4 (operationalizes §3.12) | QUESTION-ONTOLOGY | High |
| 6 | **Expand L2.B5..B11 into individual dependency edges** in the graph | QUESTION-ONTOLOGY | High |
| 7 | Declare a **fixed diverse industry panel** as the B12 generalization golden set | QUESTION-ONTOLOGY / PROGRAM | High |
| 8 | Define **QA spot-fetch sample size** (≥20% sources, 100% of critical formulae) | DEPTH-RUBRIC §3 / PROGRAM §3 | Med |
| 9 | Add **rework-loop circuit-breaker** (N FAILs → mandatory CRO arbitration) | RESEARCH-ORG §5.1 / PROGRAM §4 | Med |
| 10 | Add **operational independence test** for "independent sources" | DEPTH-RUBRIC §1 | Med |
| 11 | Correct **seed-branch "present" wording** to match disk reality | RESEARCH-PROGRAM §6 | Low |
| 12 | Add **no-self-dependency-review** clause for QA | RESEARCH-ORG §3.5 | Low |
| 13 | Flag CLAUDE.md **placeholder substitution** to CRO before any L2 build question | (escalation) | Low (blocks L2, not L1) |

---

## Final verdict

**GRADE: AMBER.** The blueprint is sound in shape and rigorous on depth; it has two governance gaps
(single-writer lock, must-study-CLAUDE.md) and two coverage holes (client product/design, client
software delivery) that must be closed before teams are spawned, plus several smaller tightenings.
All fixes are local edits to the four existing files — no re-architecture.

**Layer 1 may proceed: YES** — conditional on fixes #1, #2, #3 (blockers) being folded into the
Wave-1 plan *before researchers are assigned to artifacts*, and #4–#7 added to the ontology before
Layer-1 scouting begins on the affected branches. Fixes #8–#13 may land during Wave 1.
