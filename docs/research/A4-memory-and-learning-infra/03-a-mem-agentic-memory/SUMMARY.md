# SUMMARY — A-MEM: Agentic Memory for LLM Agents

## Full citation
- **Title:** A-MEM: Agentic Memory for LLM Agents
- **Authors:** Wujiang Xu, Zujie Liang, Kai Mei, Hang Gao, Juntao Tan, Yongfeng Zhang (Rutgers University; AIOS Foundation)
- **Year:** 2025
- **Venue:** Advances in Neural Information Processing Systems (NeurIPS 2025); arXiv preprint
- **arXiv ID / URL:** arXiv:2502.12110 — https://arxiv.org/abs/2502.12110 ; HTML: https://arxiv.org/html/2502.12110v1 ; OpenReview: https://openreview.net/forum?id=FiM0M8gcct ; code: https://github.com/agiresearch/A-mem

## Questions informed
- **L1.A4.1** Agent-memory taxonomy (structured/hierarchical memory organization).
- **L1.A4.2** RAG & retrieval foundations (embedding retrieval over a memory store).
- **L1.A4.3** Learning-over-time (memory evolution / link updating).

## Key claims (faithful) — formulae reproduced exactly
Inspired by the **Zettelkasten** method (atomic, interlinked notes).

1. **Memory note construction.** Each memory note:
   `m_i = {c_i, t_i, K_i, G_i, X_i, e_i, L_i}`
   where c_i = interaction content, t_i = timestamp, K_i = LLM-generated keywords, G_i = tags,
   X_i = contextual description, e_i = dense embedding, L_i = linked memories.
2. **Embedding.** `e_i = f_enc[concat(c_i, K_i, G_i, X_i)]` (text encoder over concatenated textual components).
3. **Link generation (cosine similarity)** to find top-k nearest neighbors:
   `s_{n,j} = (e_n . e_j) / (||e_n|| ||e_j||)` ; the LLM then judges which candidates are meaningful links.
4. **Memory evolution.** When new memory m_n is added, each affected historical neighbor m_j is updated:
   `m_j* <- LLM(m_n || M_near^n \ m_j || m_j || P_s3)` where M_near^n = nearest neighbors of m_n, P_s3 = prompt.
5. **Retrieval.** Query encoded identically `e_q = f_enc(q)`, then top-k retrieval by cosine similarity over stored e_i.

## Empirical results (exact)
- **Dataset:** LoCoMo (7,512 QA pairs across 5 categories).
- **Six LLMs:** GPT-4o-mini, GPT-4o, Qwen2.5 (1.5B / 3B), Llama 3.2 (1B / 3B).
- **F1 (GPT-4o-mini backbone), A-Mem vs LoCoMo baseline:** single-hop 27.02 vs 25.02; multi-hop 45.85 vs 18.41 (~2.5x); temporal 12.14 vs 12.04; open-domain 44.65 vs 40.36; adversarial 50.03 vs 69.23 (baseline higher on adversarial).
- **Context efficiency:** A-Mem uses ~1,200-2,500 tokens vs ~16,900 for full-history baselines.

## GRADE tier
- **High** (NeurIPS 2025, peer-reviewed) for the architecture; **Moderate** for specific F1 numbers
  pending independent replication. Down-rate note: the adversarial category shows the baseline
  outperforming A-Mem — recorded honestly, not omitted.

## Reproducibility note
Formulae transcribed from the HTML v1 (Methods). Numbers from the results tables; open-source code at the GitHub URL permits replication on LoCoMo.
