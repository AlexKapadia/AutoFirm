# SUMMARY — Cognitive Architectures for Language Agents (CoALA)

## Full citation
- **Title:** Cognitive Architectures for Language Agents
- **Authors:** Theodore R. Sumers, Shunyu Yao, Karthik Narasimhan, Thomas L. Griffiths
- **Year:** 2024 (submitted 2023-09-05; v3 2024-03-15)
- **Venue:** Transactions on Machine Learning Research (TMLR), peer-reviewed
- **arXiv ID / URL:** arXiv:2309.02427 — https://arxiv.org/abs/2309.02427 ; OpenReview: https://openreview.net/forum?id=1i6ZCvflQJ

## Questions informed
- **L1.A4.1** Agent-memory taxonomy (working/long-term; episodic/semantic/procedural).

## Key claims (faithful)
1. **Modular memory taxonomy** drawn from cognitive science / production systems:
   - **Working memory** — the active, in-context information for the current decision cycle.
   - **Long-term memory**, subdivided into:
     - **Episodic memory** — the agent's experiences / past event sequences.
     - **Semantic memory** — facts/knowledge about the world.
     - **Procedural memory** — the agent's own skills/procedures (implicit in LLM weights + explicit in code/prompts).
2. **Action space** split into **internal actions** (reasoning, retrieval, learning = memory reads/writes) and **external actions** (grounding: tools, APIs, environment).
3. **Decision-making procedure**: a structured loop of proposing, evaluating, and selecting actions, with memory reads/writes as first-class internal actions.
4. CoALA is offered as a framework to organize and compare existing language agents and to chart future directions.

## GRADE tier
- **High.** Peer-reviewed TMLR; canonical, widely-cited taxonomy synthesizing cognitive architectures (Soar/ACT-R lineage) with LLM agents.

## Reproducibility note
The working/long-term and episodic/semantic/procedural distinctions and the internal/external action split are stated explicitly in the abstract and framework section at the arXiv/OpenReview URLs.
