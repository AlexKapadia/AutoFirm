# BEST-PARTS - Workforce Reshaping / RIF (OPM 2017)

## ADOPT
1. **The RETIRE step's drivers, named and detectable.** A role/agent becomes a retirement
   candidate when: (a) the **mission/objective shifts** so the role is no longer on the critical
   path; (b) **roles overlap** (two agents redundantly own the same capability after a reorg/
   experiment merge); or (c) the capability is **superseded** (a better approach won - CLAUDE.md
   no-graveyard). ADOPT these three as the gap-detector's *surplus/obsolescence* signals - the
   inverse of the shortage signals (source 01/02).
2. **Redeploy-before-eliminate as the default retire policy.** Per the handbook, prefer
   **reassigning** an agent's capability to a still-needed role over deleting it outright; only
   eliminate when no need remains. ADOPT a `retire` decision tree: try redeploy -> else retire.
   This preserves "institutional knowledge" = the agent's accumulated memory/context (ties to A4
   memory: on retire, harvest the agent's learnings into shared memory before teardown).
3. **Plan retirement ahead, not reactively.** "More time -> less forced RIF": AutoFirm should
   detect impending role obsolescence early (e.g. an experiment branch is losing) and schedule an
   orderly retirement + handoff, not an abrupt kill. ADOPT a graceful-retirement protocol:
   checkpoint -> harvest memory -> hand off owned artifacts -> deregister -> teardown.
4. **No-graveyard alignment.** The handbook's "decline to staff the now-vacant position" maps to
   CLAUDE.md's no-graveyard rule: when a role is retired, its artifacts are reassigned or deleted
   in the same change - no orphaned dead roles left in the registry.

## REJECT
- **Federal RIF legal apparatus** (tenure groups, veteran preference, retention registers, appeal
  rights, furlough law). Entirely jurisdiction-specific employment law with no agent analogue.
  REJECT wholesale; keep only the redeploy-before-eliminate + plan-ahead + harvest-knowledge
  principles.

## Build implication
- **Component:** `org-engine/retire` with a graceful protocol:
  `detect-obsolescence -> attempt-redeploy -> (else) checkpoint+harvest-memory -> handoff-artifacts
  -> deregister-from-role-registry -> teardown`, all audited.
- **Contract:** a retire is only complete when the role's owned artifacts are reassigned-or-deleted
  (no-graveyard invariant) and the agent's memory is harvested (knowledge-retention).
- **Test:** property test asserts that after any retire, (a) the role registry has no orphaned
  artifacts owned by the retired role, and (b) a memory-harvest record exists. Feeds an `evidence/`
  "clean-retirement / zero-graveyard" metric.
