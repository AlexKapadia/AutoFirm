# SUMMARY — Anderl et al. (2016): Graph-Based / Markov Attribution

**Question(s) informed:** L1.B7.1 (attribution — peer-reviewed data-driven model with the removal-effect formula).

## Full citation
- **Title:** Mapping the customer journey: Lessons learned from graph-based online attribution modeling
- **Authors:** Eva Anderl, Ingo Becker, Florian von Wangenheim, Jan Hendrik Schumann
- **Year:** 2016
- **Venue:** *International Journal of Research in Marketing (IJRM)*, Vol. 33, No. 3, pp. 457-474
- **DOI/URL:** https://doi.org/10.1016/j.ijresmar.2016.03.001 · RePEc: https://ideas.repec.org/a/eee/ijrema/v33y2016i3p457-474.html · SSRN working paper: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2343077 · ETH Research Collection: https://www.research-collection.ethz.ch/handle/20.500.11850/121846

## GRADE tier
**High.** Peer-reviewed top-tier marketing journal (IJRM, an FT-50-adjacent / ABS-4 venue); empirical study on real clickstream data from four companies across industries. Up-rated for cross-industry data and a formally defined, reproducible method. This is the **primary peer-reviewed anchor** for data-driven (graph) attribution.

## Core content (faithful summary)
Models the customer journey as a **first-order Markov graph**: states = the marketing channels plus a START and a CONVERSION (and NULL/non-conversion) state; edges carry **transition probabilities** estimated from observed journeys. Channel importance is computed via the **REMOVAL EFFECT**.

### Removal effect (exact concept, reproduced)
The **removal effect** of a channel (state) `s_i` is the change in the probability of reaching CONVERSION (from START) when `s_i` is removed from the graph (all paths through it are redirected to NULL/non-conversion). Formally, attribution credit for channel `i` is proportional to:

  RemovalEffect(i) = [ P(conversion | full graph) - P(conversion | graph with state i removed) ]

and each channel's attributed value = its removal effect normalized so the removal effects sum to 1 (i.e. credit_i = RemovalEffect(i) / Sum_j RemovalEffect(j)). A channel whose removal sharply drops conversion probability is highly important.

P(conversion) is obtained from the Markov chain's absorption probability into the CONVERSION state given the transition matrix.

## Key claims (locators)
1. Heuristic models (last-click, first-click, linear) **mis-attribute** credit relative to the data-driven graph model; last-click systematically over-credits late-funnel channels (Sect. 5, findings).
2. The graph/Markov model is **objective, data-driven, and interpretable**, and generalizes across the four firms studied.
3. Higher-order Markov extensions can better capture path dependence (discussed; later corroborated by independent removal-effect work).

## Reproducibility note
Removal-effect attribution reproducible from the transition matrix of any path dataset (open-source implementations exist, e.g. R `ChannelAttribution`). The absorption-probability + removal-effect derivation is the method of record.
