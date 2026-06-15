# SUMMARY — Swarm Intelligence: From Natural to Artificial Systems

## Full citation
- **Title:** Swarm Intelligence: From Natural to Artificial Systems
- **Authors:** Eric Bonabeau, Marco Dorigo, Guy Theraulaz
- **Year:** 1999
- **Venue:** Oxford University Press (Santa Fe Institute Studies in the Sciences of Complexity).
  ISBN 9780195131581 (hbk) / 9780195131598 (pbk). Oxford Academic online ed. 2020.
- **URL:** https://academic.oup.com/book/40811
- Foundational concept attribution within: **stigmergy** -- Grasse 1959 (termite nest-building);
  **Ant Colony Optimization (ACO)** -- Dorigo, Maniezzo & Colorni 1996, "Ant System", *IEEE Trans.
  Systems, Man, and Cybernetics-B* 26(1):29-41, https://doi.org/10.1109/3477.484436 (independent
  primary corroboration of the ACO mechanism).

## Questions informed
- **L1.A1.1** (taxonomy of MAS coordination -- the **swarm / stigmergic** pattern) -- PRIMARY.
  Closes the prior gap where "swarm" was named in the ontology's required enumeration but absent from
  the SYNTHESIS pattern table.
- L1.A1.4 (coordination cost) -- supporting (indirect/local coordination has near-zero direct
  messaging cost but trades it for slow convergence and weak per-decision accountability).

## GRADE tier
**High** (for the *mechanism and its properties*). The canonical scholarly synthesis of swarm
intelligence by the field's originators (Dorigo = ACO; Theraulaz/Grasse lineage = stigmergy),
published by Oxford / Santa Fe Institute, corroborated by the peer-reviewed Dorigo et al. 1996 Ant
System paper. Down-rate for **indirectness** to LLM agents (social-insect / optimization setting, not
LLM orchestration); relied upon for pattern definition and intrinsic trade-offs, not LLM numbers.

## Method / model (faithful)
- **Swarm intelligence** = useful collective behavior emerging from many simple agents following
  **local rules**, interacting **locally** with each other and the environment, with **no central
  controller / no global plan**. Defining properties cited: decentralization, simple homogeneous
  agents, scalability, robustness, adaptivity, and **emergence**.
- **Stigmergy** (Grasse) = indirect coordination via **modification of a shared environment**: an agent
  changes the environment (e.g. deposits a pheromone), and that change stimulates the next agent's
  action. Coordination is mediated by the *environment*, not by direct messages.
- **ACO (Ant System, Dorigo et al. 1996):** artificial ants build solutions probabilistically biased by
  **pheromone trails** + heuristic; good solutions get **positive feedback** (more pheromone), while
  **evaporation** provides **negative feedback** that forgets stale trails -- yielding emergent
  convergence on short paths without any agent seeing the whole problem.

## Key findings (faithful)
- Self-organization rests on four ingredients (cited): **positive feedback**, **negative feedback**,
  **randomness/fluctuation** (to explore), and **multiple local interactions**.
- Swarms scale to very large agent counts and are **robust to individual failures** (no single agent is
  critical) -- the headline strength of the pattern.
- The trade-off: behavior is **emergent and not directly specified**, so outcomes are hard to *guarantee*
  or *steer*, convergence can be slow, and there is **no single accountable decision-maker**.

## Limitations / intrinsic failure modes (faithful + analysis)
- **No central accountability / non-determinism:** emergent outcomes resist guarantees, exact reproduction,
  and a clear audit "who decided this" -- directly at odds with AutoFirm's deterministic-core, append-only
  audit, fail-closed requirements (CLAUDE.md 3.2, 5.6).
- **Convergence cost:** reaching a good collective answer can require many agents/iterations (expensive in
  the LLM-token regime).
- **Indirectness:** social-insect/optimization stigmergy != LLM agent coordination; mechanism ports,
  numbers do not.

## Reproducibility note
Definitions (swarm properties, stigmergy, ACO positive/negative-feedback dynamics) are stated directly in
the book and corroborated by the peer-reviewed Dorigo et al. 1996 Ant System paper (DOI above). No
quantitative LLM-era claim is drawn from this source.
