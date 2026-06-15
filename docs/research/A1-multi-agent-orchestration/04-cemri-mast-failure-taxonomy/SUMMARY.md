# SUMMARY — Why Do Multi-Agent LLM Systems Fail? (MAST / MASFT taxonomy)

## Full citation
- **Title:** Why Do Multi-Agent LLM Systems Fail?
- **Authors:** Mert Cemri, Melissa Z. Pan, Shuyi Yang, Lakshya A. Agrawal, Bhavya Chopra, Rishabh
  Tiwari, Kurt Keutzer, Aditya Parameswaran, Dan Klein, Kannan Ramchandran, Matei Zaharia,
  Joseph E. Gonzalez, Ion Stoica (UC Berkeley et al.)
- **Year:** 2025
- **Venue:** arXiv:2503.13657 ; also on OpenReview (id=fAjbYBmonr) — peer-reviewed track.
- **URL:** https://arxiv.org/abs/2503.13657 ; HTML: https://arxiv.org/html/2503.13657v1 ;
  OpenReview: https://openreview.net/forum?id=fAjbYBmonr

## Questions informed
- **L1.A1.1** (failure modes per coordination pattern) — PRIMARY, definitive.
- **L1.A1.2** (does multi-agent actually beat single?) — PRIMARY (sobering counter-evidence:
  "performance gains on popular benchmarks are often minimal").
- L1.A1.4 (coordination cost as inter-agent misalignment) — supporting.

## GRADE tier
**High (for the failure taxonomy).** Empirically grounded on 1600+ annotated traces / 200+ tasks
across 7 frameworks (HTML extract notes 150+ traces deeply analyzed across 5 named frameworks: MetaGPT,
ChatDev, HyperAgent, AppWorld, AG2), 6 expert annotators, validated inter-annotator agreement, and an
LLM-as-judge pipeline. Peer-reviewed (OpenReview). The most authoritative source on MAS failure modes.

## MASFT taxonomy — 3 categories, 14 modes (with prevalence %)
**FC1. Specification & System Design Failures (28.5%)**
- FM-1.1 Disobey task specification (7.3%)
- FM-1.2 Disobey role specification (5.3%)
- FM-1.3 Step repetition (6.0%)
- FM-1.4 Loss of conversation history (4.6%)
- FM-1.5 Unaware of termination conditions (5.3%)

**FC2. Inter-Agent Misalignment (39.1%)** — the LARGEST category
- FM-2.1 Conversation reset (5.3%)
- FM-2.2 Fail to ask for clarification (6.6%)
- FM-2.3 Task derailment (10.6%)
- FM-2.4 Information withholding (5.3%)
- FM-2.5 Ignored other agent's input (6.6%)
- FM-2.6 Reasoning-action mismatch (4.6%)

**FC3. Task Verification & Termination (32.5%)**
- FM-3.1 Premature termination (13.2%)
- FM-3.2 No or incomplete verification (14.6%)
- FM-3.3 Incorrect verification (5.3%)

## Validation metrics (exact)
- Inter-annotator agreement (Cohen's κ): Round 1 = 0.24; Round 2 ≈ 0.92; Round 3 = 0.84.
- LLM-as-judge (few-shot) vs human: Cohen's κ = **0.77**.
- Intervention examples: ChatDev baseline accuracy 25%; +14% with interventions; AG2 +5% with prompt
  engineering. (Tactical fixes give limited gains — see conclusion.)

## Main conclusion (load-bearing)
- "many MAS failures arise from the challenges in inter-agent interactions rather than the
  limitations of individual agents."
- "improvements in the base model capabilities will be **insufficient** to address the full MASFT."
- Fix is **structural/organizational** (verification, communication protocols, state management),
  not merely better models or prompts: "good MAS design requires organizational understanding."

## Reproducibility note
Categories, all 14 modes, percentages, and κ values extracted via WebFetch of the arXiv HTML.
These are safety/correctness-critical (they define AutoFirm's required test matrix), so they are
corroborated structurally by source 01 (cascading failure, central-point) and 02 (Anthropic's
observed failures: duplicate work, premature stop, ignored-context).
