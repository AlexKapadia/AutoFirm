# SUMMARY — Wang et al. "The Long-Horizon Task Mirage? Diagnosing Where and Why Agentic Systems Break"

## Full citation
- **Title:** The Long-Horizon Task Mirage? Diagnosing Where and Why Agentic Systems Break
- **Authors:** Xinyu Jessica Wang, Haoyue Bai, Yiyou Sun, Haorui Wang, Shuibai Zhang, Wenjie Hu, Mya Schroder, Bilge Mutlu, Dawn Song, Robert D. Nowak
- **Year:** 2026
- **Venue:** COLM 2026; arXiv:2604.11978 (v1)
- **URL/DOI:** https://arxiv.org/abs/2604.11978 ; https://arxiv.org/html/2604.11978v1

## Ontology questions informed
- **L1.A3.2** Long-horizon failure modes (PRIMARY — drift, context loss, error accumulation).
- Supporting **L1.A4.*** (memory limits) and **L2.A3** (what the resume protocol must defend against).

## GRADE tier
- **Moderate–High.** Accepted at COLM 2026 (a recognized venue) — up-rated above bare arXiv. Strong empirical base: 3,100+ trajectories across 4 domains, dual annotation with reported agreement. Down-rate: very recent, single study.

## Key claims (exact taxonomy + numbers)
**Seven-category failure taxonomy** ([L]=long-horizon-specific, [S]=amplified under longer horizons):
1. **Environment Error [S]** — agent fails detecting environment changes.
2. **Instruction Error [S]** — misinterpreting / partially understanding instructions.
3. **False Assumption [S]** — incorrect beliefs about task state.
4. **Planning Error [S]** — flawed subplanning or action ordering.
5. **Catastrophic Forgetting [L]** — losing constraints despite the constraint being present in context.
6. **History Error Accumulation [L]** — compounding early mistakes across steps.
7. **Memory Limitation [L]** — information lost from the context window.

**Three structural patterns:**
- **Non-linear degradation:** success stable initially, then "sharp performance drop beyond small s" (a structural shift in failure *composition*, not just a declining rate).
- **Domain variation:** web tasks collapse at minimal extension; embodied tasks degrade most steeply.
- **Converging failure rates:** model performance gaps narrow in the "breaking" region.

**Quantitative:**
- Inter-annotator agreement **kappa = 0.61**; human–judge agreement **kappa = 0.84**.
- **3,100+ trajectories** across four domains (Web, OS, Embodied, Database).
- Failure-source split: **72.5% process-level risks; 27.5% design-level risks.**
- "Planning and memory failures constitute dominant failure modes at longer horizons."
- Conclusion (quoted): "base-model scaling alone is unlikely to fully address these failures" — planning and memory need **architectural** solutions.

## Reproducibility note
Re-fetch arxiv.org/html/2604.11978v1. The seven categories, the [L]/[S] tags, kappa values, 3,100+ trajectory count, and 72.5/27.5 process/design split are quoted from the HTML. These directly drive AutoFirm's resume-protocol threat model.
