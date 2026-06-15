# SUMMARY — Defeating Nondeterminism in LLM Inference

## Full citation
- **Title:** "Defeating Nondeterminism in LLM Inference"
- **Author(s):** Horace He, with collaborators at Thinking Machines Lab
- **Year:** 2025 (published Sept 10, 2025)
- **Venue/Publisher:** Thinking Machines Lab (technical blog / research note)
- **URL:** https://thinkingmachines.ai/blog/defeating-nondeterminism-in-llm-inference/
  (independent corroboration: Simon Willison's notes
  https://simonwillison.net/2025/Sep/11/defeating-nondeterminism/ ; related arXiv:2601.17768
  "LLM-42: Enabling Determinism in LLM Inference with Verified Speculation")

## Questions informed
- **L1.A5.2** Determinism, resumability & idempotency of CLI sessions — the MODEL-OUTPUT side:
  WHY identical inputs to the LLM can yield different outputs, independent of the substrate's
  deterministic state handling (source 08). Also feeds A9.2 (statistical rigor for stochastic
  systems) and CLAUDE.md §3.5 (deterministic core / stochastic ML layer split).

## GRADE tier
**Moderate** — a high-quality primary technical report from a credible lab with a reproducible
experiment and open code (`thinking-machines-lab/batch_invariant_ops`), but a non-peer-reviewed
blog (DEPTH-RUBRIC §2: preprint/industry-primary tier). **Up-rated** toward High on this specific
claim by an independent, consistent corroborating source (Willison) and a related arXiv paper
(LLM-42, arXiv:2601.17768) reaching the same conclusion that inference nondeterminism is a
solvable systems property, not irreducible.

## Key claims (exact numbers + verbatim core claim)

1. **Core claim (verbatim):** "The primary reason nearly all LLM inference endpoints are
   nondeterministic is that the load (and thus batch-size) nondeterministically varies!"

2. **It is NOT just "concurrency + floating point."** Floating-point non-associativity exists, but
   the operative cause is **lack of batch invariance**: inference kernels (RMSNorm, matmul,
   attention) produce numerically different results depending on batch size, which varies with
   server load. Tiny FP differences propagate and flip the argmax in greedy decoding.

3. **Experiment (exact).** `Qwen/Qwen3-235B-A22B-Instruct-2507`, 1000 identical completions at
   temperature 0 (greedy sampling):
   - **Without** batch-invariant kernels: **80 unique completions**; most frequent occurred 78
     times; divergence first appears at **token 103** (992 completions wrote "Queens, New York";
     8 wrote "New York City").
   - **With** batch-invariant kernels: **all 1000 completions identical.**
   (A separately reported smaller-model figure: Qwen3-8B in vLLM, 1000 identical prompts -> dozens
   of unique outputs under dynamic batching; nondeterminism vanishes at fixed batch size 1.)

4. **Fix.** Implement batch-invariant RMSNorm, matmul, and attention kernels (fixed reduction
   strategy — canonical tree order, proper padding masks) so results are identical regardless of
   batch size/padding/position. Open implementation provided.

5. **Cost.** Unoptimized deterministic vLLM ~2x slowdown (26s -> 55s); improved attention kernels
   reduce to ~1.6x (42s).

## Reproducibility note
Re-fetch the blog and verify: the verbatim "load (and thus batch-size)..." claim, "80 unique
completions", "token 103", "Queens, New York"/"New York City" (992/8), and the ~2x->1.6x cost.
The numbers above are quoted from the source and an independent summary (Willison), both fetched
2026-06-15. The conclusion (inference nondeterminism is a controllable systems property) is
corroborated by arXiv:2601.17768.
