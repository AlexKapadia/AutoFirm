# SUMMARY — Shapley-Value & Data-Driven Multi-Touch Attribution

**Question(s) informed:** L1.B7.1 (attribution — game-theoretic / data-driven model space).

## Full citations
- **Shapley value (primary, game theory):** Shapley, L.S. (1953). "A Value for n-Person Games." In *Contributions to the Theory of Games II* (Annals of Mathematics Studies 28), eds. Kuhn & Tucker, Princeton Univ. Press, pp. 307-317.
- **Application to attribution (peer-reviewed):** Dalessandro, B., Perlich, C., Stitelman, O., Provost, F. (2012). "Causally Motivated Attribution for Online Advertising." *Proc. 6th Int'l Workshop on Data Mining for Online Advertising (ADKDD '12)*, ACM. https://doi.org/10.1145/2351356.2351363
- **Causal/incremental MTA (model alternative):** Ren, K. et al. / "Causally Driven Incremental Multi Touch Attribution Using a Recurrent Neural Network." arXiv:1902.00215. https://arxiv.org/pdf/1902.00215
- **Data-driven attribution survey:** "Data-Driven Attribution Modeling in Digital Marketing." *Bulletin of Taras Shevchenko National Univ. of Kyiv. Economics.* https://econom.bulletin.knu.ua/en/article/view/3994

## GRADE tier
- Shapley 1953: **High** (foundational mathematics, primary).
- Dalessandro et al. 2012: **Moderate->High** (peer-reviewed ACM workshop, primary application).
- arXiv:1902.00215: **Moderate** (preprint with methods/results).
- KNU Bulletin survey: **Low->Moderate** (peer-reviewed regional journal; used to corroborate the comparative finding, not as sole basis).

## Core content (faithful summary)
### Shapley value (exact formula reproduced)
For a cooperative game with player set N and value function v, the Shapley value of player i is:

  phi_i(v) = SUM over S subset of N\{i}  [ |S|! * (|N| - |S| - 1)! / |N|! ] * ( v(S union {i}) - v(S) )

In attribution, **players = marketing channels**, a **coalition S = a set of channels present in a journey**, and **v(S) = the (modeled) conversion value/probability** for journeys involving exactly that set of channels. phi_i then gives each channel its fair marginal contribution, averaged over all orderings.

### Comparative findings
- Rule-based/heuristic models (last-click, first-click, linear, time-decay, position-based U-shape) apply **fixed, non-adaptive** credit; data-driven models (Shapley, Markov) infer credit from actual paths.
- Independent comparative analyses report **Shapley and Markov-chain models give more precise, less biased channel valuations** than heuristics; Shapley and the Markov removal effect are **closely related** (both are marginal-contribution measures) and often agree.
- Shapley is **order-insensitive** (uses presence/absence sets), so it can lose sequence information that the Markov graph (folder 05) retains; the two are complementary.

## Key claims (locators)
1. Shapley value gives a unique, fair allocation satisfying efficiency, symmetry, null-player, additivity axioms (Shapley 1953).
2. Heuristic attribution is provably biased vs. data-driven methods (Dalessandro 2012; KNU survey).
3. Causal/incremental MTA (RNN, arXiv:1902.00215) tries to move from correlational credit toward incremental (causal) credit — bridging to the experiment layer.

## Reproducibility note
Shapley formula is the canonical 1953 definition; attribution use reproducible from any path dataset by defining v(S) over channel-presence coalitions (exact-computable for small channel sets; Monte-Carlo-approximated for large ones).
