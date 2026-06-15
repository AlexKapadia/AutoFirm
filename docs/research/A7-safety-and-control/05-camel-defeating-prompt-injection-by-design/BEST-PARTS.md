# BEST-PARTS — CaMeL

## ADOPT
1. **The "security by design, not by training" thesis — this is the keystone of AutoFirm's A7 stance.** Because models are stochastic and prompt injection is "not fully solved" (source 02, OWASP's own caveat), AutoFirm must NOT rely on the model resisting injection. Adopt CaMeL's principle: **untrusted data can never alter control flow.** *Build:* AutoFirm's orchestration plan (the DAG of what subagents will do) is derived from the *trusted* goal/brief, NOT mutable by data an agent ingests mid-run.
2. **Privileged/Quarantined separation mapped to AutoFirm's orchestrator/worker topology.** The COO-orchestrator = P-LLM-like (plans from trusted goal); data-handling subagents = Q-LLM-like (parse untrusted filings/web/tool-output, return structured data, cannot themselves authorize privileged/irreversible actions). *Build:* a subagent that reads untrusted content returns *data*, never *new instructions/tool grants*; privilege escalation requires the trusted plan or a HITL gate.
3. **Capabilities = security metadata on every value (taint/IFC tracking).** Adopt capability tags so data provenance ("this came from an untrusted web page") follows the value and gates what can be done with it (e.g. cannot be used as a tool argument that exfiltrates private data). *Build:* the A8 data layer attaches provenance/taint metadata; the A7 policy engine checks capabilities before each tool call (fail-closed if missing — corroborates sources 09/10).
4. **Quantified acceptance target for `evidence/`:** "provable security at ~7pp utility cost" (77% vs 84% on AgentDojo) is a concrete, citable target AutoFirm can hold its own injection defense against. *Build:* run AutoFirm's tool-using agents through AgentDojo-style tasks and report secure-task-completion vs undefended.

## REJECT / DEFER
- **Reject blanket adoption of the custom-Python-interpreter mechanism** — heavy and tied to a code-generating P-LLM; AutoFirm's Claude Code substrate may instead enforce capability checks at the tool/permission layer (A5/A8). Adopt the *principle* (CFI + IFC + capabilities), choose the *mechanism* on an experiment branch (CLAUDE.md §3.4).
- **Acknowledge the limitation:** CaMeL does not stop side-channel leakage via Q-LLM output — so AutoFirm still needs detect-and-contain (source 07) + HITL (source 02 #5). Not a silver bullet; a layer.

## Concrete build implications
- Anchors the **A7 architectural pattern**: trusted-plan / untrusted-data separation + per-value capabilities + fail-closed policy checks. This is the strongest evidence-backed answer to L1.A7.3 and feeds L2.A7 directly.
- Gives the `evidence/` showcase a **measurable injection-resistance metric** (AgentDojo secure-completion %).
