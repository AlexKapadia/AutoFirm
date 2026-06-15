# SUMMARY — Artificial Intelligence, Algorithmic Pricing, and Collusion (Calvano et al.)

## Full citation
- **Primary:** Calvano, E., Calzolari, G., Denicolo, V. & Pastorello, S. (2020). "Artificial
  Intelligence, Algorithmic Pricing, and Collusion." *American Economic Review* 110(10), 3267-3297.
  DOI: 10.1257/aer.20190623. https://www.aeaweb.org/articles?id=10.1257/aer.20190623
- **Corroborating (LLM pricing agents):** Fish, S., Gonczarowski, Y. A. & Shorrer, R. I. (2024).
  "Algorithmic Collusion by Large Language Models." arXiv:2404.00806.
  https://arxiv.org/pdf/2404.00806
- **Corroborating (deep RL):** "By Fair Means or Foul: Quantifying Collusion in a Market Simulation
  with Deep Reinforcement Learning." arXiv:2406.02650. https://arxiv.org/pdf/2406.02650
- **Year:** 2020 (primary).
- **Venue:** *American Economic Review* (top-5 economics journal, peer-reviewed).

## Ontology question(s) informed
L1.B5.1 (risks/limits of algorithmic dynamic pricing). Critical safety/compliance input to L2.B5
and B10 (legal/antitrust). Feeds A7 (safety) constraints on autonomous pricing.

## GRADE tier
**High.** AER is a top-tier peer-reviewed venue; the finding is replicated by independent teams
(LLM-based Fish et al. 2024; deep-RL studies) -> multiple independent sources for this
safety/correctness-critical claim, exceeding DEPTH-RUBRIC sec 1 (>= 3 independent).

## Key claims and EXACT findings (faithful, verbatim where load-bearing)
1. **Headline finding (verbatim):** "the algorithms consistently learn to charge supracompetitive
   prices, without communicating with one another." The Q-learning agents, in a repeated Bertrand
   oligopoly, autonomously converge on prices above the competitive (Nash) level.
2. **Mechanism (verbatim):** "The high prices are sustained by collusive strategies with a finite
   phase of punishment followed by a gradual return to cooperation." The algorithms learn
   reward-punishment (trigger-like) strategies without any explicit agreement or communication.
3. **Robustness (exact):** the result is "robust to asymmetries in cost or demand, changes in the
   number of players, and various forms of uncertainty."
4. **Significance:** demonstrates **tacit algorithmic collusion** is achievable by independent
   learning agents -- a live antitrust concern, since it can raise consumer prices and may
   constitute (or skirt) anticompetitive conduct without human intent or communication. Corroborated
   for LLM-based pricing agents (Fish et al. 2024) and deep-RL markets.

## Reproducibility note
The supracompetitive-price + punishment-strategy result is the central, reproducible finding of
Calvano et al. (2020), AER 110(10), pp. 3267-3297 (abstract verified via aeaweb.org). Independently
reproduced by LLM-agent (2024) and deep-RL (2024) studies -> robust, multiply-confirmed. This is a
*risk* finding AutoFirm must design against, recorded exactly per DEPTH-RUBRIC sec 3.
