# SUMMARY — McCabe, A Complexity Measure (Cyclomatic Complexity)

## Full citation
- **Title:** A Complexity Measure
- **Author:** Thomas J. McCabe
- **Year:** 1976
- **Venue:** IEEE Transactions on Software Engineering, vol. SE-2, no. 4, pp. 308-320. DOI: 10.1109/TSE.1976.233837
- **URL/DOI:** https://doi.org/10.1109/TSE.1976.233837

## Questions it informs
- **L1.B14.3** (code-organisation and maintainability; objective basis for module-size/complexity limits).

## The measure (exact formula)
For a program's control-flow graph G:

    v(G) = E - N + 2P

where **E** = number of edges, **N** = number of nodes, **P** = number of connected components.
For a single-entry single-exit module (P = 1) this equals **(number of binary decision predicates) + 1**.

## Purpose (exact, from the paper)
McCabe states the goal is to "provide a quantitative basis for modularization and allow us to identify software modules that will be difficult to test or maintain." He proposes the count of **linearly independent paths** through code as that measure, and recommends keeping module complexity bounded - a **threshold of 10** is his widely-cited practical guideline for v(G), above which a module should be split or restructured.

## Empirical caveats (from later literature)
- v(G) is **strongly correlated with lines of code**, so it partly measures size (Shepperd's critique; multiple replications). Treat it as one signal, not a sole quality oracle.
- Studies relating complexity/size to defect density are **context-dependent**: some find strong v(G)-error correlation (e.g. UNIX procedures), others find weaker or non-monotonic relationships. The threshold value is heuristic, not a law.

## GRADE tier
**High** for the metric definition (primary, foundational IEEE TSE paper). The defect-correlation caveats are **Moderate** (mixed replications) and explicitly flagged as contested.

## Reproducibility note
The formula v(G) = E - N + 2P is the primary, exactly-reproducible artifact. The threshold-of-10 guidance is McCabe's heuristic, corroborated across tool docs (SciTools, etc.) but acknowledged in the literature as imprecise.
