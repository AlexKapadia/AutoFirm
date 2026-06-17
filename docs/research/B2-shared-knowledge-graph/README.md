# B2 — Shared-Knowledge / Coordination Substrate (Workstream 2) — Research Library

Deep, primary-sourced research for a **shared-knowledge / coordination substrate** that lets **heterogeneous
agents (different model providers) share context reliably**. W2 **extends** the existing pluggable memory layer
(`src/autofirm/memory/agent_memory_layer.py`) and inter-agent comms bus (`src/autofirm/comms/`) — it does not
replace them. Institution-grade bar; research gates building (§2 CRO, §3.3, §4.6).

## Sources (one folder per source)

| # | Folder | One-line takeaway |
| --- | --- | --- |
| 01 | `01-zep-graphiti-bitemporal-knowledge-graph` | Bi-temporal KG (event-time + transaction-time, append-only invalidation) gives native **"what did the org know at time T."** |
| 02 | `02-mem0-vector-and-graph-memory` | Vector memory is simplest/fastest; the graph variant buys ~+2% overall and much more on **multi-hop**, at higher ops cost. |
| 03 | `03-microsoft-graphrag-community-graph` | LLM entity/relationship extraction + Leiden communities; **LOCAL (entity-anchored) search** is the workhorse, GLOBAL indexing is expensive. |
| 04 | `04-letta-memgpt-shared-memory-blocks` | A labeled, bounded, **model-agnostic memory block** shared across agents is the cross-provider interop primitive — but "last write wins." |
| 05 | `05-context-minimisation-lost-in-the-middle-and-ruler` | More context is NOT better: U-shaped position effect + effective ≪ advertised length → **minimal, ranked, well-placed context wins.** |
| 06 | `06-obsidian-readonly-projection-over-authoritative-store` | Markdown + `[[wikilinks]]` = a free human backlink graph; keep it a **read-only, regenerable projection** of the authoritative store. |

## Bake-off & metric
- `golden-set-and-metric.md` — cross-model write→read, multi-hop, as-of-time, minimality, determinism tasks;
  metrics (precision/recall@k, temporal-correctness, cross-provider fidelity, p95 latency, determinism); and
  the temporal-graph vs vector+graph bake-off with its pre-agreed decision criterion.

## Top design implications
1. **Shared-context block = model-agnostic typed `{label, description, value, limit}` (Letta).** The assembler
   emits a **minimal** block (Lost-in-the-Middle/RULER), graph store is source of truth (CQRS), block is the
   read-only in-context projection.
2. **Bi-temporal, append-only store (Zep) extends AutoFirm's existing `evolve`/supersession pattern** — gives
   as-of-time correctness for free and keeps one architecture.
3. **LOCAL/entity-anchored retrieval (GraphRAG), not GLOBAL community indexing**, is the low-ops default for
   cross-provider coordination/multi-hop queries.
