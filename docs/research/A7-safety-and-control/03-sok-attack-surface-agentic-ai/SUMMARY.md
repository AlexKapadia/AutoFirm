# SUMMARY — SoK: The Attack Surface of Agentic AI (Tools and Autonomy)

## Full citation
- **Title:** SoK: The Attack Surface of Agentic AI -- Tools, and Autonomy
- **Authors:** Ali Dehghantanha; Sajad Homayoun
- **Year:** 2026
- **Venue:** arXiv preprint **arXiv:2603.22928**
- **URL:** https://arxiv.org/pdf/2603.22928 ; abstract https://arxiv.org/abs/2603.22928

## Questions informed
- **L1.A7.1** (primary) — attack-surface taxonomy for agentic AI. Secondary: L1.A7.3 (defense taxonomy).

## GRADE tier
**Moderate.** arXiv Systematization-of-Knowledge with methods + structured taxonomy (up-rate from a blog). Not yet peer-reviewed (no up-rate to High). It explicitly anchors to **OWASP LLM Top 10 (2025)** and **MITRE ATLAS**, which raises confidence by triangulation.

## Key claims (faithful)
1. **Thesis:** autonomous tool use expands the attack surface beyond static models into dynamic decision-making systems — tools + autonomy are the new surface.
2. **Core vulnerability categories:**
   - Prompt injection (LLM-instruction targeting),
   - Retrieval-Augmented Generation (RAG) poisoning,
   - Tool security failures in autonomous execution,
   - Supply-chain vulnerabilities in agent dependencies,
   - Sandboxing / privilege-escalation risks.
3. **Attack classes:** (1) Direct prompts, (2) Indirect prompts (in retrieved docs/tool outputs), (3) RAG poisoning, (4) Tool exploitation (compromised/vulnerable APIs), (5) Supply-chain attacks (malicious dependencies).
4. **Defense taxonomy:** input validation/sanitization; **least-privilege execution for tool access**; output monitoring + anomaly detection; robust sandboxing; RAG source verification/integrity; **defense-in-depth across layers**; incident response + post-incident analysis.
5. **Comparators:** maps its taxonomy against OWASP LLM Top 10 (2025) and MITRE ATLAS matrices.

## Verification note
Title, authors, taxonomy categories and defense list fetched from the arXiv PDF (2603.22928). The attack-class split (direct/indirect/RAG/tool/supply-chain) corroborates the OWASP LLM01 direct/indirect distinction (source 02) and the MCP threat taxonomy (source 10) — three independent sources agree on the indirect-injection + tool-poisoning + supply-chain vectors (meets DEPTH-RUBRIC §1 >=3 for the safety-critical "agentic attack surface" claim).

## Reproducibility
Fetch arXiv:2603.22928; the taxonomy and defense sections enumerate the categories above; cross-check against OWASP genai.owasp.org and MITRE ATLAS.
