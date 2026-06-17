# Zep / Graphiti — A Bi-Temporal Knowledge Graph for Agent Memory

> Workstream 2 (Shared-Knowledge / Coordination Substrate) research library — source 1 of 6.
> Method-space cell: **temporal knowledge graphs for agent memory; as-of-time query semantics.**

---

## 1. Full citation

- **Paper.** Rasmussen, P., Paliychuk, P., Beauvais, T., Ryan, J., & Chalef, D. (2025).
  *Zep: A Temporal Knowledge Graph Architecture for Agent Memory.* arXiv:2501.13956 (submitted 20 Jan 2025).
  <https://arxiv.org/abs/2501.13956>
- **Open-source engine.** `getzep/graphiti` — the temporally-aware knowledge-graph engine underneath Zep
  (PyPI: `graphiti-core`). <https://github.com/getzep/graphiti>
- *Affiliation note (flagged, unverified in-paper):* the author list is the Zep AI / getzep team; the paper body does not print an institutional affiliation.

---

## 2. Faithful structured summary

### What it is
Zep is a memory-layer service for LLM agents. Its engine, **Graphiti**, ingests both unstructured
conversational data and structured business data into a **single evolving temporal knowledge graph**,
extracting entities/relations via an LLM and **maintaining historical relationships rather than
overwriting them**. Retrieval fuses semantic + keyword + graph traversal.

### The bi-temporal model (the load-bearing idea for W2 "as-of-time")
Graphiti tracks **two independent timelines** on every edge:

| Timeline | Field names (paper notation) | Field names (Graphiti code/docs) | Meaning |
| --- | --- | --- | --- |
| **T — event / valid timeline** | `t_valid`, `t_invalid` ∈ T | `valid_at`, `invalid_at` | the period the fact actually held **in the real world** |
| **T′ — transaction / ingestion timeline** | `t'_created`, `t'_expired` ∈ T′ | `created_at`, `expired_at` | when **Zep ingested / superseded** the data |

> *Cross-source caveat (flagged):* the `valid_at/invalid_at/created_at/expired_at` names come from the
> **getzep docs/DeepWiki (code-level)**, NOT the paper. The paper uses the `t_*` mathematical notation.
> Both denote the same two-axis model. Attribute precisely.

### Edge invalidation — append-only, never deletion (reproduced faithfully)
An LLM compares each new edge against semantically related existing edges. On a **temporally-overlapping
contradiction**:

> *"the system invalidates the affected edges by setting their `t_invalid` to the `t_valid` of the
> invalidating edge."*

Edges are **never deleted** — they are closed out, preserving full history. This is what enables the
**as-of-time / point-in-time query**: because both timelines are retained, the graph can answer
*"what did the system know at time T"* — querying facts as they were **valid** at a past event time
and/or as they were **known** at a past transaction time.

### Three hierarchical subgraph tiers (verbatim labels)
- **Episode subgraph 𝒢ₑ** — raw input (messages, text, JSON); a *"non-lossy data store from which
  semantic entities and relations are extracted."*
- **Semantic Entity subgraph 𝒢ₛ** — extracted entities + relationships built on 𝒢ₑ. Episodic edges link
  episodes to entity nodes; bidirectional indices let you trace a fact **back to its source episode (citation)**
  and forward from an episode to its facts.
- **Community subgraph 𝒢_c** — *"clusters of strongly connected entities"* with high-level summaries,
  built by community detection.

### Reported benchmark numbers (attribute to arXiv:2501.13956)
- **Deep Memory Retrieval (DMR):** **Zep 94.8%** vs **MemGPT 93.4%** (Zep condition: gpt-4-turbo).
- **LongMemEval (LME) vs full-context baseline:**
  - gpt-4o-mini: **+15.2%** accuracy, **~90%** response-latency reduction.
  - gpt-4o: **+18.5%** accuracy, **~90%** latency reduction.

### Limitations / ops complexity
- Ingestion is **LLM-heavy** (entity/relation extraction + per-edge contradiction detection) → non-trivial
  write-path cost and latency; invalidation correctness depends on **LLM judgement**.
- Requires a **graph DB backend** (Neo4j / FalkorDB) — a standing operational service.
- Community summaries add maintenance cost.
- Known open issue (getzep/graphiti #1489) flags **temporal-correctness gaps on out-of-order /
  historical backfill** ingestion.

---

## 3. Best parts to take — mapped to the W2 design

| Take this | Into this W2 component |
| --- | --- |
| **The bi-temporal model** (event-time `valid_at/invalid_at` + transaction-time `created_at/expired_at`). | The **typed shared-context block** carries both axes. This is the canonical answer to *"what did the org know at time T"* — a first-class requirement in the golden set. |
| **Edge/fact invalidation by setting `invalid_at`, never deleting.** | The **knowledge-graph backend Protocol** exposes `invalidate(fact, at_time)` not `delete`. Maps cleanly onto AutoFirm's **existing append-only `evolve`/supersession-chain pattern** in `agent_memory_layer.py` — W2 *extends* that pattern to facts/edges, it does not replace it. |
| **Bidirectional episode↔fact indices (every fact traces to its source episode).** | Provenance/citation on every shared fact — feeds the append-only audit requirement (§5.6) and "explain every decision" (§3.11). The assembler can cite *why* a fact is in context. |
| **As-of-time query semantics.** | The `cross_model_context_assembler` accepts an optional `as_of` parameter; default = now. The in-memory fake backend must implement point-in-time correctly so tests run with no graph DB. |
| **Three-tier subgraph (episode / semantic / community).** | Informs the layering: raw comms episodes → extracted shared facts → (optional) role/capability communities. Start with episode + semantic; community is a later tier. |

### RED flags carried forward
- **Graph-DB operational dependency** (Neo4j/FalkorDB) threatens the "never hits blockers / unattended
  operation" goal. **Mitigation:** the backend is a **Protocol with an in-memory fake** (mirrors the
  comms-bus pattern); a real graph DB is opt-in, never required for the core to run.
- **LLM-driven invalidation** is non-deterministic — must be fenced off from the deterministic core, with
  determinism tests over repeats (mirrors AutoFirm's deterministic-core / optional-ML-layer split, §3.5).
