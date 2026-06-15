# SUMMARY — Towards a Science of Scaling Agent Systems: When and Why Agent Systems Work

## Full citation
- **Title:** Towards a Science of Scaling Agent Systems: When and Why Agent Systems Work
- **Authors (20, exact order; arXiv:2512.08296 author block):** Yubin Kim^{1,2}, Ken Gu^1,
  Chanwoo Park^2, Chunjong Park^1, Samuel Schmidgall^1, A. Ali Heydari^1, Yao Yan^1, Zhihan Zhang^1,
  Yuchen Zhuang^1, Yun Liu^1, Mark Malhotra^1, Paul Pu Liang^2, Hae Won Park^2, Yuzhe Yang^1,
  Xuhai Xu^1, Yilun Du^1, Shwetak Patel^1, Tim Althoff^1, Daniel McDuff^1, Xin Liu^1.
  - **Affiliations:** ^1 Google Research / Google DeepMind; ^2 Massachusetts Institute of Technology (MIT).
  - **MIT-affiliated (^2):** Yubin Kim (jointly with Google), Chanwoo Park, Paul Pu Liang, Hae Won Park.
  - **Corresponding authors:** Yubin Kim, Xin Liu.
  - Locator: arXiv:2512.08296 author block (names: abstract page https://arxiv.org/abs/2512.08296;
    affiliation superscripts: rendered HTML/PDF first page https://arxiv.org/html/2512.08296 — the
    abstract page itself shows the 20 names without superscripts).
- **Year:** 2026 (arXiv 2512.08296, submitted 2025-12-09, latest revision 2026-04-08; Google Research
  blog post 28 Jan 2026).
- **Venue:** arXiv preprint with full methods + results + a controlled multi-configuration study;
  authored jointly by Google Research, Google DeepMind, and MIT.
- **URL:** https://arxiv.org/abs/2512.08296 ;
  blog: https://research.google/blog/towards-a-science-of-scaling-agent-systems-when-and-why-agent-systems-work/

## Questions informed
- **L1.A1.2** (when does multi-agent beat a single strong agent) -- PRIMARY corroboration.
  Independently corroborates the prior reliance on the Anthropic blog (source 02, Low-Moderate tier)
  for the central multi-vs-single and cost/diminishing-returns claims with a controlled, multi-model
  study -- upgrading the body of evidence for those claims.
- L1.A1.1 (failure modes -- error amplification per topology) -- supporting.
- L1.A1.4 (coordination cost / when coordination overhead outweighs benefit) -- supporting.

## GRADE tier
**Moderate-High.** Reputable primary research (Google Research / Google DeepMind / MIT) with explicit methods, ablations, and
a large controlled design across **three independent model families** (OpenAI GPT, Google Gemini,
Anthropic Claude) -- so it is **independent** of source 02 (Anthropic) and source 03 (HALO). arXiv
preprint (not yet a peer-reviewed venue at time of writing) -> capped below "High" pending publication,
but up-rated for scale, multi-family consistency, and methodological transparency. Its role is to
**corroborate**, not to be a sole basis.

## Method (faithful) — config/benchmark count differs by artifact version
- The two primary artifacts report DIFFERENT scale figures; both are stated with their exact locator
  because the paper was revised after the blog:
  - **arXiv abstract (latest, v3, revised 2026-04-08, https://arxiv.org/abs/2512.08296):**
    **260 configurations** spanning **six agentic benchmarks**.
  - **Google Research blog (28 Jan 2026):** **180 agent configurations** across **four diverse
    benchmarks** (Finance-Agent, BrowseComp-Plus, PlanCraft, Workbench). The blog tracks the earlier
    (v1/v2) version of the study.
  - The four named benchmarks above are the blog's set; they are an **incomplete subset of the six**
    benchmarks in the latest arXiv abstract (the remaining two are not enumerated in the abstract
    text and are not relied upon here).
- **5 canonical architectures** (single-agent plus four multi-agent variants) and **3 model families**
  (OpenAI GPT, Google Gemini, Anthropic Claude) are consistent across both artifacts.
- Builds a predictive model mapping *task structure* -> *best architecture*, then tests it on unseen tasks.

## Key findings (faithful, exact numbers + locators)
- **Task structure decides everything**: on **decomposable / parallelizable** tasks (financial
  reasoning), centralized coordination **improved performance by +80.8%** over a single-agent baseline;
  on **sequential planning** tasks the headline degradation is **-70.0%** (arXiv abstract,
  https://arxiv.org/abs/2512.08296). The Google Research blog gives the per-variant degradation as a
  range — **"every multi-agent variant degraded performance by 39-70%"** on sequential tasks
  (blog locator: https://research.google/blog/towards-a-science-of-scaling-agent-systems-when-and-why-agent-systems-work/).
  The **39%** lower bound is the blog's range floor; the **-70.0%** single figure is the abstract's
  headline — both are stated here with their exact source so each number is independently verifiable.
- **Diminishing returns / saturation**: benefit shrinks once the single-agent baseline is already strong;
  the paper reports a hard resource ceiling — under fixed compute, per-agent reasoning capacity becomes
  too thin **beyond ~3-4 agents**, where communication cost dominates reasoning capability (arXiv
  body, https://arxiv.org/abs/2512.08296). (The blog separately frames a ~45% single-agent-baseline
  region above which the multi-agent benefit erodes; flagged as benchmark-specific, see Limitations.)
- **Error amplification differs by topology** (Google Research blog,
  https://research.google/blog/towards-a-science-of-scaling-agent-systems-when-and-why-agent-systems-work/):
  independent (uncoordinated) systems **amplified errors 17.2x**; centralized coordination contained
  amplification to **4.4x** -- a quantitative argument for a *coordinated* topology over a loose
  "bag of agents". (These figures are in the BLOG, not the arXiv abstract.)
- The predictive task->architecture model reached **87%** accuracy selecting the optimal coordination
  strategy on unseen task configurations (Google Research blog, same URL) -- evidence that *routing by
  task structure* (AutoFirm's routing predicate) is learnable and effective.

## Limitations (faithful)
- Benchmark-bound thresholds (the ~45% baseline figure is specific to the studied benchmarks) -> treat as
  directional, re-measure on AutoFirm's own golden set (CLAUDE.md 3.9 no overfitting).
- Preprint (pending peer review). Used only as corroboration of an already multi-source claim.

## Reproducibility note (per-number locator map)
Each relied-upon number is tied to its exact artifact so a re-deriving reviewer lands on the right source:
- **+80.8%** (decomposable financial reasoning) and **-70.0%** (sequential planning) -> arXiv abstract,
  https://arxiv.org/abs/2512.08296.
- **260 configs / six benchmarks** -> arXiv abstract (latest v3, 2026-04-08), same URL.
- **180 configs / four benchmarks** (Finance-Agent, BrowseComp-Plus, PlanCraft, Workbench), the
  **39-70%** degradation range (incl. the **39%** floor), **17.2x vs 4.4x** error amplification, and the
  **87%** routing accuracy -> Google Research blog,
  https://research.google/blog/towards-a-science-of-scaling-agent-systems-when-and-why-agent-systems-work/.
- **~3-4 agents** resource ceiling -> arXiv paper body (https://arxiv.org/abs/2512.08296).
Benchmark-specific thresholds (e.g. the ~45% baseline) are flagged as directional, not absolute targets.
