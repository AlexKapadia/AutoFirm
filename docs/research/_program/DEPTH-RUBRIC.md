# AutoFirm Research Depth Rubric (DEPTH-RUBRIC.md)

> The explicit, non-negotiable quality bar **per research question**. The Peer-Review/QA
> function (RESEARCH-ORG.md §3.5) audits every question against this rubric and is empowered to
> **FAIL and return** work. Implements CLAUDE.md §3.3 (deep peer-reviewed research), §3.6
> (tests/evidence with teeth), and §2 (CRO gate).
>
> **Grounding.** Source-grading uses an evidence-hierarchy discipline adapted from GRADE
> (high/moderate/low/very-low confidence, with explicit reasons to up/down-rate). Review process
> follows Kitchenham/PRISMA SLR rigor (plan → conduct → report, auditable & reproducible). Full
> citations in RESEARCH-PROGRAM.md §Sources.

---

## 1. Source-count minimums (per CLAIM, not per question)

A "claim" = any factual/quantitative statement AutoFirm will rely on (a formula, a benchmark
number, a design recommendation, an empirical effect).

| Claim criticality | Min. INDEPENDENT primary/peer-reviewed sources | Notes |
|---|---|---|
| **Safety/correctness-critical** (security control, deterministic formula, audit invariant) | **≥ 3** | Independent = different authors/orgs. At least one must be primary/peer-reviewed, not a survey-of-surveys. |
| **Important** (architecture choice, core business playbook step) | **≥ 2** | |
| **Supporting/contextual** | **≥ 1** primary + may add secondary for color | Secondary alone never suffices for a relied-upon claim. |

- **Independence rule:** two sources that cite the *same* underlying study count as **one**.
- **Primary preferred:** prefer the original paper/standard/filing over a blog summarizing it.
- A single source supporting a critical claim → **automatic FAIL** (insufficient corroboration).

---

## 2. Source-quality grading (GRADE-adapted)

Every source is tagged with a confidence tier; the *body of evidence* for a claim inherits the
**lowest tier that materially supports it** unless corroborated up.

| Tier | Typical source | Starting confidence |
|---|---|---|
| **High** | Peer-reviewed venue (top conf/journal), official standard, audited primary filing, RCT/controlled study | High |
| **Moderate** | Reputable preprint (arXiv) with methods + results, recognized industry primary data, government statistics | Moderate |
| **Low** | Vendor whitepaper, practitioner book, well-sourced secondary survey | Low |
| **Very low** | Blog, forum, undated/unsourced page, marketing copy | Very low — **never** a sole basis for a relied-upon claim |

**Down-rate** for: risk of bias, indirectness (source is about a different setting), imprecision,
inconsistency with other sources, suspected publication bias. **Up-rate** for: large/consistent
effect across independent sources, dose-response, all-plausible-confounders-would-reduce-effect.
Each up/down-rate must be **written down** in `SUMMARY.md`.

---

## 3. Exact-citation rules (zero fabrication)

Fabrication or misrepresentation of a source is the **single most serious defect** and is an
**automatic FAIL** of the whole question (CLAUDE.md §3.3: "never misrepresent").

1. **Full attribution every time:** *Title · Author(s)/Org · Year · Venue/Publisher · URL/DOI*.
   A missing field → FAIL until supplied.
2. **Formulae reproduced exactly**, in the source's own notation, with the equation/section
   reference. Any adaptation is labeled "adapted" and the original is shown alongside.
3. **Quantitative claims carry the exact number + units + the table/figure/page** they came from.
4. **Quote when in doubt.** Prefer a short exact quote (with quotation marks + locator) over a
   loose paraphrase for any contested or load-bearing statement.
5. **No dead/unverifiable citations.** QA spot-fetches a defined sample — **≥ 20% of the question's
   sources (minimum 2), and 100% of all safety/correctness-critical formulae and quantitative
   claims** — confirming each resolves and says what is claimed; an unresolvable URL/DOI → FAIL.
   ("A sample" is never left to reviewer discretion — this closes the verification loophole and
   directly beats the agent-eval finding that <20% of studies verify their numbers.)
6. **No hallucinated sources.** Every reference must be a real, retrievable artifact. QA verifies
   existence; a non-existent source is fabrication → FAIL + escalation to CRO.

---

## 4. Full-alternative-space coverage (survey EVERYTHING, then choose)

A question is shallow if it studies one convenient approach. Every question's artifacts must:

1. **Enumerate the full method/option space** relevant to the question (e.g. for orchestration:
   orchestrator-worker, hierarchical, blackboard, market/auction, debate, swarm — not just the
   one we like). For business: the full menu (e.g. pricing: value-based, cost-plus, dynamic,
   freemium, usage-based) — deterministic rules, trees, GBMs, DNNs, glass-box, **hybrids**
   where the question is ML-shaped (CLAUDE.md §3.4–3.5).
2. **For each option: an explicit ADOPT / REJECT / DEFER decision with rationale** tied to cited
   evidence (lives in `BEST-PARTS.md`). "Rejected because X (source Y)" — never silent omission.
3. **Name what was excluded and why** (scope boundary), so coverage gaps are visible, not hidden.
4. **Prefer hybrids** by default where requirements conflict; justify if a single paradigm wins.

---

## 5. Real-world usefulness (it must inform the build)

Faithful summaries are necessary but not sufficient. Each question must show **how it changes
what AutoFirm does**:

- `BEST-PARTS.md` states **what AutoFirm adopts and the design implication** (which component,
  which contract, which test it drives) — not just "this paper is interesting".
- For business questions: the playbook step must be **industry-parameterized** (works for ANY
  industry/size), not fitted to one example company (generality, CLAUDE.md §3.9).
- Quantitative/efficacy claims must be **expressed in a form a test or evidence chart can use**
  (a number, a threshold, an accuracy/latency target) — feeding `evidence/` (CLAUDE.md §3.10).

---

## 6. What DISQUALIFIES work (instant FAIL conditions)

QA fails-and-returns the question if **any** of these hold:

- ✗ A relied-upon claim rests on **< the required source count** or on a **Very-low** tier alone.
- ✗ **Any** fabricated, misattributed, or unverifiable source/formula/number ("vibe citation").
- ✗ A formula or finding **paraphrased inaccurately** vs. the original.
- ✗ The **alternative space is not surveyed** (single-approach tunnel vision) or options listed
   with no adopt/reject rationale.
- ✗ **Overfit:** conclusions tied to one example/dataset/company; no generalization argument.
- ✗ **No build implication** in `BEST-PARTS.md` (research-for-its-own-sake).
- ✗ Missing citation fields, dead links, or unstated up/down-rate reasoning.
- ✗ **Dependency not satisfied:** an L2/L3 question built on an un-PASSED L1 dependency.
- ✗ Plagiarism / verbatim copying beyond short attributed quotes.

A FAIL returns a **written defect list**; the question re-enters the iterate-to-perfection loop
(RESEARCH-PROGRAM.md §iteration) and cannot be marked "answered" by the CRO until QA PASSes.

---

## 7. PASS checklist (QA sign-off)

A question PASSES only when **all** are true:

- ☑ Source counts met per §1; every source graded per §2 with reasons.
- ☑ Every citation exact and verifiable per §3 (QA spot-fetched a sample).
- ☑ Full alternative space surveyed with adopt/reject rationale per §4.
- ☑ `BEST-PARTS.md` states concrete, general, build-relevant implications per §5.
- ☑ No §6 disqualifier present.
- ☑ All ontology dependencies for the question are themselves PASSED.
- ☑ Reproducibility note present (how a reviewer can re-derive the conclusion).

> **The bar in one line:** every claim AutoFirm relies on is corroborated by enough independent,
> exactly-cited primary sources; the full option space was surveyed and judged; the conclusion is
> general (not overfit); and it concretely changes the build — proven, not vibed.
