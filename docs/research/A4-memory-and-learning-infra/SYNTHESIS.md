# SYNTHESIS — A4 Memory & Learning Infrastructure (Layer 1)

Branch A4 owner deliverable. Surveys the full option space for the four L1.A4 sub-questions and
gives a concrete, cited recommendation for AutoFirm. Feeds L2.A4 (design the tiered, provenance-aware,
governed memory & learning infrastructure). Every recommendation traces to a source folder (NN-) here.

---

## L1.A4.1 — Agent-memory taxonomy (surveyed space -> recommendation)

**Option space surveyed:**
- Cognitive taxonomy: working / long-term, long-term split into episodic / semantic / procedural
  (CoALA, 02 — High/TMLR).
- Maturity taxonomy: Storage -> Reflection -> Experience (Storage-to-Experience survey, 01 — ACL 2026 Findings).
- Structural organizations: lightweight-semantic, entity-centric, episodic-reflective,
  structured/hierarchical (01); Zettelkasten linked-note graph (A-Mem, 03 — NeurIPS 2025); memory
  stream (Generative Agents, 04 — UIST 2023); OS-tiered main/external context (MemGPT, 09).

**Recommendation:** a two-axis taxonomy — (axis 1) CoALA four stores
working/episodic/semantic/procedural; (axis 2) maturity tier Storage->Reflection->Experience.
Records stored as linked structured notes (A-Mem) and managed with OS-style tiering/paging (MemGPT).
Corroborated by one peer-reviewed taxonomy (CoALA) + one venue survey (Storage-to-Experience) + two
peer-reviewed instantiations (A-Mem, Generative Agents): meets the >=2-source "important" bar.

## L1.A4.2 — RAG, retrieval foundations & context-window limits

**Option space surveyed:**
- Retrievers: lexical/BM25 baseline; dense dual-encoder dot-product/cosine (DPR, 07 — EMNLP 2020,
  +9-19% top-20 over BM25); recency+relevance+importance heuristic (Generative Agents, 04);
  graph/hybrid routing (RAG survey, 06).
- RAG paradigms: Naive -> Advanced (re-rank, query-rewrite) -> Modular (RAG survey, 06); seminal
  parametric+non-parametric RAG with index-swap updates (Lewis, 05 — NeurIPS 2020).
- Context limits: lost-in-the-middle U-shaped degradation even in long-context models (08 — TACL);
  virtual context management / paging (MemGPT, 09).

**Recommendation:** External memory + Advanced/Modular RAG retrieval, NOT context-stuffing. Durable
knowledge lives in a swappable external index (Lewis 05) so it is never trusted to model weights and
is per-tenant isolable. Retriever = hybrid dense+lexical pipeline (DPR 07 + RAG-survey 06):
query-rewrite -> retrieve -> re-rank -> compress, ranked by the explainable recency/relevance/
importance score (Generative Agents 04, weights/decay as TUNED PARAMETERS, never magic constants).
Assembled context places top items at the edges, never the middle (08), and stays short. The
"context windows are not memory" axiom (08) is binding. Critical retrieval claims (cosine formula,
dense>lexical) meet >=2 independent primary peer-reviewed sources (DPR + Lewis + Generative Agents).

## L1.A4.3 — Learning-over-time

**Option space surveyed:**
- No-gradient verbal RL with reflection-to-memory (Reflexion, 10 — NeurIPS 2023; HumanEval 80.1->91.0%).
- Cross-trajectory experience/insight abstraction without parametric updates (ExpeL, 11 — AAAI 2024).
- Reflection synthesis from observations (Generative Agents, 04 — threshold-triggered).
- Memory evolution / link-rewriting (A-Mem, 03).
- (Rejected family) parametric fine-tuning / RLHF on memory — infeasible for a hosted Claude model.

**Recommendation:** learn WITHOUT touching model weights — the only viable path for a hosted-model
platform, corroborated independently by Reflexion (10) and ExpeL (11), both peer-reviewed (>=2-source
bar met). Mechanism: a reflection loop (act -> evaluate with a SEPARATE judge -> write verbal
reflection -> condition next attempt; Reflexion 10) feeding a cross-trajectory Experience tier that
distills industry-scoped, versioned insights (ExpeL 11), triggered on accumulated importance
(Generative Agents 04). This is the engine for "AutoFirm gets better over time" and underpins B12
generalization. Insight reuse is curated/scoped to avoid overfitting one client (CLAUDE.md s3.9).

## L1.A4.4 — Memory security & governance

**Option space surveyed:**
- Six-phase lifecycle Write/Store/Retrieve/Execute/Share/Forget + five governance primitives
  WA/PV/PS/RB/VF (LTM Security Survey, 12).
- Primary attack evidence: AgentPoison (13 — NeurIPS 2024; >80% ASR at <0.1% poison rate, <1% benign degradation).
- Verified forgetting / deletion verification + reversibility risk (Unlearning Verification, 14).

**Recommendation (safety/correctness-critical — >=3 independent sources: 12, 13, 14):** the memory
layer is fail-closed by default and enforces all five primitives:
- WA — no write without an authenticated, authorized source (refuse on ambiguity).
- PV — every record carries queryable provenance lineage (joins A6 append-only audit).
- PS — retrieval is principal/tenant-scoped IN THE DATA LAYER, not by convention (joins A8.2).
- RB — versioned snapshots + write logs enable rollback to a known-safe state.
- VF — deletion is EXACT (external store, drop+reindex) and produces an auditable
  non-recoverability proof (14); approximate weight-unlearning is rejected as unverifiable.
A six-phase threat model with at least one adversarial test per phase is mandatory, with extra test
budget on the literature weak spots (store/share/forget per 12). AgentPoison (13) is the binding
red-team: an undefended baseline >80% ASR must be driven toward zero by WA+PS.

---

## Cross-branch joins (for L3 synthesis)
- A6 (provenance/audit): PV + "every memory write is an audited internal action" (CoALA 02).
- A7 (safety/fail-closed): WA/PS/VF are fail-closed; LLM self-edit (A-Mem 03, MemGPT 09) is governed, not autonomous.
- A8.2 (multi-tenant isolation): PS enforced in the data layer; per-tenant external indices (Lewis 05).
- A3 (long-horizon/resume): MemGPT tiering/paging (09) enables resume.
- B12 (generalization): ExpeL (11) cross-trajectory insights are the cross-industry learning engine.

## Evidence-showcase outputs (CLAUDE.md s3.10)
1. tokens-per-query vs accuracy (memory beats context-stuffing) — A-Mem 03 / Lost-in-Middle 08.
2. retrieval accuracy: hybrid vs BM25 baseline (top-20) — DPR 07.
3. accuracy-vs-trial learning curve — Reflexion 10 / ExpeL 11.
4. poisoning robustness: ASR vs poison-rate, defended vs undefended — AgentPoison 13.
5. retrieval-component ablation (recency/relevance/importance) — Generative Agents 04.

## Open items handed to L2.A4
- Pick concrete encoder + index tech (branch-experiment on the golden set).
- Tune (not hard-code) decay/threshold/weights from Generative Agents (04) per golden set.
- Decide reflection cadence + insight-curation/conflict-resolution policy.
