# BEST-PARTS - Job Characteristics Model (Hackman & Oldham)

## ADOPT
1. **The five core dimensions as the role-charter schema.** When a manager authors a role-spec,
   the charter must specify, for the agent's role: **skill variety** (which `must_study`
   skills/tools), **task identity** (a whole, owned deliverable - not a fragment), **task
   significance** (how it serves the manager's objective), **autonomy** (decision scope /
   single-writer ownership), and **feedback** (the explicit success metric / QA signal the agent
   gets back). ADOPT these five as the *mandatory fields* of every AutoFirm role charter.
2. **Task identity == single-writer ownership.** AutoFirm's single-writer rule (one agent owns a
   directory/artifact) is exactly JCM "task identity": a whole identifiable piece of work. This is
   independent theoretical justification for the single-writer design.
3. **Feedback is mandatory, not optional.** JCM makes feedback a core dimension; a role with no
   feedback loop is defective by design. ADOPT: every spawned agent charter MUST define the
   metric/QA signal it receives - operationalising CLAUDE.md's iterate-to-perfection loop at the
   role-design layer.
4. **MPS as a role-charter quality gate.** Because MPS is multiplicative in autonomy x feedback,
   a charter with zero autonomy OR zero feedback scores ~0. ADOPT a **charter-completeness check**:
   reject any authored role-spec that lacks a defined ownership scope (autonomy) or a defined
   success signal (feedback). This is a deterministic, testable pre-spawn validation.

## REJECT
- **Growth Need Strength moderation.** GNS is an individual-difference variable about human
  intrinsic motivation; LLM agents have no GNS. REJECT the motivational/affective claims; ADOPT
  only the **structural** dimensions as a role-design checklist, not as a satisfaction predictor.
- **MPS as a numeric optimisation target.** Don't optimise agents to maximise a motivation score;
  use MPS's *structure* (the multiplicative gate) as a completeness check, not a KPI.

## Build implication
- **Component:** `role-charter` schema + `org-engine/charter-validator`.
- **Contract:** `RoleCharter = {role_id, must_study[], owned_artifact (task identity),
  objective_link (significance), ownership_scope (autonomy), success_signal (feedback)}`.
- **Test:** property test - a charter missing `ownership_scope` or `success_signal` FAILS
  validation (MPS-collapse analogue) and cannot be spawned. Feeds `evidence/` as a
  charter-completeness pass-rate metric.
