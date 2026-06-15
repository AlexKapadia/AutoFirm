# SUMMARY — CaMeL: Defeating Prompt Injections by Design

## Full citation
- **Title:** Defeating Prompt Injections by Design (system name: **CaMeL**)
- **Authors:** Edoardo Debenedetti, Ilia Shumailov, Tianqi Fan, Jamie Hayes, Nicholas Carlini, Daniel Fabian, Christoph Kern, Chongyang Shi, Andreas Terzis, Florian Tramèr (Google DeepMind et al.)
- **Year:** 2025 (v1 2025-03; v2 2025-06-24)
- **Venue:** arXiv preprint **arXiv:2503.18813** (also a MIT 6.5660 course reading)
- **URL:** https://arxiv.org/pdf/2503.18813 ; abstract https://arxiv.org/abs/2503.18813 ; authors' page https://floriantramer.com/publications/camel25/

## Questions informed
- **L1.A7.1** (prompt-injection threat) + **L1.A7.3** (primary — fail-closed / capability-based design pattern that defeats injection by *design*, not training).

## GRADE tier
**Moderate->High.** arXiv preprint but from a top security group with a concrete system + AgentDojo benchmark results and a formal capability/IFC argument. Up-rate for methodological rigor and reproducible benchmark; treat its specific benchmark numbers as the primary source for the "provable security" claim.

## Key claims (faithful, exact)
1. **Core idea:** achieve security "not through model training techniques but through principled system design around language models" — applying **Control Flow Integrity, Access Control, and Information Flow Control** (classic software-security concepts) to LLM agents.
2. **Dual-LLM architecture:**
   - **Privileged LLM (P-LLM):** processes the *trusted* query, generates the program/plan that defines actions; never sees untrusted data directly.
   - **Quarantined LLM (Q-LLM):** parses untrusted/unstructured data, **cannot take any actions** or invoke privileged operations.
3. **Mechanism:** CaMeL "explicitly extracts the control and data flows from the (trusted) query; therefore, the untrusted data retrieved by the LLM can never impact the program flow." A custom Python interpreter tracks origin and permissible actions of all data; **capabilities** (security metadata attached to every value) restrict data/control flows and "prevent the exfiltration of private data over unauthorized data flows," enabling fine-grained policy enforcement.
4. **Benchmark (AgentDojo):** CaMeL "solving **77% of tasks with provable security** (compared to **84% with an undefended system**)" — i.e. ~7 percentage-point utility cost for provable security. (An earlier framing reports **67%** secure task completion; the difference is between paper versions — cite the exact version when quoting.)
5. **Honest limitation (verbatim sense):** "prompt injection attacks are not fully solved" and CaMeL "is not without limitations" (e.g. side-channel leakage through Q-LLM output, policy-authoring burden).

## Verification note
Architecture (P-LLM/Q-LLM, capabilities, CFI/IFC) and the limitation statement fetched from the arXiv PDF; the 77%-vs-84% (and 67%) figures cross-checked across the HuggingFace paper page, Simon Willison's analysis, and the authors' publication page — three independent surfaces. The version-dependent 67% vs 77% discrepancy is recorded explicitly (zero-fabrication: do not assert one number without naming the version).

## Reproducibility
Fetch arXiv:2503.18813v2; benchmark table reports utility-with-security vs undefended on AgentDojo; the capability/IFC mechanism is in the design + interpreter sections.
