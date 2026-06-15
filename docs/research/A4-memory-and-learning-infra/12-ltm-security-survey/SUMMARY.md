# SUMMARY — A Survey on Long-Term Memory Security in LLM Agents

## Full citation
- **Title:** A Survey on Long-Term Memory Security in LLM Agents: Attacks, Defenses, and Governance Across the Memory Lifecycle (v1 subtitle: "Toward Mnemonic Sovereignty")
- **Authors:** Zehao Lin, Xixuan Hao, Renyu Fu, Shaobo Cui, Kai Chen, Chunyu Li, Zhiyu Li, Feiyu Xiong
- **Year:** 2026
- **Venue:** arXiv preprint
- **arXiv ID / URL:** arXiv:2604.16548 — https://arxiv.org/abs/2604.16548 ; HTML v2: https://arxiv.org/html/2604.16548v2

## Questions informed
- **L1.A4.4** Memory security & governance over the memory lifecycle (poisoning, deletion-verify).

## Key claims (faithful)
1. **Six-phase memory-lifecycle framework** (exact phase definitions):
   - **Write** — "commits content to long-term memory through explicit user instruction, implicit
     dialogue summarization, environmental observation, or cross-agent memory sharing."
   - **Store** — "indexes, compresses, merges, decays, and evicts written content."
   - **Retrieve** — "brings previously stored memory entries back into context through embedding
     similarity, keyword matching, graph-based retrieval, or hybrid routing."
   - **Execute** — "retrieved memories begin to shape the model's planning, reasoning, and tool-use decisions."
   - **Share & Propagate** — contamination can spread "laterally, from agent to agent via shared
     memory; vertically, from individual users to organizational memory; or temporally."
   - **Forget & Rollback** — "remove contaminated memories, roll back to a known-safe state, trace
     the provenance of poisoned entries."
2. **Five governance primitives (exact):**
   - **Write Authorization (WA)** — every entry "be attributable to an authenticated source and pass an explicit authorization check."
   - **Provenance Visibility (PV)** — every entry "carry a queryable, lineage-complete provenance record tracing back to its originating write event."
   - **Principal-Scoped Retrieval (PS)** — retrieval "return only entries whose authorized scope includes the querying principal."
   - **Rollbackability (RB)** — "maintain versioned snapshots and write logs sufficient to restore memory store to a known-safe state."
   - **Verified Forgetting (VF)** — after deletion, "the system can demonstrate ... that the target content is no longer recoverable."
3. **Attack categories** mapped to phases: memory poisoning (Write), provenance tampering (Store),
   retrieval corruption (Retrieve), control-flow hijacking (Execute), cross-agent propagation
   (Share), incomplete-deletion/rollback failures (Forget).
4. **Key gap finding (exact):** "threats at the write and retrieve phases are well-studied while
   defenses at the store, share, and forget phases remain comparatively sparse." The survey also
   notes no existing published system covers the full memory lifecycle with complete governance.

## GRADE tier
- **Moderate.** arXiv survey (secondary), recent and directly on-topic; its lifecycle + primitives
  framework is corroborated by primary attack work (AgentPoison, folder 13) and unlearning
  verification (folder 14). Used as the organizing framework, not as sole basis for any number.

## Reproducibility note
Phase and primitive definitions quoted verbatim from HTML v2; framework re-derivable at the URL.
(Note: v1 used the "mnemonic sovereignty" subtitle and an earlier primitive count; v2's FIVE
primitives WA/PV/PS/RB/VF are the citation of record here.)
