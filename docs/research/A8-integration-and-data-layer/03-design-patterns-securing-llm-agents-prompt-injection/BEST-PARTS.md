# BEST-PARTS — Design Patterns for Securing LLM Agents

## ADOPT (and which AutoFirm component each drives)
- **The core invariant** — "once an agent ingests untrusted input it must be impossible for that input to trigger consequential actions." → becomes a **hard platform rule**: untrusted data is forbidden from influencing control flow (tool selection) and is constrained out of high-impact tool parameters. This is the A8.1 acceptance criterion.
- **Dual LLM** for any flow where an AutoFirm agent must read untrusted external content (scraped pages, third-party docs, tool outputs): a **privileged orchestrator** (tools, trusted plan) + **quarantined reader** (no tools) whose outputs return as **symbolic variables** dereferenced by a non-LLM orchestrator. → drives the `quarantined_reader` service + symbolic-variable passing in the integration layer.
- **Plan-Then-Execute** for the orchestrator's own multi-step plans → control-flow integrity: a tool output can fill a parameter but can NEVER add/replace a planned action. Cheap, broadly applicable default.
- **LLM Map-Reduce** for batch ingestion (e.g., reading N filings/registry records) → isolates each untrusted document so one poisoned doc can't hijack the batch (directly serves the B4.4 public-data ingestion path).
- **Context-Minimization** as a cheap add-on to strip the raw user prompt / raw untrusted text before final output generation.

## REJECT / DEFER
- **Action-Selector as the *general* pattern — REJECT** for AutoFirm's open-ended company-building work: it is too rigid (all actions pre-enumerated). ADOPT it only for narrow, high-risk fixed actions (e.g., a payment-execution sub-tool with a closed action set).
- **Treating any single pattern as sufficient — REJECT.** The paper is explicit that flexibility erodes guarantees; AutoFirm layers patterns (defense-in-depth) rather than relying on one.

## CONCRETE BUILD IMPLICATION
- **Contract:** a `Trust` tag on every value in the agent runtime (`trusted | untrusted`), propagated; tool-call sites assert the control-flow decision and high-impact params are `trusted`-derived. Pairs with CaMeL capabilities (#04).
- **Test it drives:** AgentDojo-style adversarial suite (#05) as the platform's prompt-injection gate; property test: *no untrusted-tagged value reaches a consequential tool's action selector*.
- **Generality:** pattern set is task- and industry-agnostic.
