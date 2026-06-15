# BEST-PARTS - HALO dynamic role instantiation

## ADOPT
1. **The mid-level role-design agent == AutoFirm's manager-authored role-spec step, validated in
   MAS.** HALO demonstrates that **instantiating task-specific roles on demand** (vs. a fixed role
   roster) measurably outperforms static designs (+14.6% avg over ADAS). ADOPT this as the
   *platform-side evidence* that AutoFirm's gap->role-spec->spawn dynamic-role lifecycle is the
   right pattern, not over-engineering: dynamic > static, with numbers.
2. **Three-layer separation maps onto AutoFirm's org engine.** plan (decompose objective) ->
   role-design (author charter + spawn) -> inference (the worker executes). ADOPT the layer split
   so role-DESIGN (charter authoring) is a distinct, auditable step owned by the manager, separate
   from EXECUTION. This cleanly separates "who creates roles" from "who does work" - reinforcing
   the RACI decision-rights gate (source 09).
3. **Role instantiation is conditioned on subtask semantics + global context.** ADOPT: a spawned
   agent's charter is derived from (a) the specific gap/subtask and (b) the global objective/
   workspace context - not a generic template. This is the "general, not overfit" charter-authoring
   rule (CLAUDE.md §3.9) given a concrete mechanism.
4. **Benchmark numbers as a target for AutoFirm's own org-engine evaluation.** Use the HALO deltas
   as a comparison point: AutoFirm's dynamic-role engine should be A/B-tested (dynamic-role vs.
   fixed-roster) on its own golden set and is expected to win, per this evidence.

## REJECT
- **MCTS workflow search as AutoFirm's spawn mechanism.** HALO's MCTS over the agentic action space
  is a per-task search heuristic; AutoFirm's roles are durable, audited org entities, not
  search-tree nodes. REJECT MCTS for role lifecycle; ADOPT the *role-design-agent* concept only.
- **HALO's lack of a retirement mechanism.** HALO instantiates but does not retire roles. REJECT
  the implicit "never retire" stance; AutoFirm MUST add the org-theory retirement step (sources
  04, 10) - this is a named gap HALO does not cover.

## Build implication
- **Component:** `org-engine` three-layer split: `planner` (decompose) | `role-designer` (author
  charter + decide spawn, under RACI decision-rights) | `worker` (execute).
- **Evidence/test:** an A/B experiment on `experiment/dynamic-roles` vs. `experiment/fixed-roster`
  measured on the org-engine golden set; expected win for dynamic roles (HALO-corroborated),
  recorded in `evidence/` with the comparison chart - the only winner merges to main (CLAUDE §3.4).
