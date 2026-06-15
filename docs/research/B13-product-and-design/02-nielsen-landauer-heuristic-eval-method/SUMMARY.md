# SUMMARY — Heuristic Evaluation Method, Evaluator Math Model & Severity Ratings

## Full citation
- **(A) Primary peer-reviewed:** Nielsen, J. & Landauer, T. K. (1993). *A mathematical model of
  the finding of usability problems.* Proc. INTERCHI '93 (ACM CHI), pp. 206-213.
  DOI: 10.1145/169059.169166 · https://dl.acm.org/doi/10.1145/169059.169166
- **(B) Method:** Nielsen, J. *How to Conduct a Heuristic Evaluation* + *The Theory Behind
  Heuristic Evaluations.* Nielsen Norman Group.
  https://www.nngroup.com/articles/how-to-conduct-a-heuristic-evaluation/ ·
  https://www.nngroup.com/articles/how-to-conduct-a-heuristic-evaluation/theory-heuristic-evaluations/
- **(C) Severity:** Nielsen, J. *Severity Ratings for Usability Problems.* NN/g.
  https://www.nngroup.com/articles/how-to-rate-the-severity-of-usability-problems/
- **Year:** 1993 (model) / NN/g articles ongoing
- **Venue/Publisher:** ACM CHI (peer-reviewed) + Nielsen Norman Group

## Questions it informs
- **L1.B13.1** (design-research / competitive-teardown METHOD — PRIMARY: how to systematically
  evaluate category-leading products)
- L1.B13.3 (how the 10 heuristics from source 01 are applied in practice)

## GRADE tier: High
The mathematical model is a peer-reviewed ACM CHI paper (primary). The method/severity articles
are the author's canonical practitioner statements. No down-rate. Up-rate: the Poisson model has
been independently replicated across 11 studies in the original paper plus decades of practice.

## Key claims (exact)

**The evaluator math model (Nielsen & Landauer 1993).** Problem detection across i independent
evaluators is modeled as a Poisson process:

    ProblemsFound(i) = N * (1 - (1 - L)^i)

where **N** = total number of usability problems in the interface; **L** (lambda) = proportion of
all usability problems found by a single average evaluator; **i** = number of independent
evaluators. Across six case studies lambda ranged "from 19 percent to 51 percent with a mean of
34 percent" (single evaluators found ~35% on average).

**Recommended panel.** "Three to five independent evaluators" — the cost-benefit sweet spot;
each individual "is likely to miss some of the potential usability issues," so independence then
aggregation is essential.

**Method (3 steps).** (1) Preparation — train evaluators on the heuristics, set scope.
(2) Independent evaluation — each evaluator works ALONE (two passes: familiarize, then hunt
heuristic violations) and must not see others' work first (avoids groupthink). (3) Consolidation
— synthesize via affinity diagramming, agree priorities.

**Severity = frequency + impact + persistence**, rated on a 0-4 scale (exact labels):
- **0** = "I don't agree that this is a usability problem at all"
- **1** = "Cosmetic problem only: need not be fixed unless extra time is available"
- **2** = "Minor usability problem: fixing this should be given low priority"
- **3** = "Major usability problem: important to fix, so should be given high priority"
- **4** = "Usability catastrophe: imperative to fix this before product can be released"

## Reproducibility note
The Poisson formula and lambda range (19-51%, mean 34%) are in the 1993 CHI paper (Table of the
six case studies). The 0-4 severity labels are quoted verbatim from the NN/g severity article.
