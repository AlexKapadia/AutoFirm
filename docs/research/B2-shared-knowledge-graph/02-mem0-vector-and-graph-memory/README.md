# Mem0 — Scalable Long-Term Agent Memory (vector vs graph variant)

> Workstream 2 research library — source 2 of 6.
> Method-space cell: **vector + graph hybrid memory; recall vs latency vs ops-complexity tradeoff.**

---

## 1. Full citation

Chhikara, P., Khant, D., Aryan, S., Singh, T., & Yadav, D. (2025).
*Mem0: Building Production-Ready AI Agents with Scalable Long-Term Memory.* arXiv:2504.19413 (submitted 28 Apr 2025).
<https://arxiv.org/abs/2504.19413>
Team: Mem0 (mem0ai). *(Affiliation not printed in paper body — flagged unverified.)*

---

## 2. Faithful structured summary

### What it is
A memory-centric architecture that **dynamically extracts, consolidates, and retrieves** salient facts from
ongoing multi-session dialogue, instead of stuffing full history into the context window. Two variants:
- **Mem0** — vector / dense memory.
- **Mem0ᵍ** — graph-based memory capturing relational structure.

### Two-phase pipeline (faithful)
1. **Extraction phase** — processes a message pair `(m_{t−1}, m_t)` plus a conversation summary and recent
   messages; an LLM `φ(P)` extracts salient candidate memories `Ω`.
2. **Update phase** — compares each extracted memory against semantically similar existing ones and applies
   an operation via a **Tool Call** mechanism.

### The LLM-selected operation set (four — reproduced verbatim)
- **ADD** — *"creation of new memories when no semantically equivalent memory exists."*
- **UPDATE** — *"augmentation of existing memories with complementary information."*
- **DELETE** — *"removal of memories contradicted by new information."*
- **NOOP** — *"when the candidate fact requires no modification to the knowledge base."*

### Mem0ᵍ graph data model (reproduced)
Directed labeled graph **G = (V, E, L)**:
- **V** = entities (e.g. `Alice`, `San_Francisco`)
- **E** = relationships (e.g. `lives_in`)
- **L** = semantic type labels (e.g. `Alice → Person`, `San_Francisco → City`)

Pipeline = entity extraction → relationship generation producing **relationship triplets**.

### Reported LOCOMO results (attribute to arXiv:2504.19413; metric = LLM-as-a-Judge "J" score)
- **Overall J (Table 1):** Mem0 **66.88 ± 0.15%**, Mem0ᵍ **68.44 ± 0.17%**, OpenAI baseline **52.90 ± 0.14%**.
  Headline **+26% relative** (Mem0 over OpenAI); graph variant ≈ **+2%** over base Mem0.
- **Per-category J (Mem0):** single-hop **67.13 ± 0.65**; **multi-hop 51.15 ± 0.31**; open-domain **72.93 ± 0.11**;
  temporal **55.51 ± 0.34**.
- **Latency (Table 2, p95 total):** Mem0 **1.440 s** vs full-context **17.117 s** → **91% lower p95 latency**.
- **Token cost:** **>90% savings** vs full-context (Mem0 ≈ 1,764 tokens vs ≈ 26,031 for full conversation).

### Recall vs latency vs ops-complexity tradeoff (the key W2 lesson)
- **Vector Mem0:** simplest ops (vector store only), **lowest latency**, strong overall accuracy; **weakest on
  relational / multi-hop** (51.15).
- **Graph Mem0ᵍ:** ~2 pts higher overall and **better on relational/temporal** reasoning, but adds a graph
  store + extra extraction (entity + relation triplets) → higher write-path cost and operational complexity.
- Both vastly cheaper than full-context. Paper frames it as *"a compelling balance between advanced reasoning
  capabilities and practical deployment constraints."*

---

## 3. Best parts to take — mapped to the W2 design

| Take this | Into this W2 component |
| --- | --- |
| **The ADD / UPDATE / DELETE / NOOP consolidation operation set.** | Maps onto the knowledge-graph backend Protocol's write API. Note: AutoFirm's append-only invariant means **DELETE → invalidate** (set `invalid_at`), never physical delete (see Zep folder 01). |
| **The vector-vs-graph numeric tradeoff (graph buys ~+2% overall, big on multi-hop, at higher ops cost).** | Direct input to the **bake-off decision** (see `golden-set-and-metric.md`): graph only earns its place on **evidence** — specifically the multi-hop / "which role owns capability that produced artifact Z" tasks. |
| **p95 latency + token-cost numbers as the latency/cost baseline.** | The W2 evidence showcase should report p95 retrieval latency and assembled-context token count against a full-dump baseline, exactly as Mem0 does. |
| **Mem0ᵍ G=(V,E,L) typed-edge model.** | The in-memory fake graph backend uses the same shape (typed nodes, typed labeled edges), so swapping in a real graph store is contract-preserving. |

### RED flags carried forward
- **Multi-hop is the weak spot of the vector variant (51.15).** If W2's coordination tasks are multi-hop-heavy,
  the simpler vector backend may **not generalise** — this is the discriminating signal for the bake-off.
- LLM-driven consolidation is **non-deterministic**; fence it from the deterministic retrieval/assembly core.
