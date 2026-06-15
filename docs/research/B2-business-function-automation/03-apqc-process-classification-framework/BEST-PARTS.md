# BEST-PARTS — APQC PCF → AutoFirm

## ADOPT
- **PCF as AutoFirm's OPERATIONAL function taxonomy (the L2–L4 detail under Porter's L1 spine).**
  This is the single most directly reusable artifact for B2: an industry-agreed, hierarchical,
  cross-industry process tree that already names "hundreds of processes" in a neutral vocabulary.
  **Build implication:** seed `function_decomposition/process_taxonomy/` with the 12 categories →
  process groups → processes hierarchy. Each leaf process is the unit an agent-team is assigned to
  and the unit at which automatability is scored (source 06 McKinsey gives the scoring method).
- **The 5-level hierarchy (Category→Group→Process→Activity→Task)** is exactly the granularity
  AutoFirm needs to delegate: Categories → agent-org divisions; Processes → sub-teams; Tasks →
  individual agent turns. It also matches the "task-based" automation evidence (sources 06/07):
  automation is decided at the *Activity/Task* level, not the *Category* level.
- **"Horizontal processes, not vertical functions"** is the right mental model for an autonomous
  agent company — work flows across the chain, so AutoFirm's orchestration should follow process
  flow (matches A1/A2 workflow-DAG research) rather than rigid departmental silos.
- **Industry-neutral by design** → directly serves the B12 generality requirement; the same 12
  categories apply to every panel industry, with industry-specific PCFs (banking, healthcare,
  telecom, retail, etc.) available as overlays when a client needs depth.

## REJECT / use-with-care
- **Reject wholesale literal import without version-pinning.** Labels and the operating/support
  split shift across versions; AutoFirm must **pin a specific PCF version** (cite the exact
  version in the spec) so the taxonomy is deterministic and auditable (CLAUDE §3.13 traceability).
- **Reject PCF as a *strategic* or *business-model* layer** — it is purely operational; pair it with
  Porter (strategy) and BMC (business logic). PCF answers "what processes run", not "is this a good
  business" or "how does it make money".
- **Use-with-care: APQC licensing.** The cross-industry PCF is freely downloadable but APQC asserts
  IP over the framework content; AutoFirm should treat it as a *reference vocabulary mapping*, not
  redistribute the verbatim PCF text in client deliverables (legal note for B10).

## Concrete build implication
- Component: `function_decomposition/process_taxonomy/apqc_pcf_v8_seed.py` — version-pinned 12-category hierarchy with stable IDs; each node carries `{id, level, parent, automatability_score}`.
- Test it drives: every B12 panel industry must populate all 12 categories with at least one active process; a determinism test asserting the same client input yields an identical process tree across repeated runs (CLAUDE §3.6 determinism).
