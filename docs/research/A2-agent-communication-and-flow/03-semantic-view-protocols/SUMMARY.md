# SUMMARY — Beyond Message Passing: A Semantic View of Agent Communication Protocols

## Full citation
- **Title:** Beyond Message Passing: A Semantic View of Agent Communication Protocols
- **Authors:** Dun Yuan, Fuyuan Lyu, Ye Yuan, Weixu Zhang, Bowei He, Jiayi Geng, Linfeng Du,
  Zipeng Sun, Yankai Chen, Changjiang Han, Jikun Kang, Xi Chen, Haolun Wu, Xue Liu
- **Year:** 2026 (arXiv v3)
- **Venue:** arXiv preprint (cs.AI / cs.MA)
- **URL/DOI:** https://arxiv.org/pdf/2604.02369 (arXiv:2604.02369)

## Questions it informs
- **L1.A2.1** (message schemas — the semantic layer beyond syntax — PRIMARY for the gap)
- L1.A2.3 (standardization-of-meaning as coordination — supporting bridge)

## GRADE tier: Moderate
arXiv preprint with an analytical framework grounded in established linguistics (Grice 1975,
Clark 1996, Sperber & Wilson 1995). **Down-rate:** preprint; the detailed taxonomy tables were
not fully extractable from the PDF, so only the clearly-stated thesis-level claims are relied
upon here (the linguistic foundations are independently verifiable). **Up-rate:** consistent
with FIPA-ACL's speech-act semantics (source 04) and MAST's "intent/social-reasoning" gap
(source 02) — corroborated direction, not a lone claim.

## Key claims (faithful, thesis-level)

- **Core thesis:** current protocols (MCP, A2A, ACP) operate at the **syntactic level** —
  they define message *structure/format* — but lack **semantic grounding**; effective
  interoperability needs "shared meaning, intent, and ontological alignment beyond mere message
  passing." The title's "Beyond Message Passing" signals syntactic format is insufficient.

- **Three identified gaps in syntactic protocols:**
  1. **No shared ontology** — no agreed conceptual framework for what domain terms mean across
     heterogeneous agents.
  2. **Intent opacity** — agents cannot reliably infer communicative intent / pragmatic
     expectation from message content alone.
  3. **Contextual grounding** — without semantic anchoring, agents cannot resolve ambiguity or
     ground abstract references in shared context.

- **Recommended directions for semantic interoperability:**
  1. **Explicit semantic contracts** — agents declare/negotiate shared meaning before
     interaction.
  2. **Ontology alignment** — standardize domain vocabularies and concept definitions.
  3. **Pragmatic layers** — model communicative *intent*, not just content.

- **Linguistic foundations cited:** Grice (1975) conversational implicature; Clark (1996)
  communication as collaborative grounding; Sperber & Wilson (1995) relevance theory. (These
  are the same speech-act / pragmatics lineage underpinning FIPA-ACL — source 04.)

## Reproducibility note
Thesis and the three gaps are stated in the abstract/intro and the linguistic citations are
independently verifiable primary works. Any quantitative dimension table (referenced as
"table.caption.23") must be re-extracted from the paper PDF before being relied upon; it is NOT
used as a load-bearing claim here.
