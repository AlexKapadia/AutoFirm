# SUMMARY — Why Do Multi-Agent LLM Systems Fail? (MAST)

## Full citation
- **Title:** Why Do Multi-Agent LLM Systems Fail?
- **Authors:** Mert Cemri, Melissa Z. Pan, Shuyi Yang, Lakshya A. Agrawal, Bhavya Chopra,
  Rishabh Tiwari, Kurt Keutzer, Aditya Parameswaran, Dan Klein, Kannan Ramchandran,
  Matei Zaharia, Joseph E. Gonzalez, Ion Stoica (UC Berkeley et al.)
- **Year:** 2025
- **Venue:** NeurIPS 2025 Datasets & Benchmarks Track (spotlight); arXiv:2503.13657
- **URL/DOI:** https://arxiv.org/abs/2503.13657 · OpenReview: https://openreview.net/forum?id=fAjbYBmonr
  · Repo: https://github.com/multi-agent-systems-failure-taxonomy/MAST

## Questions it informs
- **L1.A2.1** (what message/contract design must prevent — supporting)
- **L1.A2.2** (reliability of coordination — PRIMARY, the central evidence)

## GRADE tier: High
Peer-reviewed (NeurIPS D&B spotlight), large empirical study, strong inter-rater reliability.
**Up-rate:** large, consistent dataset (1600+ traces, 7 frameworks), high kappa, open data.
No material down-rate. This is the anchor primary source for A2 reliability claims.

## Key claims (exact numbers + locators)

- **MAST = Multi-Agent System Failure Taxonomy:** "14 unique failure modes" organized into
  **3 categories** (abstract).
- **Method:** "1600+ annotated traces" across "7 popular MAS frameworks"; inter-annotator
  agreement **Cohen's kappa = 0.88** (abstract / OpenReview).
- **Category prevalence (from Berkeley MAST project page):**
  - **FC1 Specification / System Design issues: 41.77%**
  - **FC2 Inter-Agent Misalignment: 36.94%**
  - **FC3 Task Verification (and Termination): 21.30%**
- **FC3 sub-breakdown (futureagi summary of paper):** premature task ending 6.2%,
  incomplete verification 8.2%, incorrect verification 9.1%.

**Named failure modes (verified subset):**
- FC1: task misinterpretation, ambiguous role definitions, poor decomposition,
  duplicate agent roles, missing termination conditions; e.g. **FM-1.3 step repetition**.
- FC2 (Inter-Agent Misalignment): **FM-2.1 conversation reset**, **FM-2.4 information
  withholding** ("failure to share critical data across agents"), **FM-2.6 reasoning-action
  mismatch** ("inconsistency between reasoning and behavior"); category also covers
  communication breakdowns, context loss during handoffs, conflicting outputs, format
  mismatches between agents, and gradual derailment from the initial task.
- FC3: **FM-3.1 premature termination**; incomplete/incorrect verification.

**Load-bearing qualitative finding (quoted, OpenReview/paper discussion):** solutions
"focused on context or communication protocols are often insufficient for inter-agent
misalignment failures, which demand deeper 'social reasoning' abilities from agents," and a
subordinate agent may "disobey" its role, "unilaterally making executive decisions."

## Reproducibility note
Category percentages, kappa, and trace counts are re-derivable from the open MAST-Data dataset
(GitHub / HuggingFace) and the NeurIPS camera-ready (OpenReview id wM521FqPvI). The exact
per-mode percentages beyond those quoted should be re-confirmed against Table 3 of the paper
before being treated as safety-critical.
