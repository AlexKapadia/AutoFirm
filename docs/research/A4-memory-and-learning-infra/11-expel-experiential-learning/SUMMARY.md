# SUMMARY — ExpeL: LLM Agents Are Experiential Learners

## Full citation
- **Title:** ExpeL: LLM Agents Are Experiential Learners
- **Authors:** Andrew Zhao, Daniel Huang, Quentin Xu, Matthieu Lin, Yong-Jin Liu, Gao Huang (Tsinghua University)
- **Year:** 2024
- **Venue:** Proceedings of the AAAI Conference on Artificial Intelligence, Vol. 38(17), pp. 19632-19642 (AAAI 2024, oral), peer-reviewed
- **DOI / URL:** https://ojs.aaai.org/index.php/AAAI/article/view/29936 ; arXiv:2308.10144 ; code: https://github.com/LeapLabTHU/ExpeL

## Questions informed
- **L1.A4.3** Learning-over-time (experience abstraction: extracting reusable insights from many trajectories).

## Key claims (faithful)
1. **Experience gathering + insight extraction without parametric updates.** The agent autonomously
   collects trajectories across a set of **training tasks**, then uses the LLM to **extract
   natural-language insights** (cross-task rules/lessons) and stores successful trajectories.
2. **At inference**, the agent **recalls extracted insights + relevant past experiences** to inform
   decisions (k-NN retrieval of similar past tasks + the distilled insight set).
3. **Motivation (exact intent):** fine-tuning is resource-intensive and SOTA models (GPT-4, Claude)
   are API-only with proprietary weights, so learning must happen **from experience without
   parametric updates**.
4. **Result:** ExpeL shows **consistent performance improvement as experiences accumulate**, and
   improves over base ReAct/Reflexion-style agents on the evaluated decision-making/QA benchmarks.

## GRADE tier
- **High.** Peer-reviewed AAAI 2024 (oral). Specific per-benchmark deltas treated as Moderate pending
  independent replication; the qualitative "improves with accumulated experience" claim is well-supported.

## Reproducibility note
Insight-extraction + experience-recall pipeline described in the Method; open-source code enables
replication on the listed benchmarks.
