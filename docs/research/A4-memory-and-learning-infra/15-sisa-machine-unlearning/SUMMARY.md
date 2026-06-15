# SUMMARY — Machine Unlearning (SISA)

## Full citation
- **Title:** Machine Unlearning
- **Authors:** Lucas Bourtoule, Varun Chandrasekaran, Christopher A. Choquette-Choo, Hengrui Jia,
  Adelin Travers, Baiwu Zhang, David Lie, Nicolas Papernot
- **Year:** 2021 (arXiv 2019)
- **Venue:** **IEEE Symposium on Security and Privacy (S&P / "Oakland") 2021** — peer-reviewed,
  top-tier security venue
- **arXiv ID / URL:** arXiv:1912.03817 — https://arxiv.org/abs/1912.03817
- **DOI:** 10.1109/SP40001.2021.00019

## Questions informed
- **L1.A4.4** Memory security & governance — the **Verified Forgetting (VF)** primitive: what "exact"
  deletion costs and why an external-store design sidesteps it. **Primary** source for the
  exact-vs-approximate deletion distinction relied on in SYNTHESIS L1.A4.4.

## Key claims (faithful)
1. **SISA (Sharded, Isolated, Sliced, Aggregated) training** "expedites the unlearning process by
   strategically limiting the influence of a data point in the training procedure." Training data is
   partitioned into shards; each shard trains an isolated constituent model; only the shard(s)
   containing a removed point are retrained, then predictions are aggregated.
2. **Exact unlearning is retraining-from-scratch on the data minus the removed sample** — the gold
   standard the paper accelerates but does not eliminate. SISA reduces *retraining cost*, it does not
   make weight-baked influence free to remove.
3. **Measured speed-ups (exact numbers, from abstract):** unlearning is **4.63x** faster on the
   Purchase dataset and **2.45x** on SVHN over retraining from scratch, with a **1.36x** speed-up on
   ImageNet classification — i.e. even an optimized approach to forgetting weight-baked data remains
   expensive at scale.

## GRADE tier
- **High.** Peer-reviewed at IEEE S&P (top security venue), large/consistent measured effect across
  multiple datasets, foundational and heavily cited. No down-rate; up-rated for consistency across
  datasets.

## Why this strengthens the body of evidence
The A4.4 VF claim ("deletion must be exact and provable") was previously corroborated only by two
arXiv **surveys** (folders 12, 14, both Moderate). SISA is the **primary, peer-reviewed** anchor for
the exact-vs-approximate distinction, and its measured retraining costs are the quantitative argument
FOR AutoFirm keeping durable memory in an **external store** (folder 05) where deletion is a cheap,
exact drop+reindex rather than an expensive, never-fully-verifiable weight operation.

## Reproducibility note
SISA construction (Section: "SISA training") and the speed-up numbers (abstract + evaluation tables)
are re-derivable at the arXiv URL / DOI.
