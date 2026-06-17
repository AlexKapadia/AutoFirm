# LLM-Blender — Pairwise Ranking + Generative Fusion (rank-then-fuse ensemble)

> Research note for AutoFirm capability **B1 (multi-model egress)** / workstream **W1**
> (deterministic selection + optional learned router + ensemble-quorum reconciliation
> behind a self-hosted OpenAI-compatible gateway). Faithful to the source; formulae
> reproduced verbatim with the paper's own notation. Where notation was reconstructed
> from the HTML render it is flagged.

---

## (1) Full citation

- **Title:** LLM-Blender: Ensembling Large Language Models with Pairwise Ranking and Generative Fusion
- **Authors:** Dongfu Jiang, Xiang Ren, Bill Yuchen Lin
- **Year:** 2023
- **Venue:** Proceedings of ACL 2023 (main conference)
- **arXiv:** arXiv:2306.02561 [cs.CL]
- **URL:** https://arxiv.org/abs/2306.02561
- **Code/data:** MixInstruct benchmark released with the paper.

---

## (2) Faithful structured summary

### PROBLEM
> "optimal LLMs for different examples can significantly vary."

No single open-source LLM dominates across all inputs. The goal is an ensemble that
**consistently** extracts the best-performing output per example by leveraging the
complementary strengths of a pool of N base models.

### METHOD
Two stages: **PairRanker** (rank the N candidate outputs) then **GenFuser** (fuse the
top-K into a new, improved output).

**PairRanker — pairwise comparison scoring.**
The input `x` and a *pair* of candidate outputs `y_i`, `y_j` are jointly encoded by a
cross-attention encoder (RoBERTa-style):

> "we jointly encode the input x and the two candidate outputs y_i and y_j as input to a
> cross-attention encoder (e.g., RoBERTa), in the form of **f_φ(x, y_i, y_j)**, to learn
> and determine which candidate is better."

Training objective for a pair (`z_i`, `z_j` indicate which candidate is superior under
quality metric Q; σ is the logistic sigmoid):

```
ℒ_Q = − z_i · log σ( s^(i,j)_i ) − z_j · log σ( s^(i,j)_j )
```

**Pairwise comparison matrix M (built at inference).**
After running all ordered pairs:

> "After N(N−1) iterations, we obtain a matrix **M**, where **M_{ij} = s_{ij}** represents
> the confidence that y_i is better than y_j."

with the pair-specific difference

```
s_{ij} = s^(i,j)_i − s^(i,j)_j
```

**Aggregation matrix → single ranking.** Three aggregators defined; **MaxLogits** is the
default (best performing):

```
MaxLogits:  s_i = Σ ( M_{i*} − M_{*i} )        # default aggregator
MaxWins:    s_i = |{ s_{ij} ∈ M_{i*} | s_{ij} > 0 }| + |{ s_{ji} ∈ M_{*i} | s_{ji} < 0 }|
```

> "MaxLogits yields the best performance, so we use MaxLogits as the default aggregator
> for PairRanker."

The candidate with the highest aggregated `s_i` is ranked first (argmax over `s_i`).

**GenFuser — generative fusion.** The input `x` and the **top-K** PairRanker candidates
are concatenated with separator tokens and fed to a fine-tuned seq2seq (T5-like) fuser:

> "we concatenate the input x and K top-ranked candidates sequentially using separator
> tokens, such as `<extra_id_i>`, and fine-tune a T5-like model to learn to generate y."

So the final answer is a **newly generated** sequence, not a verbatim pick.

### KEY FORMULAE (reproduced exactly — see verbatim quotes above)
1. Pairwise scorer: `f_φ(x, y_i, y_j)` → scores `s^(i,j)_i`, `s^(i,j)_j`.
2. Pairwise loss: `ℒ_Q = − z_i log σ(s^(i,j)_i) − z_j log σ(s^(i,j)_j)`.
3. Matrix entry: `M_{ij} = s_{ij} = s^(i,j)_i − s^(i,j)_j`.
4. Default aggregation (MaxLogits): `s_i = Σ ( M_{i*} − M_{*i} )`.

### RESULTS (headline numbers, cited exactly)
- **Base models:** **N = 11** open-source LLMs ensembled.
- **MixInstruct benchmark:** **100k train / 5k val / 5k test** examples; includes oracle
  pairwise comparisons.
- **LLM-Blender vs. best single model (Open Assistant), headline metrics:**
  | Metric | Open Assistant (best single) | LLM-Blender |
  | --- | --- | --- |
  | BARTScore (↑, less negative better) | −3.45 | **−3.02** |
  | BLEURT (↑) | −0.39 | **−0.17** |
  | GPT-Rank (↓, lower=better avg rank) | 3.90 | **3.01** |
  | In GPT top-3 (%) | 51.98% | **68.59%** |
- PairRanker showed the highest correlation with ChatGPT-based ranking among rankers.

---

## (3) Best-parts-to-take for W1 (ensemble-quorum reconciliation)

**What this is good for in W1:** the **rank-then-fuse** branch of reconciliation — i.e. the
path used when outputs are **free text** (summaries, drafts, analysis) where there is no
exact-match "vote" to take and quality is subtle.

Concrete adoption guidance:

- **When to rank-then-fuse vs. majority-vote.** Use **majority/quorum** (exact-match) for
  *structured/extraction/classification* outputs (a JSON field, a label, a number) — see
  the self-consistency note. Use a **PairRanker-style rank** (and optionally GenFuser-style
  fuse) only for *open-ended free-text* outputs where votes don't apply. The two are
  complementary reconciliation modes selected by **output type**, decided deterministically.
- **Keep the gateway deterministic & auditable even with a learned ranker.** PairRanker is a
  *trained* model, so its scores are an added dependency and a non-deterministic-training
  artifact. Make the *reconciliation policy around it* deterministic: (a) pin the ranker
  checkpoint + version + hash in the audit log; (b) run the scorer at temperature 0 / greedy
  so `f_φ` is reproducible; (c) define an **exact deterministic tie-break** on equal
  aggregated `s_i` (e.g. lowest candidate index = priority order of the model pool) so a tie
  never resolves randomly; (d) log the full matrix `M` and the per-candidate `s_i` so the
  selection is replayable.
- **Prefer "rank-and-pick-top-1" over "fuse" by default.** GenFuser *generates a new
  string*, which (i) adds a second generative dependency, (ii) reintroduces sampling
  non-determinism, and (iii) can hallucinate content absent from all candidates. For an
  auditable gateway, the safer default is **PairRanker → return the top-ranked candidate
  verbatim** (fully traceable to a real model output). Reserve GenFuser-style fusion for
  cases where blending is explicitly wanted and a human-review/eval gate exists.
- **MaxLogits is the formula to implement** for the deterministic aggregation step
  (`s_i = Σ(M_{i*} − M_{*i})`), with the documented exact tie-break — it's a pure function of
  the matrix, so it is itself deterministic once the scores are fixed.
- **Cost implications.** PairRanker is **O(N(N−1))** forward passes of the *ranker* per query
  (all ordered pairs) — quadratic in pool size, though the ranker is far cheaper than the
  base LLMs. GenFuser adds one more generation. So cost = N base generations + ~N² cheap
  ranker passes (+1 fuser pass if fusing). For W1, cap N (e.g. 3–5) and prefer rank-then-pick
  to bound cost.

### RED flags for W1
- **Trained-fuser/ranker dependency.** Both PairRanker and GenFuser are *fine-tuned models*
  — adopting them adds model-training, checkpoint-hosting, and version-pinning burden, and
  they are domain-shifted (trained on MixInstruct). A naive deterministic-vote path has none
  of this.
- **Non-determinism from GenFuser sampling** and from any non-greedy ranker decoding — must
  be pinned to greedy/T=0 or the gateway output is not reproducible.
- **Hallucination risk in fusion:** GenFuser can emit content present in *no* candidate;
  unacceptable for extraction/numeric/regulator-facing paths.
- **Quadratic ranker cost** in N — does not scale to large pools.

### Verification status
All four formulae and the headline table were extracted from the ar5iv HTML render of
arXiv:2306.02561 and quoted verbatim above. The matrix-difference notation `M_{i*} − M_{*i}`
in MaxLogits denotes row-minus-column sums for candidate i; the render uses subscript-star
notation rather than explicit Σ_j — the explicit per-j form is
`s_i = Σ_j (M_{ij} − M_{ji})`. **Confidence: high**, but confirm the exact star/Σ_j
typography against the PDF before hard-coding.
