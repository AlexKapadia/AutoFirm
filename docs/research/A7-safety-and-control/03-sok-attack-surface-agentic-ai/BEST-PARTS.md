# BEST-PARTS — SoK Attack Surface of Agentic AI

## ADOPT
1. **"Tools + autonomy = the attack surface" as AutoFirm's framing.** AutoFirm's whole value is autonomous tool use across many integrations (A8) — so the threat model must center the *tool boundary*, not the model. *Build:* every tool registration carries a threat annotation; the integration layer (A8) is a primary security boundary.
2. **Supply-chain + tool-poisoning as first-class threats.** AutoFirm uses MCP servers, plugins, and skills — each is an untrusted dependency. *Build:* pin/verify MCP servers and skills; dependency + provenance scanning in CI (CLAUDE.md §5.6 dep-scan); treat a new tool like new code (review before grant).
3. **Defense-in-depth + anomaly detection.** Adopt the layered defense list as AutoFirm's A7 defense outline; pair static controls with runtime output monitoring. *Build:* anomaly detection on tool-call patterns feeds the audit agent (source 07) and the kill-switch (source 08).
4. **RAG/memory source verification.** Links to A4.4 memory poisoning + TRiSM (source 01). *Build:* retrieved/remembered content is integrity-checked and tagged untrusted before use.

## REJECT / DEFER
- **Defer using it as a sole numeric source** — it is a taxonomy SoK, not an efficacy benchmark; for defense effectiveness numbers cite AgentDojo/CaMeL (sources 05, 06).
- **Reject sandboxing alone as containment** — the SoK itself lists privilege-escalation/sandbox-escape as a category; sandboxing is necessary but must be combined with least-privilege capabilities (sources 09/10).

## Concrete build implications
- Produces AutoFirm's **attack-surface map**: model boundary, tool boundary, data/RAG boundary, memory boundary, supply-chain boundary — each gets a control + test row in the threat model.
- Validates the choice to make the **integration & data layer (A8)** a hardened, fail-closed chokepoint rather than letting agents call tools freely.
