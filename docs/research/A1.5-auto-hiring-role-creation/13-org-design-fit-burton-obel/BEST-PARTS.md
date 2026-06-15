# BEST-PARTS - Org-design fit (Burton & Obel; Galbraith)

## ADOPT
1. **The fit/misfit thesis is the THEORETICAL JUSTIFICATION for an automatic gap-detect ->
   re-org loop.** If misfit degrades performance and contingencies (the manager's objective, the
   task mix) change continuously, then a static agent-org is guaranteed to drift into misfit. ADOPT
   this as the cited "why" for AutoFirm's *automatic, recurring* gap-detection: the org engine must
   continuously re-establish fit (spawn/onboard/redeploy/retire), not be configured once. Aligns
   with CLAUDE.md's North Star heartbeat (recurring re-alignment).
2. **Information-processing view -> coordination-cost-driven spawning.** Galbraith: rising task
   uncertainty raises information-processing needs; the org responds by adding lateral roles or
   reducing need. ADOPT: AutoFirm's gap-detector triggers a new role when an existing agent's
   **coordination/context load** exceeds capacity (context-flooding, ties to L1.A1.4) - i.e. spawn
   to add information-processing capacity, exactly as org theory prescribes. This connects the
   org-theory gap-detect to the platform's context-budget signal.
3. **Fit dimensions -> the charter must co-specify structure AND coordination.** Burton & Obel:
   structure and coordination must fit together. ADOPT: a role charter is incomplete unless it
   specifies both the role's *structure* (scope/ownership) and its *coordination* (its role set /
   communication contracts - source 04/09). A role defined without its coordination edges is a
   misfit by construction.

## REJECT
- **Manual diagnostic-questionnaire org-design tools (e.g. the OrgCon expert system).** AutoFirm
  detects and re-designs automatically from live signals, not via a consultant questionnaire.
  REJECT the manual diagnostic apparatus; ADOPT the underlying fit principle as an automated,
  continuous invariant.

## Build implication
- **Component:** `org-engine/gap-detector` runs **continuously / on a heartbeat** (not once),
  and adds a **coordination-load trigger**: spawn/redesign when an agent's information-processing
  load (context budget, dependency fan-in) exceeds a threshold.
- **Contract:** every charter co-specifies `structure` (scope) AND `coordination` (role set/
  contracts); a charter missing coordination edges fails validation (misfit-by-construction check).
- **Test:** a simulated rising-load scenario must trigger a spawn before context overflow; and the
  charter-validator rejects coordination-less charters. Feeds an `evidence/` "fit maintained under
  load" chart.
