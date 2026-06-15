# BEST-PARTS — Formal MCP Security Framework

## ADOPT
1. **This is AutoFirm's MCP-specific A7.3 mechanism source** — AutoFirm's substrate IS MCP + Claude Code tools, so the MCP threat taxonomy and defenses apply directly (no indirectness down-rate). Adopt all five defenses as the A7 tool-layer control set:
   - **Least-Privilege Enforcement** + **Capability Scoping** -> per-agent capability matrix binding tools to task context (operationalizes Saltzer/Schroeder least-privilege, source 09, and CaMeL capabilities, source 05). *Build:* each MCP tool grant is a scoped, expiring capability; arguments validated against the matrix.
   - **Fail-Closed Design** -> "deny when trust boundary uncertain" — verbatim AutoFirm doctrine (CLAUDE.md §5.6). *Build:* ambiguous/missing capability = refuse.
   - **Runtime Monitoring** + **Complete Mediation** (source 09) -> intercept and validate every MCP tool invocation against declared policy. *Build:* an A7 policy-enforcement point sits between agent and MCP server.
   - **Zero-Trust** -> verify every MCP request before execution, including requests from trusted-but-possibly-compromised agents.
2. **Adopt the formal grounding (Denning / Schneider / Ligatti) as AutoFirm's verification model.** This lets AutoFirm express its A7 policy as an *enforceable security policy* (Schneider) implemented as a runtime monitor / edit-automaton over tool calls, with information-flow (Denning lattice) tracking taint/capabilities. *Build:* the A7 policy engine is a runtime monitor (Schneider edit-automaton style) over the tool boundary — citable, formal, regulator-defensible.
3. **Tool Poisoning + Supply-Chain rows** corroborate source 03 -> drives MCP server/skill verification before grant.

## REJECT / DEFER
- **Defer the heaviest formal-verification machinery** (full property-based proofs over all behavior) as aspirational — adopt the *model* (enforceable policy + IFC lattice + complete mediation) now; full formal proofs are a later evidence target, not a Gate-2 blocker.
- **Reject relying on its (absent) quantitative results** — no own benchmark in the excerpt; for efficacy numbers use AgentDojo/CaMeL/AutoGuard (sources 05, 06, 08).

## Concrete build implications
- Gives AutoFirm a **formal, citable A7.3 enforcement architecture**: a runtime policy-monitor at the MCP tool boundary doing complete mediation + capability scoping + fail-closed denial + IFC taint tracking. This is the direct, evidence-backed answer to L1.A7.3 and the core input to L2.A7.
- Unifies sources 05 (capabilities/IFC), 09 (least-priv/fail-safe/complete-mediation principles), and 10 (MCP-specific enforcement + formal model) into one enforcement point.
