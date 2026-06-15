# SUMMARY — MemGPT: Towards LLMs as Operating Systems

## Full citation
- **Title:** MemGPT: Towards LLMs as Operating Systems (later: Letta)
- **Authors:** Charles Packer, Sarah Wooders, Kevin Lin, Vivian Fang, Shishir G. Patil, Ion Stoica, Joseph E. Gonzalez (UC Berkeley)
- **Year:** 2023
- **Venue:** arXiv preprint (widely cited; basis of the Letta/MemGPT system)
- **arXiv ID / URL:** arXiv:2310.08560 — https://arxiv.org/abs/2310.08560

## Questions informed
- **L1.A4.1** Agent-memory taxonomy (tiered memory: main context vs external).
- **L1.A4.2** Context-window limits (virtual context management as the mitigation).

## Key claims (faithful)
1. **Virtual context management**, by analogy to OS hierarchical memory (RAM vs disk): the LLM is
   given the *appearance* of large memory by **paging information between a limited "main context"
   (the LLM context window) and "external context" (out-of-context storage)**.
2. **Self-directed memory management:** the LLM itself issues **function calls** to read/write its
   memory tiers and to manage control flow via **interrupts** (e.g., yield to user, retrieve more).
3. **Memory tiers:** main context = system instructions + working context + FIFO message queue;
   external context = recall storage (full message history) + archival storage (general read/write DB).
4. **Evaluated** on (a) document analysis exceeding the base LLM's context window and (b) multi-session
   chat where the agent remembers, reflects, and evolves across long interactions — outperforming
   fixed-context baselines on consistency and recall over long conversations.

## GRADE tier
- **Moderate.** Influential arXiv preprint with an open implementation (Letta); architecture claims
  well-supported, specific benchmark numbers treated as Moderate pending peer review.

## Reproducibility note
The OS-analogy tiering and self-editing function-call interface are described in the System section;
open-source implementation enables replication.
