# BEST-PARTS - Role Episode Model (Katz & Kahn)

## ADOPT
1. **The role episode == AutoFirm's onboarding handshake.** When a manager spawns an agent, it is
   the **role sender**; the spawned agent is the **focal person**. ADOPT the loop as the literal
   onboarding protocol: manager sends expectations (the charter) -> agent acknowledges its
   *received* role (restates the brief) -> agent enacts -> manager/QA observes and corrects until
   enacted behaviour matches expectations. This is the cited theoretical basis for an
   **acknowledge-and-restate** onboarding step, not fire-and-forget spawning.
2. **Role ambiguity / role conflict as the failure modes to engineer against.** AutoFirm's
   role-spec must minimise **ambiguity** (every expectation explicit, single-writer scope) and
   **conflict** (no two charters claim the same artifact). ADOPT these as named, testable defects:
   an ambiguity check (is every required behaviour specified?) and a conflict check (do any two
   live charters overlap in ownership?).
3. **Roles outlive incumbents - roles-as-data.** Katz & Kahn: organisations persist because roles
   persist independent of who fills them. ADOPT **roles as durable, audited data** (a role
   registry) distinct from the ephemeral agent *instances* that enact them; an agent can be
   retired/respawned without losing the role. Directly grounds A6.4's "roles-as-data audit trail".
4. **The role set defines the role.** A role is defined by its dependents, not in isolation. ADOPT:
   a charter must name its **role set** (who consumes its outputs / whom it reports to), so
   communication contracts (L2.A2) and accountability are explicit from spawn.

## REJECT
- **The affective/stress-and-wellbeing apparatus** (role strain, tension, coping) - human
  psychological strain doesn't transfer to agents. REJECT the wellbeing claims; ADOPT only the
  *structural* constructs (ambiguity, conflict, the sending loop) as design invariants.

## Build implication
- **Component:** `org-engine/onboarding` (the acknowledge-restate handshake) + `role-registry`
  (roles-as-data) + `charter-validator` (ambiguity + conflict checks).
- **Contract:** onboarding is not complete until the agent emits a `RoleReceived` acknowledgement
  whose restated scope matches the charter (role clarity check).
- **Test:** conflict check is a property test over the live charter set - asserts no two charters
  share an owned artifact (single-writer invariant), feeding an `evidence/` zero-conflict metric.
