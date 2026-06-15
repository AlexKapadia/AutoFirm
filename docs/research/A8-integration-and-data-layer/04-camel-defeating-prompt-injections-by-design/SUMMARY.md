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
3. **Benchmark (exact, v2 abstract):** CaMeL solves 77% of tasks with provable security in AgentDojo — compared to 84% with an undefended system (NeurIPS 2024 benchmark). (Prior "67%" came from a stale project page; the arXiv v2 abstract is the venue-bound primary and states 77% vs 84% undefended.)
4. **Limitations acknowledged:** requires writing explicit security policies per task domain (authoring burden); residual side-channel risks; coverage gaps against some multi-step/indirect attacks.

## Up/down-rate reasoning
- Up-rated: peer-reviewed venue acceptance; provable-security framing; open-source reference implementation (reproducible).
- Down-rated: finer interpreter mechanics only partially extractable from fetched excerpts — the 77%-vs-84%-undefended AgentDojo / capability / control-vs-data-flow claims are verified from the v2 abstract; interpreter internals should be re-read from the v2 PDF before quoting verbatim.

## Reproducibility note
The 77%-with-provable-security vs 84%-undefended figures and the control/data-flow + capability framing are in the **v2 abstract** (arXiv:2503.18813v2, verified by WebFetch 2026-06-15); the project page is **stale** (quotes 67%) and must not be cited for this number. Interpreter/capability mechanics are in the v2 PDF (cite section when quoting). Reference code public on GitHub.
- **Open item resolved:** the v2 abstract has been re-read (77% / 84%); the remaining re-verify step is the v2 PDF §3-4 interpreter internals before quoting those verbatim.
