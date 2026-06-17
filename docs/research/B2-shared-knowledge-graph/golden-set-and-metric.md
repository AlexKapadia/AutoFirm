# W2 Shared-Knowledge Substrate — Golden Set & Metric (DRAFT)

> Defines the pre-agreed evaluation up front (per §3.4 / §4.5), so the temporal-graph vs vector+graph
> bake-off is decided by **evidence, not taste**. This is a draft for CRO/CTO ratification before any build.

W2 EXTENDS, does not replace, the existing pluggable memory layer (`src/autofirm/memory/agent_memory_layer.py`
— versioned, principal-scoped, injected `SemanticEmbeddingBackend` Protocol) and the inter-agent comms bus
(`src/autofirm/comms/` — FIPA envelope, fail-closed routing, append-only audit). The golden set therefore
treats those as fixtures: facts arrive over the bus, are written through the memory/store layer, and are read
back by a *different-provider* agent.

---

## 1. What "ground truth" means here

A **synthetic-only** corpus (per §3.12 — no real PII/client data in tests) of org-state facts with:
- a known **entity/edge graph** (roles, capabilities, artifacts, owners) — the retrieval ground truth;
- a known **bi-temporal timeline** (`valid_at`/`invalid_at`, `created_at`/`expired_at`) — the as-of-time
  ground truth (model from the Zep bi-temporal model, folder 01);
- known **correct answers** for each coordination/multi-hop/as-of query.

The corpus is **parameterised and generated** (not hand-fixtured) so we test the **general** problem and never
overfit (§3.9). Cross-provider tests run the *same* corpus through agents on **≥2 distinct providers**.

---

## 2. Golden task families

| # | Family | Example | Tests |
| --- | --- | --- | --- |
| **T1** | **Cross-model write→read** | Model A (provider X) writes fact `F`; model B (provider Y) must retrieve `F` and act correctly. | cross-provider fidelity; the core W2 interop guarantee (Letta shared-block, folder 04). |
| **T2** | **Multi-hop coordination** | *"Which role owns the capability that produced artifact Z?"* (artifact → capability → role → owner). | multi-hop recall; the discriminating signal between vector and graph backends (Mem0 multi-hop 51.15, folder 02). |
| **T3** | **As-of-time correctness** | *"What did the org know about the pricing model at time T?"* (a fact valid then, later invalidated). | bi-temporal point-in-time query (folder 01). Must return the state **as known/valid at T**, not now. |
| **T4** | **Invalidation/supersession** | A fact is superseded; later reads must not surface the stale version (but audit/history must still hold it). | append-only correctness vs AutoFirm's existing `evolve` chain. |
| **T5** | **Minimality / position adversarial** | Inject many distractor facts; assert the assembler emits a **minimal, ranked** block with load-bearing facts at head/tail. | Lost-in-the-Middle / RULER (folder 05): minimal beats raw dump. |
| **T6** | **Determinism** | Same query, same `as_of`, repeated N times across processes. | byte-identical assembled context on deterministic paths (§3.11). |

---

## 3. Metrics (with error bars — peer-reviewed presentation per §3.10)

| Metric | Definition | Bar |
| --- | --- | --- |
| **Retrieval precision/recall@k** | vs the known graph ground truth, per task family, mean ± 95% CI. | high recall on T1–T4; report precision to show minimality (T5). |
| **Temporal-correctness** | fraction of T3/T4 queries returning the correct as-of state (not now-state, not stale). | must be **1.0** on deterministic as-of paths (zero numerical/logic errors, §3.11). |
| **Cross-provider fidelity** | agreement rate of B's action on T1 across provider pairs; A-writes-B-reads success rate. | report per provider pair; flag any pair < others. |
| **p95 retrieval latency** | end-to-end retrieve+assemble, p95 over the suite (mirror Mem0 Table 2 presentation). | report vs a raw-dump baseline; both must beat full-context. |
| **Assembled-context size** | tokens emitted by the assembler vs the full store / full-dump baseline. | demonstrate large reduction (cf. Mem0 >90% token saving) **without** recall loss. |
| **Determinism** | byte-identical assembled output over N repeats / processes. | **1.0** on deterministic paths. |

LLM-driven extraction/consolidation paths (non-deterministic) are measured separately and **fenced from the
deterministic retrieval/assembly core** (deterministic-core / optional-ML-layer split, §3.5).

---

## 4. Bake-off recommendation

**Bake off two backends on separate `experiment/` branches, same corpus, same metrics:**

- **Candidate A — Temporal graph** (Zep/Graphiti-style bi-temporal KG; folder 01). Native `valid_at/invalid_at`
  + `created_at/expired_at` and append-only invalidation make **T3/T4 as-of-time correctness first-class**.
- **Candidate B — Vector + graph hybrid** (Mem0-style; folder 02). Vector recall for T1, optional graph layer
  (G=(V,E,L)) for T2 multi-hop.

### Decision criterion (pre-agreed)

1. **Temporal-correctness (T3/T4) is a hard gate.** If a candidate cannot hit **1.0** on deterministic as-of
   paths, it loses outright — bi-temporal correctness is non-negotiable for *"what did the org know at T."*
2. Among survivors, **multi-hop recall (T2)** and **cross-provider fidelity (T1)** decide on the numbers
   (mean ± CI), with **p95 latency** and **assembled-context size** as tie-influencers.
3. **If they tie on accuracy, the SIMPLER one wins** (§ unattended-operation bias). The decisive question is
   **ops complexity**: does the backend require a standing graph-DB service (Neo4j/FalkorDB) that threatens
   "never hits blockers"?

### Recommended favourite (to be confirmed by the bake-off, not assumed)

**Lean toward a single bi-temporal graph store with an in-memory fake (Candidate A), accessed primarily via
LOCAL/entity-anchored retrieval (GraphRAG folder 03), with vectors as an optional ranking signal inside it —
NOT two separate stores.** Rationale:
- T3/T4 as-of-time correctness is a stated W2 requirement and is **native** to the bi-temporal model but
  **bolted-on** for a vector-first design.
- One store (Protocol + in-memory fake) is **operationally simpler** than vector-store + graph-store + sync
  glue — and simplicity wins ties for unattended operation.
- It maps cleanly onto AutoFirm's **existing append-only/versioned** memory pattern, so W2 extends rather than
  forks the architecture.

The bake-off exists to falsify this: if Candidate B reaches **1.0** temporal-correctness AND wins meaningfully
on T2/T1/latency, it takes `main` and A is deleted (no graveyard, §3.8).

---

## 5. What would make each WIN

- **Temporal graph (A) wins if:** it hits temporal-correctness 1.0 (expected), holds T2 multi-hop recall, and
  its single-store ops footprint stays inside the in-memory fake for the core (real graph DB optional). This
  is the simpler unattended story.
- **Vector+graph (B) wins if:** it matches A on temporal-correctness AND beats it materially on T2 multi-hop
  recall or p95 latency at scale — i.e. the relational gains (Mem0ᵍ ≈ +2% overall, larger on multi-hop)
  justify the second store and its sync complexity with hard numbers.
