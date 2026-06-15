# BEST-PARTS - Six Socialization Tactics (Van Maanen & Schein)

## ADOPT
1. **Pick the institutionalized cluster for AutoFirm onboarding - it is the lower-ambiguity,
   higher-fit pattern (empirically, sources 06/08).** Concretely, AutoFirm onboarding should be:
   - **Sequential + Fixed (content tactics):** a defined, ordered onboarding sequence with a
     known completion point (the `must_study` reading list + an acknowledgement gate) - NOT
     ad-hoc. This is the cited basis for the `must_study` rule.
   - **Serial (social tactic):** a predecessor/manager role-models the role - i.e. the spawning
     manager (or a prior agent's handoff notes) seeds the newcomer, reducing cold-start ambiguity.
   - **Formal:** onboarding is an explicit, prescribed step in the lifecycle, not learned by
     trial-and-error mid-task.
2. **Investiture (affirm incoming skills).** Spawn agents with their relevant skills/tools already
   provisioned and acknowledged, rather than stripping context - reduces ramp time.
3. **Choose the tactic deliberately per role.** Routine, must-never-deviate roles -> fully
   institutionalized (custodial, predictable). Exploratory/experiment roles -> lean individualized
   (innovative, role-redefining) to allow the agent to redefine the approach. ADOPT tactic-choice
   as a charter field, justified by this taxonomy.

## REJECT
- **Divestiture (identity-stripping).** Costly, slow, and irrelevant for agents - REJECT; always
  use investiture (provision skills up front).
- **Collective tactics as a default.** AutoFirm agents are mostly spawned individually for scoped
  work; collective cohort-socialisation rarely applies. Use individual unless a genuine cohort
  (e.g. a parallel experiment fleet) exists.

## Build implication
- **Component:** `org-engine/onboarding` + `role-charter.socialization_profile`.
- **Contract:** `socialization_profile in {INSTITUTIONALIZED, INDIVIDUALIZED}` with the
  institutionalized profile mandating: ordered `must_study` list, a serial handoff source, and an
  acknowledgement gate before first action.
- **Test:** an agent on the INSTITUTIONALIZED profile cannot take its first task action until its
  `must_study` items are marked read and its `RoleReceived` ack is logged - deterministic gate,
  unit-testable, audited.
