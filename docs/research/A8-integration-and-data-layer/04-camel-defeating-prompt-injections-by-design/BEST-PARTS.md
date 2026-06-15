# BEST-PARTS — CaMeL (Defeating Prompt Injections by Design)

## ADOPT
- **Control-flow / data-flow separation as a design principle** — the trusted query defines the program; untrusted data can never alter the program flow. → AutoFirm's integration layer should derive the *plan/program* from the trusted orchestrator only; untrusted content is data the program operates on, never instructions.
- **Capabilities = provenance + permission metadata on every value**, with a **non-LLM interpreter enforcing the policy** at each tool call. → drives a `capability` wrapper on integration-layer values: each carries (source, tenant, sensitivity, allowed-sinks); the gateway/runtime blocks disallowed flows (e.g., one tenant's data -> another's sink; private data -> public egress). This is the *enforcement engine* behind the A8.1 trust-tag and the A8.2 tenant boundary.
- **Provable-security framing + a measurable target** — 77% of AgentDojo tasks solved *with provable security* (vs 84% with an undefended system; arXiv v2 abstract) gives AutoFirm a concrete bar to beat/track in `evidence/`: close the 77%->84% utility gap while keeping provable security.
- **Explicit security policies** as code (not prompts) → fail-closed, auditable, testable (ties to A6 audit, A7 fail-closed).

## REJECT / note limitations
- **Don't treat CaMeL as zero-cost** — the authors flag a **policy-authoring burden** and residual **side channels**. AutoFirm adopts the architecture but must budget for policy authoring + accept that side-channel leakage needs separate controls (rate/size limits, egress allowlists from #01).
- Do not over-claim "provable" beyond the policy's coverage — provability is relative to the written policy.

## CONCRETE BUILD IMPLICATION
- **Component:** `capability_interpreter/` — a non-LLM execution/enforcement layer between the planning LLM and tools, tagging values and enforcing data-flow policies. Unifies A8.1 (injection), A8.2 (tenant), A8.3 (credential-scope) enforcement in one auditable place.
- **Test it drives:** AgentDojo provable-security score as a tracked metric; capability-flow property tests (no cross-tenant / private->public flow ever permitted).
- **Re-read note:** before quoting interpreter internals verbatim, re-read arXiv:2503.18813 v2 PDF §3-4.
