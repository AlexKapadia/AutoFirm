# BEST-PARTS — RAG (Lewis et al. 2020)

## ADOPT
- **The parametric/non-parametric split as AutoFirm's core memory principle.** Build implication:
  AutoFirm NEVER relies on the model's weights to "remember" client/company facts — durable facts
  live in a **swappable external index** (the semantic store), retrieved at inference. This is the
  architectural justification for an external memory layer at all.
- **Index-swap = knowledge update without retraining.** Build implication: per-client and
  per-industry knowledge is updated by writing to the index, not by fine-tuning — enabling
  multi-tenant isolation (each tenant's index is separate; ties to A8.2) and instant correction.
- **Marginalize-over-top-k** as a robustness pattern when a single retrieved doc is unreliable.

## REJECT / DEFER
- **Defer end-to-end joint training of retriever+generator.** AutoFirm uses a frozen hosted model
  (Claude); it cannot backprop into the generator. Adopt RAG's *inference-time* retrieval pattern,
  not its *training* recipe.

## Build implication (concrete)
Grounds the decision that **company/client knowledge = external swappable index, never model
weights** — the foundation of the L2.A4 semantic store and its per-tenant isolation (A8.2).
