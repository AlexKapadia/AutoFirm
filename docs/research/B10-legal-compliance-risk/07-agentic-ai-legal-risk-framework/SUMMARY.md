# SUMMARY — Managing the legal risks of agentic AI (professional risk framework)

## Full citations
- **Squire Patton Boggs (2025).** *The Agentic AI Revolution: Managing Legal Risks.* SPB Publications.
  URL: https://www.squirepattonboggs.com/insights/publications/the-agentic-ai-revolution-managing-legal-risks/
- **Kolt, N. (2025).** *Governing AI Agents.* arXiv:2501.07913. (Scholarly legal/governance analysis;
  corroborating primary-adjacent source.) URL: https://arxiv.org/pdf/2501.07913
- **Jones Walker LLP (2025).** *AI Vendor Liability Squeeze: Courts Expand Accountability While Contracts
  Shift Risk.* (Corroborating professional source on liability allocation.)
  URL: https://www.joneswalker.com/en/insights/blogs/ai-law-blog/

## Ontology questions informed
- **L1.B10.1** — the **risk** leg (the legal risk taxonomy + mitigations for deploying autonomous
  agents). Feeds **L2.B10** (risk register), **L2.A7** (safety stack), and is the legal counterpart to
  CLAUDE.md §5.6.

## GRADE tier
- **Moderate-High.** Squire Patton Boggs and Jones Walker are major international law firms (professional
  primary analysis of current law); Kolt's *Governing AI Agents* is a scholarly arXiv paper. These are
  **practitioner/scholarly secondary** on a fast-moving area — corroborated across three independent
  firms/authors, so the **risk taxonomy** claim is well-supported (≥3 independent). Specific regulatory
  details are cross-checked against source 08 (EU AI Act primary text).

## Key claims (with locators)
1. **Five legal-risk categories for agentic AI** (Squire Patton Boggs): **(1) Regulatory compliance**
   (fragmented global frameworks — EU AI Act, US state law, UK sector law); **(2) Contractual liability**
   (unauthorized contract execution, breach of third-party usage restrictions); **(3) Tortious
   liability** (negligence, nuisance for autonomous harm); **(4) Data-security risks** (data leakage,
   poisoning, model inversion, adversarial attacks); **(5) IP disputes** (infringement + unresolved
   ownership of AI-generated works).
2. **Liability attaches to humans/organizations, not the AI** (Squire Patton Boggs; Kolt; Jones Walker):
   AI agents are **not legal persons**; harms are channeled through existing doctrines — **product
   liability, negligence, and agency** — onto **developers and deployers.**
3. **Recommended controls** (Squire Patton Boggs, verbatim): *"Appoint a senior person with
   responsibility for oversight of AI governance"*; *"Ensure that a human manager is responsible for the
   supervision and oversight of AI systems"* (human sign-off on material decisions); *"Build guardrails
   into AI systems by design, including clearly defined decision perimeters"*; *"Maintain detailed logs
   of decisions made in the AI's inferencing layer"*; *"Ensure that automated circuit breakers/kill
   switches are built into AI systems"*; *"Implement processes and procedures via which individuals may
   contest AI outcomes"*; and consider **specific AI-risk insurance**.
4. **Contracts shift risk but courts expand accountability** (Jones Walker): vendor contracts attempt to
   disclaim liability, yet courts are increasingly willing to hold AI deployers/vendors accountable —
   contractual risk-shifting is **not a complete shield.**

## Corroboration
- The "deployer is accountable" + "human oversight, kill-switch, audit logs, contestability" cluster is
  corroborated independently by Squire Patton Boggs, Kolt (*Governing AI Agents*), and Jones Walker, and
  aligns with the EU AI Act high-risk obligations (source 08) — strong multi-source agreement.

## Reproducibility note
A reviewer re-derives the five-category taxonomy and the seven controls from the SPB publication
(quoted verbatim above); the deployer-liability conclusion is cross-checked against Kolt and the EU AI
Act provider/deployer obligations (source 08).
