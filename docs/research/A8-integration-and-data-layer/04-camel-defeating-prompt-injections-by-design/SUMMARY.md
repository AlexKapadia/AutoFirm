# SUMMARY — CaMeL: Defeating Prompt Injections by Design

## Full citation
- **Title:** Defeating Prompt Injections by Design.
- **Authors:** Edoardo Debenedetti, Ilia Shumailov, Tianqi Fan, Jamie Hayes, Nicholas Carlini, Daniel Fabian, Christoph Kern, Chongyang Shi, Andreas Terzis, Florian Tramer.
- **Year:** 2025 (v1 submitted 24 Mar 2025; v2 24 Jun 2025).
- **Venue:** arXiv:2503.18813 (preprint); accepted to IEEE SaTML 2026 (Conf. on Secure and Trustworthy Machine Learning) per the project page. Code: https://github.com/google-research/camel-prompt-injection
- **URL:** https://arxiv.org/abs/2503.18813 · PDF (v2): https://arxiv.org/pdf/2503.18813 · project: https://floriantramer.com/publications/camel25/

## Questions informed
- **L1.A8.1** Untrusted-input handling (provable design-level defense).
- **L1.A8.3** Capability-based scoping / data-flow control over what an agent may do with a credentialed tool.

## GRADE tier
**Moderate->High.** arXiv preprint accepted at a peer-reviewed venue (SaTML 2026) — up-rated toward High for the design claim; corroborated by AgentDojo (#05) and #03.

## Key claims (with locators)
1. **Design (abstract, exact):** CaMeL "explicitly extracts the control and data flows from the (trusted) query; therefore, the untrusted data retrieved by the LLM can never impact the program flow." It "relies on a notion of a capability to prevent the exfiltration of private data over unauthorized data flows."
2. **Architecture:** a Privileged LLM (P-LLM) plans and emits code from the trusted user query; a Quarantined LLM (Q-LLM) parses/extracts from untrusted data only (no tool access). A custom Python interpreter executes the P-LLM code and enforces capabilities + security policies on every tool call — a hard technical boundary, not instruction-following. Capabilities tag each value with provenance/permission metadata so the interpreter can block disallowed data flows (e.g., private data -> public sink).
3. **Benchmark (exact):** CaMeL solves 67% of tasks with provable security in AgentDojo (NeurIPS 2024 benchmark).
4. **Limitations acknowledged:** requires writing explicit security policies per task domain (authoring burden); residual side-channel risks; coverage gaps against some multi-step/indirect attacks.

## Up/down-rate reasoning
- Up-rated: peer-reviewed venue acceptance; provable-security framing; open-source reference implementation (reproducible).
- Down-rated: finer interpreter mechanics only partially extractable from fetched excerpts — the 67% AgentDojo / capability / control-vs-data-flow claims are verified from the abstract + project page; interpreter internals should be re-read from the v2 PDF before quoting verbatim.

## Reproducibility note
The 67% figure and control/data-flow + capability framing are in the abstract (arXiv:2503.18813) and the project page; interpreter/capability mechanics are in the v2 PDF (cite section when quoting). Reference code public on GitHub.
