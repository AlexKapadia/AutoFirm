# BEST-PARTS — A-MEM

## ADOPT
- **Zettelkasten-style structured notes with explicit links** as AutoFirm's episodic/semantic store
  format. Build implication: a memory record carries `{content, timestamp, keywords, tags,
  context, embedding, links[]}` — directly instantiating the CoALA episodic/semantic stores with a
  retrievable+navigable graph.
- **Embedding retrieval via cosine similarity** (formula 3/5) as the default retriever for the
  memory layer — cheap, deterministic given a fixed encoder, and testable.
- **Context efficiency as a hard KPI.** The ~1,200-2,500 vs ~16,900 token result is the evidence
  that memory-augmentation beats stuffing full history into context (directly supports the
  "context windows are not memory" thesis of L1.A4.2 / Lost-in-the-Middle). Use as an
  `evidence/` chart: tokens-per-query vs accuracy.

## REJECT / DEFER
- **Defer automatic LLM-driven "memory evolution" (formula 4) under fail-closed governance.** Letting
  an LLM rewrite existing historical memories is an integrity risk (it is exactly the surface the
  LTM-security survey, folder 12, warns about: write-time corruption). Adopt the *structure* and
  *linking*; gate destructive in-place rewrites behind Write-Authorization + provenance + rollback
  (A4.4). Prefer append-with-supersede over in-place mutation so history is auditable.
- **Reject treating the adversarial-category number as a win** — be honest: baseline beat A-Mem there.

## Build implication (concrete)
Specifies the **episodic/semantic record format + cosine retriever** for L2.A4, plus the
**tokens-per-query efficiency KPI** for the evidence showcase, and flags **in-place memory rewrite
as a governed (not default-on) operation**.
