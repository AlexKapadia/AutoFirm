# SUMMARY — Design Patterns for Securing LLM Agents Against Prompt Injections

## Full citation
- **Title:** Design Patterns for Securing LLM Agents Against Prompt Injections.
- **Authors:** Luca Beurer-Kellner, Beat Buesser, Ana-Maria Cretu, Edoardo Debenedetti, Daniel Dobos, Daniel Fabian, Marc Fischer, David Froelicher, Kathrin Grosse, Daniel Naeff, Ezinwanne Ozoani, Andrew Paverd, Florian Tramer, Vaclav Volhejn.
- **Year:** 2025.
- **Venue/Affiliation:** arXiv:2506.08837 (v2). Multi-institutional: Invariant Labs, IBM, EPFL, ETH Zurich, Swisscom, Google, AppliedAI Institute for Europe, Microsoft, Kyutai.
- **URL:** https://arxiv.org/abs/2506.08837 · HTML: https://arxiv.org/html/2506.08837v2 · PDF: https://arxiv.org/pdf/2506.08837

## Questions informed
- **L1.A8.1** Untrusted-input handling for tool-using agents (the integration layer agent-facing side).

## GRADE tier
**Moderate** (arXiv preprint with explicit methods/case studies; strong named multi-org authorship; not yet a peer-reviewed venue). Corroborated by CaMeL (#04), OWASP LLM cheat sheet (#06), AgentDojo (#05) -> body-of-evidence confidence high.

## Core security principle (exact quote)
> "Once an LLM agent has ingested untrusted input, it must be constrained so that it is impossible for that input to trigger any consequential actions—that is, actions with negative side effects on the system or its environment."

Fundamental constraint: untrusted data must be isolated from control-flow decisions (which tools/actions) and, where possible, from tool-call parameters. Untrusted = anything not authored by the developer or an explicitly trusted user (user inputs, third-party docs, DB contents, API responses, external docs).

## The six patterns (definition - guarantee - tradeoff)
1. **Action-Selector** — LLM-modulated switch mapping NL to one of a predefined set of tool calls. Guarantee: trivially injection-immune (no feedback loop). Tradeoff: low flexibility; all actions pre-defined.
2. **Plan-Then-Execute** — fix the plan (action list) before execution; tool outputs may set parameters but cannot change which actions run. Guarantee: control-flow integrity. Tradeoff: parameters still manipulable; doesn't stop injection in the user prompt.
3. **LLM Map-Reduce** — isolated sub-agents each process one untrusted item (map); aggregate via non-LLM reduce or constrained-LLM reduce. Guarantee: malicious data in one source can't affect processing of others. Tradeoff: needs decomposable task; a doc can still boost its own score.
4. **Dual LLM** — privileged LLM (tools, trusted) + quarantined LLM(s) (no tools, untrusted data); quarantined outputs become symbolic variables the privileged LLM manipulates by reference; a non-LLM orchestrator dereferences. Guarantee: untrusted data cannot trigger tool execution. Tradeoff: quarantined LLM still injectable in its outputs.
5. **Code-Then-Execute** — LLM emits an explicit program that calls tools and invokes unprivileged LLMs on untrusted text. Guarantee: transparent control flow; planning/execution separated. Tradeoff: parameters still alterable; modest gain over plan-then-execute.
6. **Context-Minimization** — strip unnecessary content (esp. the user prompt) from context after the decision, before generating the result. Guarantee: user-prompt injections can't shape final output. Tradeoff: doesn't stop third-party-data injection.

## Up/down-rate reasoning
- Up-rated: named senior researchers across many orgs; concrete patterns with worked case studies; consistent with peer-reviewed CaMeL.
- Down-rated: preprint; patterns are design guidance, not measured effect sizes (numbers come from AgentDojo/CaMeL).

## Reproducibility note
The six pattern names + the core constraint quote are on the v2 HTML/PDF; each pattern guarantee/tradeoff is in its section.
