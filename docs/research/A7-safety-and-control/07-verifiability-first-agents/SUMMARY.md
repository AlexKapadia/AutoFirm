# SUMMARY — Verifiability-First Agents

## Full citation
- **Title:** Verifiability-First Agents: Provable Observability and Lightweight Audit Agents for Controlling Autonomous LLM Systems
- **Author:** Abhivansh Gupta
- **Year:** 2025 (submitted 2025-12-19)
- **Venue:** arXiv preprint **arXiv:2512.17259**
- **URL:** https://arxiv.org/abs/2512.17259 ; PDF https://arxiv.org/pdf/2512.17259

## Questions informed
- **L1.A7.2** (primary) — oversight architectures (audit agents, verifiability-first, detect-and-remediate).

## GRADE tier
**Moderate (lean Low for sole numeric claims).** Single-author arXiv preprint with a clear architecture + a proposed benchmark (OPERA) but no peer review. Used for the **architectural concept** (verifiability-first, audit agents), NOT as a sole basis for any quantitative claim; corroborated by the HITL/oversight literature (sources 02 #5, governance refs) and the kill-switch paper (source 08).

## Key claims (faithful)
1. **Thesis / paradigm shift:** prioritize *detection and remediation* of misalignment over *prevention alone* — measure "how quickly and reliably misalignment can be detected and remediated," not just "how likely misalignment is."
2. **Verifiability-First Architecture — three components:**
   - **Runtime attestations** using cryptographic and symbolic methods to verify agent actions.
   - **Lightweight Audit Agents** using constrained reasoning to continuously compare *intended vs actual* behavior.
   - **Challenge-response protocols** for high-risk operations requiring extra verification.
3. **OPERA benchmark** (Observability, Provable Execution, Red-team, Attestation): measures detection capability for misaligned behavior, **time-to-detection under stealthy attack**, and resilience to adversarial prompt injection / persona manipulation.

## Verification note
Title, sole author, three architectural components, and the OPERA acronym fetched from the arXiv abstract (2512.17259). The PDF text stream was non-extractable (compressed), so claims are taken from the abstract only and explicitly scoped to it. The *concept* (audit agents comparing intended vs actual behavior; tamper-evident attestation) independently corroborated by the HITL/delegation-chain governance literature (Stanford CodeX / Galileo oversight patterns) and source 08 — so the architectural pattern is multiply-attested even though this preprint is a single source.

## Reproducibility
Open arXiv:2512.17259 abstract; the three components + OPERA are stated there. Treat detailed numbers as unverified until the full PDF is read.
