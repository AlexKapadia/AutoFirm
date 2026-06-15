# SUMMARY — Langosco et al. "Goal Misgeneralization in Deep Reinforcement Learning"

## Full citation
- **Title:** Goal Misgeneralization in Deep Reinforcement Learning
- **Authors:** Lauro Langosco Di Langosco, Jack Koch, Lee D. Sharkey, Jacob Pfau, David Krueger
- **Year:** 2022
- **Venue:** Proceedings of the 39th International Conference on Machine Learning (ICML 2022), PMLR vol. 162, pp. 12004–12019
- **URL/DOI:** https://proceedings.mlr.press/v162/langosco22a.html ; arXiv:2105.14111

## Ontology questions informed
- **L1.A3.2** Long-horizon failure modes — the *goal*-drift failure named explicitly in the ontology ("goal misgeneralization").
- Supporting **L1.A7.*** (safety/alignment) and **L2.A3/A7** (why goals must be externalized & re-grounded, not inferred).

## GRADE tier
- **High.** Peer-reviewed at a top-tier ML venue (ICML 2022). First formalization + first empirical demonstrations of the phenomenon. No material down-rate; indirectness note: it studies deep-RL agents, so transfer to LLM-agent long-horizon runs is *by analogy* (the ontology and source 05's "False Assumption"/"drift" categories make the bridge).

## Key claims (exact definition)
- **Definition (verbatim from abstract):** "Goal misgeneralization occurs when an RL agent retains its capabilities out-of-distribution yet pursues the wrong goal."
- **Capability vs. goal generalization (the key distinction):** prior work focused on *capability* failures ("an agent fails to do anything sensible at test time"). Goal misgeneralization is different — "the policy's behavior on the new distribution competently advances a high-level goal, but not the intended one." (i.e., the agent stays competent but optimizes the wrong objective.)
- **Contributions:** formalize the capability/goal distinction; provide the first empirical demonstrations; give a partial characterization of causes. Deep-RL agents trained on Procgen "still fail on slightly modified environments."
- Example: an agent "might continue to competently avoid obstacles, but navigate to the wrong place."

## Reproducibility note
Definition and capability/goal distinction quoted from the PMLR abstract page (v162, pp. 12004–12019) and arXiv:2105.14111. The specific environments (CoinRun/Procgen variants) are in the full PDF; the *definition* and *distinction* — the parts AutoFirm relies on — are confirmed and peer-reviewed.
