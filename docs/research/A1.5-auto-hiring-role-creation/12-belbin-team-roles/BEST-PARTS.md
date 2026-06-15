# BEST-PARTS - Belbin Team Roles

## ADOPT
1. **A capability gap can be a MISSING ROLE TYPE, not just missing headcount.** Belbin's coverage
   principle gives AutoFirm a third gap kind beyond SHORTAGE (too few) and SKILL_GAP (missing
   competency): a **ROLE_COVERAGE_GAP** - a needed *function* is entirely uncovered (e.g. no
   QA/critic role, no integrator/co-ordinator role). ADOPT: the gap-detector checks that the
   org has the **function archetypes** the objective needs (a maker, a critic/evaluator, an
   integrator, a finisher), echoing CLAUDE.md's mandate for management + QA functions in the
   org engine.
2. **The "critic/evaluator" and "finisher" archetypes are mandatory.** Belbin's Monitor-Evaluator
   (critical judgement) and Completer-Finisher (closes out, checks details) map directly to
   AutoFirm's **generator/evaluator split** and iterate-to-perfection loop. ADOPT: every
   non-trivial sub-org must cover an *evaluator* role distinct from the *maker* role (a different
   agent must judge - CLAUDE.md §4.9). This is org-theory backing for the separate-reviewer rule.
3. **Coordinator/integrator archetype == the orchestrator.** Belbin's Co-ordinator (clarifies
   goals, delegates) is the COO/orchestrator function; ADOPT as a required covered role.

## REJECT
- **Belbin's specific 9-role taxonomy as a literal agent role-set, and the SPI psychometrics.**
  The evidence on specific role mixes predicting performance is **mixed** (Aritzeta et al. 2007),
  and the personality-trait basis (Growth/behaviour styles) doesn't transfer to agents. REJECT the
  nine named roles as a fixed schema and REJECT any quantitative role-balance claim. Keep ONLY the
  abstract **"cover the needed function archetypes (maker / critic / integrator / finisher)"**
  principle.

## Build implication
- **Component:** `org-engine/gap-detector` gains a third gap kind:
  `ROLE_COVERAGE_GAP` (a required function archetype is uncovered).
- **Contract:** the org-engine enforces that any spawned sub-org covers at minimum a
  {maker, evaluator, integrator} set for non-trivial objectives (evaluator != maker agent).
- **Test:** property test - for a non-trivial objective, the resulting org has at least one
  evaluator role distinct from its maker role(s); a coverage report feeds `evidence/`.
