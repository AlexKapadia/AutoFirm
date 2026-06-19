# W2 Shared-Knowledge Substrate — design decision (build the winner directly)

> Records WHY the W2 shared-knowledge / coordination layer was built directly as the
> research-settled winner instead of via a throwaway `experiment/` bake-off branch,
> citing `docs/research/B2-shared-knowledge-graph/`. Companion to the golden-set &
> metric draft (`docs/research/B2-shared-knowledge-graph/golden-set-and-metric.md`).

## Decision

Build **Candidate A — a single bi-temporal graph store + LOCAL/entity-anchored
retrieval**, behind a `Protocol` seam with a deterministic in-memory fake mandatory,
and a Letta-style model-agnostic shared-context block as the cross-provider interop
primitive. No second store, no standing graph-DB service in the core.

## Why directly, not a live bake-off

The B2 golden-set doc (§4) pre-agreed the decision criterion: **temporal-correctness
(T3/T4) is a hard gate** that a candidate must hit at **1.0** or lose outright, and
among survivors the **simpler** design wins ties (ops complexity, unattended
operation). The research library already establishes the outcome with primary
sources, so a parallel `experiment/` branch would only re-derive a settled result:

- **Bi-temporal correctness is native to Candidate A, bolted-on for Candidate B**
  (Zep/Graphiti, folder 01): event-time `valid_at`/`invalid_at` + transaction-time
  `recorded_at`/`superseded_at` with append-only invalidation give "what did the org
  know at T" for free. A vector-first design (Candidate B, Mem0, folder 02) must add
  a temporal layer on the side — strictly more moving parts for the SAME ceiling
  (temporal-correctness caps at 1.0; B cannot beat A there, only match it).
- **One store is operationally simpler than vector-store + graph-store + sync glue**
  (golden-set §4 decision rule 3). Candidate B's gains (Mem0ᵍ ≈ +2% overall, larger
  on multi-hop) do not clear the bar of a second standing service for an unattended
  platform.
- **LOCAL/entity-anchored retrieval is the low-ops workhorse** (GraphRAG, folder 03);
  GLOBAL community indexing is expensive and unnecessary for cross-provider
  coordination/multi-hop queries.
- **The minimal-context assembler is mandated regardless of backend** (Lost-in-the-
  Middle / RULER, folder 05): more context is not better, so the assembler emits a
  minimal ranked block, never a raw dump — orthogonal to the store choice.

The falsification condition still stands (golden-set §5): if a future measurement
shows a vector+graph hybrid reaching 1.0 temporal-correctness AND beating A
materially on multi-hop/latency at scale, it takes `main` and A is deleted (no
graveyard, CLAUDE.md §3.8). The retrieval precision/recall@k efficacy test
(`tests/knowledge/test_cross_model_context_assembler__retrieval_precision_recall.py`)
is the in-repo measurement harness for that comparison.

## The poisoning defence (B6, the single most dangerous attack)

Shared-knowledge poisoning — one poisoned entry fanning out to many agents — is
mitigated by attaching **taint/provenance at WRITE-TIME** to the immutable entry
(`SharedKnowledgeEntry.origin` + `KnowledgeProvenance`) and **carrying it WITH the
value across every hop** in the assembler (`ContextItem.origin`/`.provenance`, copied
verbatim, never re-derived). The assembler **never elevates UNTRUSTED to TRUSTED**
and **gates any consequential path** when an untrusted value is present
(CaMeL / dual-LLM trusted-plan / untrusted-data, `docs/research/B6-egress-and-
supplychain-threats/`). The Obsidian projection is **read-only / one-way** so the
human-facing view can never inject back into the authoritative store.

## What landed on `main`

`src/autofirm/knowledge/`:
- `shared_knowledge_contract.py` — frozen model-agnostic block; write-time taint;
  bi-temporal validity with fail-closed ordering validators.
- `knowledge_graph_backend_protocol.py` — `Protocol` + deterministic in-memory
  bi-temporal fake (append-only; logical invalidation; as-of-time reconstruction).
- `cross_model_context_assembler.py` — pure minimal ranked assembler carrying taint
  every hop, no elevation, fail-closed consequential gate.
- `obsidian_vault_export_view.py` — pure read-only markdown + `[[backlink]]`
  projection, no write-back path.
