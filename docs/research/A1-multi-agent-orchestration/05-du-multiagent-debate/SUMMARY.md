# SUMMARY — Improving Factuality and Reasoning in Language Models through Multiagent Debate

## Full citation
- **Title:** Improving Factuality and Reasoning in Language Models through Multiagent Debate
- **Authors:** Yilun Du (MIT CSAIL), Shuang Li (MIT CSAIL), Antonio Torralba (MIT CSAIL),
  Joshua B. Tenenbaum (MIT CSAIL/BCS/CBMM), Igor Mordatch (Google Brain)
- **Year:** 2023 (arXiv 23 May 2023); published **ICML 2024**.
- **Venue:** Proceedings of the 41st International Conference on Machine Learning (ICML 2024);
  preprint arXiv:2305.14325. Peer-reviewed.
- **URL/DOI:** https://arxiv.org/abs/2305.14325 ; ICML: https://dl.acm.org/doi/10.5555/3692070.3692537 ;
  OpenReview: https://openreview.net/pdf?id=zj7YuTE4t8 ; site: https://composable-models.github.io/llm_debate/

## Questions informed
- **L1.A1.1** (debate as a coordination pattern) — PRIMARY exemplar.
- **L1.A1.2** (multi-agent beats single) — PRIMARY (peer-reviewed evidence).
- L1.A1.4 (cost of the pattern) — supporting (compute expense, context-length limit).

## GRADE tier
**High.** Peer-reviewed ICML 2024, multiple tasks, ablations on agents and rounds, public code/site.
The canonical primary source for the "debate / society-of-minds" coordination pattern.

## Method (faithful)
- "multiple language model instances propose and debate their individual responses and reasoning
  processes over multiple rounds to arrive at a common final answer." Inspired by Minsky's
  *Society of Mind*.
- Procedure: each agent first answers independently; then each agent receives the **concatenated**
  responses of all other agents (a "consensus prompt") and updates its answer; repeated over rounds.
- Main experiments: **3 agents, 2 rounds** ("Due to computational expense"). Tasks (six): arithmetic,
  grade-school math (GSM8K), chess move prediction/validity, biographies (new factuality benchmark),
  MMLU, and a chess-move-optimality (pawn score via Stockfish) task.
- Baselines: single agent; single agent + reflection; multi-agent majority vote; multi-agent debate.

## Key findings (faithful)
- Debate "gives a substantial boost in reasoning across each of the tasks," outperforming single-agent
  zero-shot CoT and reflection on all six tasks (Table 1 reasoning, Table 2 factuality — exact bar
  values are in figures/tables not text-extractable from the PDF; the directional results and
  rankings are stated in text). Reflection gives only "a modest boost"; debate (≈ reflection +
  multi-agent generation) gives the largest gain.
- **Scaling:** "On arithmetic, performance monotonically increases with the increased number of
  agents." Increasing rounds also "monotonically increases" performance, but "additional debate
  rounds above four led to a similar final performance to 4 rounds" (diminishing returns ~4 rounds).
- **Mixed-model debate (chatGPT + Bard, 20 GSM8K problems):** Bard alone solved 11, chatGPT alone 14,
  joint debate **17/20** — debate raised both.
- **Convergence:** "debate can be seen as a multi-agent game, where convergence is not guaranteed";
  empirically models converge. "Stubborn" prompts (trust own answer more) → longer debates and better
  final solutions; instruction-tuned models are "relatively agreeable."
- **Error correction:** debate is not mere amplification — "many cases where all the models initially
  make incorrect predictions, but then arrive at the correct answer as debate progresses."

## Limitations (faithful)
- Compute expense (why only 3 agents/2 rounds in mains). For many agents, responses must be
  **summarized** rather than concatenated "due to context length error" — a coordination-cost /
  context-flooding signal (feeds L1.A1.4).

## Reproducibility note
Method, scaling behavior, mixed-model 11/14/17 result, and convergence/cost caveats extracted via
pdftotext. Bar-chart numeric values live in figures (not OCR-able from text layer); the *rankings*
and *monotonicity* claims are stated in prose and are what AutoFirm relies on.
