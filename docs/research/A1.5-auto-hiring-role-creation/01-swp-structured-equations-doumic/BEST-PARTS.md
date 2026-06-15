# BEST-PARTS - SWP structured equations (Doumic et al. 2016)

## ADOPT
1. **The SWP definition as AutoFirm's gap-detect contract.** AutoFirm's `gap-detect` step is
   literally: `gap(t) = required_capability(t) - available_capability(t)` measured **over time**,
   not at a single instant. ADOPT this as the formal definition the gap-detector implements.
2. **The 5 milestones as the gap-detect -> role-spec pipeline stages.** Map directly onto the
   AutoFirm org engine:
   - baselining        -> snapshot current agent-org roster (roles-as-data registry).
   - demographic fcast -> project natural evolution (which agents will retire / context-exhaust).
   - business needs    -> the manager's stated objective decomposed into required
     headcount + **competencies** (drives the role charter's `must_study` skill set).
   - gap analysis      -> the gap-detector's output (surplus / shortage / skill-gap).
   - bridge solutions  -> spawn / onboard / redeploy / retire decisions.
   This is the canonical, cited backbone for L2.ORG's lifecycle.
3. **Competency dimension is first-class, not just headcount.** The framework explicitly gathers
   "business needs, both in terms of **headcount and competencies**." AutoFirm must detect *skill*
   gaps (a missing capability), not only *capacity* gaps (too few workers) - the two trigger
   different remedies (spawn-new-role vs. spawn-another-instance).
4. **Saturating spawn-rate to prevent agent-population explosion.** The h(P_t)=1/(1+P_t^2)
   saturation is the mathematical justification for a **span-of-control / spawn-rate cap** in the
   org engine: unbounded proportional spawning is the linear (Malthusian) case that explodes.
   ADOPT a saturating spawn function so the agent count converges to a stable P_eq rather than
   blowing up context/compute. This is a directly testable invariant.
5. **Retirement as a hard boundary condition.** Modelling retirement as the z_max boundary maps
   onto AutoFirm's `retire` step: a role/agent that crosses a defined boundary (task done,
   context exhausted, capability obsolete) leaves the active roster deterministically.

## REJECT
- **The specific PDE solver / long-time asymptotics machinery.** AutoFirm's roster is small and
  discrete (dozens of agents, not a continuous age density); the continuous renewal-PDE and its
  convergence proofs are overkill. ADOPT the *conceptual* structure (in/out flows, saturation,
  boundary-retirement) but implement it as a **discrete roles-as-data state machine**, not a PDE.
- **The flat-labour-cost economic objective as the primary metric.** AutoFirm optimises
  capability-coverage and task-throughput under a compute budget, not payroll smoothing; reject
  cost-flatness as the objective but keep "minimal cost to maintain experience" as a *secondary*
  budget constraint.

## Build implication
- **Component:** `org-engine/gap-detector` and `org-engine/roster-dynamics`.
- **Contract:** `Gap = {role_id, kind: SHORTAGE|SURPLUS|SKILL_GAP, magnitude, competencies[]}`
  computed as required - available over a time window.
- **Invariant + test:** spawn-rate is saturating; property test asserts roster size converges and
  never exceeds a configured P_max (the org-engine cap) for any arrival pattern - directly feeds
  `evidence/` as a stability chart (population vs. time -> P_eq).
