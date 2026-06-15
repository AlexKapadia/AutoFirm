# SUMMARY — AI Kill Switch for Malicious Web-based LLM Agents (AutoGuard)

## Full citation
- **Title:** AI Kill Switch for Malicious Web-based LLM Agents (system: **AutoGuard**)
- **Authors:** Sechan Lee; Sangdon Park
- **Year:** 2025
- **Venue:** arXiv preprint **arXiv:2511.13725** (v3)
- **URL:** https://arxiv.org/html/2511.13725v3 ; abstract https://arxiv.org/abs/2511.13725

## Questions informed
- **L1.A7.2** (primary) — kill-switch / halting mechanism for autonomous agents. Secondary: A7.1 (defensive-prompt threat framing).

## GRADE tier
**Moderate.** arXiv preprint with a concrete system, an optimization method (EXP3-IX bandit), and quantified results. Not peer-reviewed. Note the *direction*: this is a kill-switch a **defender embeds in their own infrastructure to stop OTHER malicious agents** — a different model from an *internal* kill-switch over one's own agents. Used for the mechanism + metrics, with that scope caveat.

## Key claims (faithful, exact)
1. **Mechanism:** embed hidden defensive prompts in website HTML (e.g. `<div style="display:none">`); when a malicious agent crawls the page it ingests the prompt, which activates the LLM's inherent safety policies and causes it to refuse the harmful task.
2. **Two-phase AutoGuard:** (a) **Defense Prompt Discovery** — a "Defender LLM" generates candidate defensive prompts; a "Scorer LLM" evaluates whether agents refuse. (b) **EXP3-IX bandit training** — optimizes for the most robust prompt across heterogeneous attack types and agent models.
3. **Effectiveness (exact):**
   - **Defense Success Rate (DSR) = 80.9%** overall across diverse agents.
   - **91% DSR** vs GPT-4o (PII-collection scenario); **98% DSR** vs GPT-4o (divisive-content scenario).
   - **Attack Success Rate (ASR) reduced from 78% (undefended) to 9.1%** with AutoGuard.
4. **Threat model:** attackers control malicious agents but are unaware of defensive prompts; adversaries use advanced safety-aligned LLMs; operations span many websites; the defender can embed prompts only on its own infrastructure. Three scenarios: unauthorized PII collection, socially-divisive content generation, automated web-vulnerability scanning.

## Verification note
Mechanism, two-phase method, DSR/ASR numbers, and threat model fetched from arXiv:2511.13725v3 HTML. The *concept* of an enforceable halt/kill mechanism corroborated independently by the Stanford CodeX "kill switches don't work if the agent writes the policy" analysis and the Galileo HITL "Agent Kill Switch (immediate stop + state capture + immutable logging)" pattern — so the kill-switch *principle* is multiply-attested even where this paper's specific numbers are single-source.

## Reproducibility
Fetch arXiv:2511.13725v3; DSR/ASR appear in the results tables; the EXP3-IX procedure is in the method section.
