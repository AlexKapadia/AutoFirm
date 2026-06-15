# BEST-PARTS — AgentDojo

## ADOPT
- **AgentDojo as AutoFirm's prompt-injection evaluation harness** for the integration layer. → it is the golden-set/metric (CLAUDE.md §3.4/§4.5) against which any A8.1 defense (dual-LLM, CaMeL capabilities, plan-then-execute) is *measured*, not asserted. Defenses compete on `experiment/*` branches; the winner is the one with the best AgentDojo robustness at acceptable utility.
- **Its threat model** — "data returned by external tools hijacks the agent to execute malicious tasks" — as the canonical statement of the indirect-injection risk AutoFirm's egress/ingest layer must contain.
- **Extensibility** — AgentDojo is an environment, not a fixed test set → AutoFirm adds **company-building-specific tasks** (e.g., reading a malicious vendor doc during procurement, a poisoned public filing during financial modeling) to cover its real attack surface beyond the stock email/banking/travel tasks.

## REJECT / scope
- **Do not treat a high AgentDojo score as total security** — it measures one class (indirect injection via tool outputs). It is necessary, not sufficient; combine with multi-tenant isolation tests (#07/#08) and credential-scope tests (#09/#10).
- It is an LLM-agent benchmark, not a data-layer or secrets benchmark — keep it scoped to A8.1.

## CONCRETE BUILD IMPLICATION
- **Evidence artifact:** an AgentDojo robustness/utility curve per candidate defense, feeding `evidence/` (accuracy-with-error-bars chart) — the quantitative proof the integration-layer defense works.
- **Test it drives:** CI gate = AgentDojo (stock + AutoFirm-added tasks) must pass the agreed robustness threshold before any tool-using agent ships.
- **Generality:** tasks are deliberately diverse; AutoFirm extends them across the B12 industry panel so the defense is proven general, not overfit.
