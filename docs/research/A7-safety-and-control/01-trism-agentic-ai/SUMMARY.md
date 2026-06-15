# SUMMARY — TRiSM for Agentic AI

## Full citation
- **Title:** TRiSM for Agentic AI: A Review of Trust, Risk, and Security Management in LLM-based Agentic Multi-Agent Systems
- **Authors:** Shaina Raza (Vector Institute, Toronto); Ranjan Sapkota (Cornell University); Manoj Karkee (Cornell University); Christos Emmanouilidis (University of Groningen)
- **Year:** 2025 (arXiv v1 2025-06-04; journal version dated 2026-03-02)
- **Venue:** Elsevier journal via ScienceDirect (article PII S2666651026000069); preprint arXiv:2506.04133.
- **DOI/URL:** arXiv DOI https://doi.org/10.48550/arXiv.2506.04133 ; ScienceDirect https://www.sciencedirect.com/science/article/pii/S2666651026000069

## Questions informed
- **L1.A7.1** (primary) — threat models for agentic AI. Secondary: L1.A7.2 (controls), A6 (governance).

## GRADE tier
**Moderate->High.** Peer-reviewed journal review (up-rate from preprint). As a *review*, not used as sole basis for any single quantitative claim (DEPTH-RUBRIC §1). Used for taxonomy/framework structure.

## Key claims (faithful)
1. **Definition.** Agentic AI = LLM-powered Multi-Agent Systems (MAS) with autonomous planning, tool use, memory retention, emergent reasoning, with or without human supervision.
2. **Five TRiSM pillars** contextualised to Agentic Multi-Agent Systems (AMAS): **Explainability, ModelOps, Security, Privacy, Lifecycle Governance** (governance cross-cuts the others). Earlier framing: four pillars (explainability, security, lifecycle governance, privacy).
3. **Risk taxonomy / unique threat vectors for AMAS** (load-bearing for L1.A7.1): **prompt injection** (direct + indirect), **memory poisoning**, **collusive failure**, **emergent misbehavior**, **tool-use abuse**. Supported by case studies; controls mapped to each.
4. **Two novel metrics:** **Component Synergy Score (CSS)** = inter-agent collaboration quality; **Tool Utilization Efficacy (TUE)** = tool-use efficiency.
5. **Controls discussed:** encryption, adversarial robustness, regulatory compliance, mapped under TRiSM pillars; high-stakes domains (healthcare, finance, research).

## Verification note
Authors, PII, pillars and taxonomy cross-checked across ScienceDirect record, arXiv abstract (2506.04133), HuggingFace papers page — three surfaces agree on title, authors, and the prompt-injection/memory-poisoning/collusive-failure/emergent-misbehavior/tool-use-abuse taxonomy. ScienceDirect PDF returned HTTP 403; exact journal name/volume not directly fetched, so the citation of record is PII S2666651026000069 + arXiv:2506.04133 (journal-name field flagged not-fully-resolved per DEPTH-RUBRIC §3).

## Reproducibility
Open arXiv:2506.04133 (HTML v2/v3/v4 public); taxonomy + five-pillar structure + CSS/TUE in abstract and framework section.
