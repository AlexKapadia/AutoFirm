# Microsoft GraphRAG — Entity/Community Graph Construction over a Corpus

> Workstream 2 research library — source 3 of 6.
> Method-space cell: **entity/community graph construction over a corpus; local vs global retrieval.**

---

## 1. Full citation

Edge, D., Trinh, H., Cheng, N., Bradley, J., Chao, A., Mody, A., Truitt, S., Metropolitansky, D., Ness, R. O.,
& Larson, J. (2024). *From Local to Global: A Graph RAG Approach to Query-Focused Summarization.*
arXiv:2404.16130. Microsoft Research. <https://arxiv.org/abs/2404.16130>
Companion: `microsoft/graphrag` repo + docs.

Leiden algorithm cited within: Traag, V. A., Waltman, L., & van Eck, N. J. (2019).
*From Louvain to Leiden: guaranteeing well-connected communities.* arXiv:1810.08473.

---

## 2. Faithful structured summary

### Two-phase design
- **Index time (expensive, LLM-driven):** build an entity knowledge graph from source text, detect a
  **hierarchy of communities** over it, and **pre-generate a summary for every community at every level**.
- **Query time:** answer *global* (corpus-wide, "sensemaking") questions by a **map-reduce over community
  summaries**. Targets query-focused summarization where naive vector RAG fails because no single retrieved
  chunk contains a corpus-wide answer.

### Indexing pipeline — reproduced as named (paper §3.1.1–3.1.6)
- **3.1.1 Source Documents → Text Chunks.** *Chunk-size tradeoff (confirmed):* GPT-4 extracted **~2× as many
  entity references at 600-token chunks vs 2400-token chunks** in a single pass — smaller chunks = higher
  recall but more LLM calls/cost. *(The specific integer pair sometimes quoted is **UNVERIFIED** against the
  paper text; only the ~2× relationship is confirmed.)*
- **3.1.2 Text Chunks → Element Instances.** A multipart LLM prompt extracts **entities** (name, type,
  description) and **relationships** (source, target, description) per chunk. **Gleanings:** missed entities
  are recovered by feeding results back and asking the LLM to "glean" any it missed, over **multiple rounds**,
  using a **logit bias of 100** to force a yes/no "did we miss any?" decision. *(Default round count is
  config-driven `max_gleanings` — exact default UNVERIFIED.)*
- **3.1.3 Element Instances → Element Summaries.** Duplicate instances of the same entity/relationship across
  chunks are summarized into a **single element-level description** (the graph node/edge text).
- **3.1.4 Element Summaries → Graph Communities.** The weighted undirected graph is partitioned by the
  **Leiden algorithm** (Traag et al. 2019), chosen for efficient recovery of **hierarchical** community
  structure on large graphs (guarantees connected communities, unlike Louvain). Produces nested levels
  (evaluation uses **C0 → C3**, root → leaf).
- **3.1.5 Graph Communities → Community Summaries.** A report-like summary is generated for **every community
  at every level**, **precomputed at index time** and reusable across queries.
- **3.1.6 Community Summaries → Global Answer (Map-Reduce).** For a chosen level: (a) **shuffle** community
  summaries and **pack into context windows** (paper uses an **8k-token** window); (b) **MAP** — generate a
  partial answer per window, each with a **helpfulness score 0–100**; (c) **REDUCE** — drop score-0 answers,
  sort by score descending, pack into a final window, generate the single **global answer**.

### LOCAL vs GLOBAL search (confirmed distinction)
- **GLOBAL search** = the §3.1.6 map-reduce over **community summaries** — corpus-wide / thematic questions.
- **LOCAL search** = **entity-anchored** retrieval: map the query to specific entities, then pull their
  neighborhood (connected entities, relationships, element + covariate descriptions, relevant raw chunks)
  into context — questions about specific entities. *(LOCAL mechanics live in the `microsoft/graphrag` docs;
  the QFS paper centers on GLOBAL.)*

### Limitations / ops complexity
- Indexing is a **full LLM-driven pass over all source text** (extraction + gleanings + per-community,
  per-level summarization) — explicitly **token-expensive** and the dominant cost. Built for **global
  sensemaking**, not point lookups; community summaries are amortized once across many queries.

---

## 3. Best parts to take — mapped to the W2 design

| Take this | Into this W2 component |
| --- | --- |
| **Explicit entity+relationship extraction with typed (name, type, description) nodes/edges.** | Defines the shape the knowledge-graph backend Protocol stores and the in-memory fake returns. |
| **LOCAL (entity-anchored) search.** | This — not GLOBAL — is the workhorse for W2 coordination/multi-hop queries (*"which role owns the capability that produced artifact Z?"*): anchor on the entity (artifact Z), traverse the neighborhood. The assembler emits the **minimal** anchored neighborhood, not the whole graph. |
| **GLOBAL community summaries (Leiden) as an OPTIONAL higher tier.** | Maps to Zep's community subgraph (folder 01). Defer to a later tier — useful for org-wide "what is the company state" sensemaking, but **its index-time LLM cost is a RED flag for unattended ops**. |
| **Map → score → reduce assembly with explicit helpfulness scores.** | Pattern for the `cross_model_context_assembler`: rank candidate facts, keep only the highest-scoring, drop the rest — *minimal* assembled context, scored and ordered (reinforced by Lost-in-the-Middle, folder 05). |

### RED flags carried forward
- **Index-time LLM cost** (full corpus pass + per-community summaries) is the single biggest ops-complexity
  risk for "never hits blockers." For W2, **prefer LOCAL/entity-anchored retrieval as the default**; treat
  community-summary GLOBAL indexing as opt-in, off the unattended critical path.
- Leiden + community summaries do **not generalise to low-latency point retrieval** — wrong tool for the
  cross-provider write-then-read coordination tasks that are W2's core.
