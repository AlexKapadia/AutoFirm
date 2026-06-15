# SUMMARY — Beyond the Strongest LLM: Multi-Turn Multi-Agent Orchestration vs. Single LLMs on Benchmarks

## Full citation
- **Title:** Beyond the Strongest LLM: Multi-Turn Multi-Agent Orchestration vs. Single LLMs on
  Benchmarks
- **Authors:** Aaron Xuxiang Tian, Ruofan Zhang, Jiayao Tang, Young Min Cho, Xueqian Li, Qiang Yi,
  Ji Wang, Zhunping Zhang, Danrui Qi, Zekun Li, Xingyu Xiang, Sharath Chandra Guntuku, Lyle Ungar,
  Tianyu Shi, Chi Wang
- **Year:** 2025 (submitted 28 Sep 2025)
- **Venue:** arXiv preprint (arXiv:2509.23537).
- **URL:** https://arxiv.org/abs/2509.23537 ; PDF: https://arxiv.org/pdf/2509.23537

## Questions informed
- **L1.A1.2** (when does multi-agent orchestration beat the single strongest LLM) — PRIMARY.
- L1.A1.1 (consensus/voting orchestration pattern) — supporting.
- L1.A1.4 (herding / premature consensus as a coordination cost) — supporting.

## GRADE tier
**Moderate.** arXiv preprint, recent, with a clear cross-model experimental design over three
recognized benchmarks; not yet peer-reviewed (down-rate). Up-rated for using multiple frontier models
and standard benchmarks, and for corroborating the multi-beats-single direction independently of the
vendor source (02). Specific per-benchmark numbers were not extractable from the abstract page;
the directional conclusions are stated and relied upon.

## Method (faithful)
- Multi-turn, multi-agent **orchestration via consensus**: "multiple large language model (LLM) agents
  interact over multiple turns by iteratively proposing answers or casting votes until reaching
  consensus."
- Agents drawn from four frontier models: **Gemini 2.5 Pro, GPT-5, Grok 4, Claude Sonnet 4**.
- Benchmarks: **GPQA-Diamond, IFEval, MuSR**.

## Key findings (faithful)
- "**Orchestration matches or exceeds the strongest single model and consistently outperforms the
  others.**" (Heterogeneous orchestration lifts the ensemble above its weaker members and is
  competitive with / better than the single best model.)
- Information-transparency effects on the consensus dynamics:
  - "revealing **authorship** increases self-voting and ties"
  - "showing **ongoing votes** amplifies **herding**, which speeds convergence but can sometimes
    yield **premature consensus**."

## Reproducibility note
Method, model list, benchmark list, and the headline "matches or exceeds the strongest single model"
conclusion plus the herding/authorship effects were extracted via WebFetch of the arXiv abstract
page. Exact per-benchmark accuracy deltas are in the PDF tables (not extracted); the directional
conclusion is what AutoFirm relies on, and it is corroborated by sources 02, 03, and the clinical
workload study for the broader L1.A1.2 claim.
