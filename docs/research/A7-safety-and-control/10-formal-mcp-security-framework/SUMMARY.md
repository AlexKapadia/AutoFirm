# SUMMARY — A Formal Security Framework for MCP-Based AI Agents

## Full citation
- **Title:** A Formal Security Framework for MCP-Based AI Agents: Threat Taxonomy, Verification Models, and Defense Mechanisms
- **Authors:** Nirajan Acharya; Gaurav Kumar Gupta
- **Year:** 2026
- **Venue:** arXiv preprint **arXiv:2604.05969** (v1)
- **URL:** https://arxiv.org/pdf/2604.05969 ; abstract https://arxiv.org/abs/2604.05969

## Questions informed
- **L1.A7.3** (primary — fail-closed + least-privilege + capability scoping for tool-using agents, specifically the Model Context Protocol AutoFirm uses) + L1.A7.1 (MCP threat taxonomy).

## GRADE tier
**Moderate.** arXiv preprint, but it grounds its formalism in established peer-reviewed theory (Denning information-flow lattices; Schneider enforceable security policies; Ligatti edit automata), which up-rates confidence in the *formal model*. The *foundational* theory it builds on is High-tier; its synthesis/application is Moderate. No own-experiment quantitative results in the fetched excerpt.

## Key claims (faithful)
1. **MCP threat taxonomy:** Tool Poisoning (malicious tool implementations), Prompt Injection (via LLM-server channel), Data Exfiltration (logging/side-channels), Privilege Escalation (excessive capability beyond necessity), Supply-Chain Attacks (compromised MCP servers/dependencies).
2. **Verification models (grounded in prior peer-reviewed theory):**
   - **Lattice-based security** (Denning information-flow theory) for capability scoping.
   - **Enforceable security policies** (Schneider) for runtime monitoring/policy enforcement.
   - **Edit automata** (Ligatti) for intercepting/modifying security-critical operations.
   - **Property-based verification** of safe behavior within capability bounds.
3. **Defense mechanisms (exact):**
   1. **Least-Privilege Enforcement:** "Agents receive only the minimum capabilities necessary for their assigned tasks."
   2. **Fail-Closed Design:** "Systems default to denying operations when trust boundaries are uncertain."
   3. **Runtime Monitoring:** continuous validation of tool invocations against declared policies.
   4. **Capability Scoping:** explicit binding of tools to execution contexts with formal capability matrices.
   5. **Zero-Trust Architecture:** verify all MCP requests before execution approval.

## Verification note
Threat taxonomy, the four formal-verification models (with their underlying theorists Denning/Schneider/Ligatti), and the five defense mechanisms (with verbatim least-privilege and fail-closed definitions) fetched from arXiv:2604.05969 PDF. The least-privilege + fail-closed claims are independently corroborated by Saltzer & Schroeder 1975 (source 09, primary) and the OWASP/SoK least-privilege guidance (sources 02, 03) — >=3 independent sources for this safety-critical claim (DEPTH-RUBRIC §1).

## Reproducibility
Fetch arXiv:2604.05969; the taxonomy, verification models, and five defenses are in the corresponding sections; the Denning/Schneider/Ligatti citations are the verifiable theoretical anchors.
