# SUMMARY — From Storage to Experience: A Survey on the Evolution of LLM Agent Memory Mechanisms

## Full citation
- **Title:** From Storage to Experience: A Survey on the Evolution of LLM Agent Memory Mechanisms
- **Authors:** Jinghao Luo, Yuchen Tian, Chuxue Cao, Ziyang Luo, Hongzhan Lin, Kaixin Li, Chuyi Kong, Ruichao Yang, Jing Ma
- **Year:** 2026 (submitted 2026-05-07)
- **Venue:** Accepted to ACL 2026 Findings; arXiv preprint
- **arXiv ID / URL:** arXiv:2605.06716 [cs.AI] — https://arxiv.org/abs/2605.06716
  (Note: the program seed file cited the Preprints.org mirror 202601.0618 — https://www.preprints.org/manuscript/202601.0618 — same work.)

## Questions informed
- **L1.A4.1** Agent-memory taxonomy (storage->reflection->experience).
- **L1.A4.3** Learning-over-time mechanisms (reflection, experience abstraction).

## Key claims (faithful)
1. **Three-stage evolution framework**, in the source's own terms:
   - **Storage = "trajectory preservation"** — raw interaction history is kept.
   - **Reflection = "trajectory refinement"** — stored trajectories are distilled/improved.
   - **Experience = "trajectory abstraction"** — higher-order, transferable knowledge abstracted across trajectories.
2. **Three core drivers** (exact): "the necessity for long-range consistency, the challenges in dynamic environments, and the ultimate goal of continual learning."
3. **Memory-Augmented Generation taxonomy — four memory structures:** (i) Lightweight Semantic, (ii) Entity-Centric and Personalized, (iii) Episodic and Reflective, (iv) Structured and Hierarchical.
4. **Two frontier (Experience-stage) mechanisms:** "proactive exploration and cross-trajectory abstraction." Exploration decomposes into breadth (curiosity), depth (high-order skill extraction), strategy (dynamic decision-path optimization).
5. Bridges OS-engineering and cognitive-science views of agent memory; offers design principles for next-generation agents.

## GRADE tier
- **Moderate**, up-rated toward High for taxonomy claims: arXiv preprint accepted to ACL 2026 Findings (peer-reviewed). It is a survey (secondary synthesis); numeric claims it relays are traced here to their primary papers (A-Mem, Generative Agents, Reflexion, ExpeL).

## Reproducibility note
Stage definitions and the four-structure taxonomy are stated in the abstract/intro and re-derivable at the arXiv URL above. No formulae in this source.
