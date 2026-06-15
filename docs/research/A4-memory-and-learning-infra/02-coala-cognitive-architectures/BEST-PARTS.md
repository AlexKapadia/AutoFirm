# BEST-PARTS — CoALA

## ADOPT
- **The four-way memory taxonomy as AutoFirm's canonical memory types.** Build implication: the
  memory contract names exactly four stores — `working` (per-session context), `episodic`
  (trajectories/events of a build), `semantic` (facts about a client/company/industry), and
  `procedural` (reusable playbooks/skills). This is the schema backbone for L2.A4.
- **Internal vs. external action split as a governance boundary.** Memory reads/writes are
  **internal actions** subject to their own authorization, distinct from external tool calls.
  Build implication: every memory write is an auditable internal action (feeds A6 provenance and
  A4.4 Write-Authorization), and external grounding actions are gated separately under A7.
- **The propose/evaluate/select decision loop** as the place reflection and retrieval hook in.

## REJECT / DEFER
- **Reject conflating procedural memory with model weights only.** AutoFirm cannot fine-tune the
  base Claude weights per client; treat procedural memory as **explicit, externalized** playbooks
  (prompts/skills/code), not implicit weight updates — aligns with ExpeL's no-gradient stance.

## Build implication (concrete)
Defines the **four-store memory schema** (`working/episodic/semantic/procedural`) and the rule that
**every memory mutation is an audited internal action** — the join point between A4 (memory) and
A6/A7 (governance/safety).
