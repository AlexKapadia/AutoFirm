# SUMMARY — AgentPoison: Red-teaming LLM Agents via Poisoning Memory or Knowledge Bases

## Full citation
- **Title:** AgentPoison: Red-teaming LLM Agents via Poisoning Memory or Knowledge Bases
- **Authors:** Zhaorun Chen, Zhen Xiang, Chaowei Xiao, Dawn Song, Bo Li
- **Year:** 2024
- **Venue:** Advances in Neural Information Processing Systems (NeurIPS 2024), peer-reviewed
- **arXiv ID / URL:** arXiv:2407.12784 — https://arxiv.org/abs/2407.12784 ; NeurIPS PDF: https://proceedings.neurips.cc/paper_files/paper/2024/file/eb113910e9c3f6242541c1652e30dfd6-Paper-Conference.pdf ; code: https://github.com/AI-secure/AgentPoison

## Questions informed
- **L1.A4.4** Memory security (primary attack evidence: memory/RAG poisoning).

## Key claims (faithful)
1. **First backdoor attack on generic and RAG-based LLM agents by poisoning long-term memory or the
   RAG knowledge base.** Requires NO additional model training or fine-tuning of the victim.
2. **Mechanism:** trigger generation framed as a **constrained optimization** that maps triggered
   instances to a unique region of the retriever's embedding space, so a query containing the trigger
   reliably retrieves the malicious poisoned entry; the trigger is optimized for transferability,
   in-context coherence, and stealth.
3. **Result (exact):** "average attack success rate higher than 80% with minimal impact on benign
   performance (less than 1%) with a poison rate less than 0.1%."
4. **Targets:** three real-world agent types — RAG-based autonomous-driving agent, knowledge-intensive
   QA agent, and a healthcare EHRAgent.

## GRADE tier
- **High.** Peer-reviewed NeurIPS 2024; primary attack paper with quantified, reproducible results
  and open code. This is a safety/correctness-critical source for A4.4 (>=3 independent sources met
  with folders 12 and 14).

## Reproducibility note
The >80% ASR / <1% benign-degradation / <0.1% poison-rate figures are the paper's headline metrics;
open-source code enables replication on the three agent types.
