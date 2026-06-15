# SUMMARY — Zhu et al. "Where LLM Agents Fail and How They Can Learn From Failures"

## Full citation
- **Title:** Where LLM Agents Fail and How They Can Learn From Failures
- **Authors:** Kunlun Zhu, Zijia Liu, Bingxuan Li, Muxin Tian, Yingxuan Yang, Jiaxun Zhang, Pengrui Han, Qipeng Xie, Fuyang Cui, Weijia Zhang, Xiaoteng Ma, Xiaodong Yu, Gowtham Ramesh, Jialian Wu, Zicheng Liu, Pan Lu, James Zou, Jiaxuan You
- **Year:** 2025 (arXiv:2509.25370v1, 2025-10-01)
- **Venue:** arXiv (also on OpenReview); code: github.com/ulab-uiuc/AgentDebug
- **URL/DOI:** https://arxiv.org/abs/2509.25370

## Ontology questions informed
- **L1.A3.2** Long-horizon failure modes (PRIMARY — taxonomy + error-propagation).
- Supporting **L1.A9.*** (eval of failures) and **L2.A3** (validation/correction in the resume loop).

## GRADE tier
- **Moderate.** arXiv + OpenReview, with a released tool (AgentDebug) and benchmark results — reproducible. Tiered Moderate (§2 preprint). Corroborates source 05's taxonomy from an independent author group (different institutions), strengthening the failure-mode body of evidence.

## Key claims (exact taxonomy + numbers)
- **AgentErrorTaxonomy — five modules:** **memory, reflection, planning, action, and system-level operations.** Failures are organized "as a causal lens for understanding how failures originate, propagate, and interact across modules."
- **Error propagation thesis:** "a single root-cause failure can cascade into successive errors, compounding degradation and leading to task failure"; early mistakes "cascade into subsequent steps... ultimately derailing the entire trajectory."
- **Method — AgentDebug:** systematically attributes a trajectory's failure to its **root-cause step + module**, enabling targeted correction.
- **Quantitative results (from abstract):**
  - "AgentDebug achieves **24% higher all-correct accuracy** and **17% higher step accuracy** compared to the strongest baseline."
  - Failure-informed correction yields "**up to 26% relative improvements in task success**" across **ALFWorld, GAIA, and WebShop** benchmarks.

## Reproducibility note
Re-fetch arXiv:2509.25370 abstract for the 24% / 17% / 26% figures and the five-module taxonomy. Benchmarks (ALFWorld/GAIA/WebShop) and the AgentDebug repo are independently checkable. The five-module taxonomy and source-05's seven-category taxonomy are complementary (module-of-origin vs. symptom), not contradictory.
