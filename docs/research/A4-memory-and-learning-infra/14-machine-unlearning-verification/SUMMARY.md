# SUMMARY — Towards Reliable Forgetting: A Survey on Machine Unlearning Verification

## Full citation
- **Title:** Towards Reliable Forgetting: A Survey on Machine Unlearning Verification
- **Authors:** (survey author group; see arXiv listing) — Machine Unlearning Verification survey
- **Year:** 2025
- **Venue:** arXiv preprint
- **arXiv ID / URL:** arXiv:2506.15115 — https://arxiv.org/pdf/2506.15115
- Supporting/contrast source: "Unlearning Isn't Deletion: Investigating Reversibility of Machine Unlearning in LLMs" — arXiv:2505.16831 — https://arxiv.org/html/2505.16831v1

## Questions informed
- **L1.A4.4** Memory security & governance (deletion-verify / Verified Forgetting primitive).

## Key claims (faithful)
1. **Verification is the gap, not deletion itself.** "Without a trustworthy verification mechanism,
   compliance claims remain unsubstantiated"; unlearning verification "enables model providers to
   generate verifiable compliance artifacts while allowing users and auditors to assess whether data
   deletion has occurred."
2. **Exact vs approximate unlearning.** Exact unlearning = retraining from scratch on the dataset
   minus the removed samples (gold standard, but costly/impractical for LLMs). Approximate unlearning
   = techniques to remove a sample's influence from trained weights without full retraining.
3. **Reversibility risk (supporting source 2505.16831):** apparent "unlearning" in LLMs can be
   reversible — content that seems removed can be recovered — so deletion must be *verified*
   irrecoverable, not assumed.

## GRADE tier
- **Moderate.** arXiv surveys (secondary), recent and directly on-topic; corroborate the LTM-security
  survey's Verified-Forgetting primitive (folder 12) with the broader unlearning literature.

## Reproducibility note
Exact/approximate distinction and the verification-gap argument are central claims at the arXiv URLs;
the reversibility finding is from the companion empirical study.
