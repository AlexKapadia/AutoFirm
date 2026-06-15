# SUMMARY — Reflexion: Language Agents with Verbal Reinforcement Learning

## Full citation
- **Title:** Reflexion: Language Agents with Verbal Reinforcement Learning
- **Authors:** Noah Shinn, Federico Cassano, Edward Berman, Ashwin Gopinath, Karthik Narasimhan, Shunyu Yao
- **Year:** 2023
- **Venue:** Advances in Neural Information Processing Systems (NeurIPS 2023), peer-reviewed
- **arXiv ID / URL:** arXiv:2303.11366 — https://arxiv.org/abs/2303.11366 ; NeurIPS proceedings PDF: https://proceedings.neurips.cc/paper_files/paper/2023/file/1b44b878bb782e6954cd888628510e90-Paper-Conference.pdf

## Questions informed
- **L1.A4.3** Learning-over-time mechanisms (reflection; RL-on-memory WITHOUT weight updates).

## Key claims (faithful)
1. **Verbal reinforcement learning.** The agent improves NOT by updating weights but by generating
   **linguistic self-reflections** on task feedback and storing them in an **episodic memory buffer**
   to improve subsequent trials.
2. **Three components:**
   - **Actor (M_a)** — LLM that generates actions/text from state, conditioned on short-term
     trajectory + long-term memory (uses CoT/ReAct).
   - **Evaluator (M_e)** — scores the Actor's output (exact-match for reasoning, heuristics for
     decisions, or an LLM binary classifier).
   - **Self-Reflection (M_sr)** — converts the sparse reward into detailed verbal feedback stored for future trials.
3. **Memory:** short-term (current trajectory) + long-term (distilled reflections), bounded to ~1-3
   stored experiences to respect context limits.

## Empirical results (exact)
- **HumanEval (Python) pass@1 = 91.0%**, surpassing the prior SOTA GPT-4 at **80.1%**.
- **ALFWorld: 130/134 tasks completed, a 22% absolute improvement** over a ReAct baseline (over 12 learning steps).
- **HotpotQA: 20% improvement** on reasoning, using episodic memory + self-reflection.

## GRADE tier
- **High.** Peer-reviewed NeurIPS 2023; canonical source for no-gradient, memory-based self-improvement.

## Reproducibility note
The 91.0% / 80.1% HumanEval, 130/134 (22%) ALFWorld, and 20% HotpotQA figures and the
Actor/Evaluator/Self-Reflection architecture are from the paper's results and method sections;
open-source code (github.com/noahshinn/reflexion) enables replication.
