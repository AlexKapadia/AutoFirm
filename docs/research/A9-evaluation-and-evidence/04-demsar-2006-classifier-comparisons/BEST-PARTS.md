# BEST-PARTS — Demsar 2006 (Statistical Comparisons of Classifiers)

## ADOPT

1. **Use Friedman + Nemenyi as AutoFirm's multi-approach comparator across the fixed industry
   panel.** When >=3 `experiment/*` approaches are compared across the 8-row industry panel
   (QUESTION-ONTOLOGY B12 golden set), pairwise t-tests would inflate the false-positive rate via
   multiple comparisons. *Build implication:* the eval harness's "rank N approaches over M
   industries" routine uses the **Friedman omnibus test** then the **Nemenyi post-hoc** with the
   CD = q_alpha * sqrt(k(k+1)/(6N)) critical difference, and emits a **critical-difference (CD)
   diagram** straight into evidence/ (CLAUDE.md §3.10).

2. **Adopt the "do not average accuracies across datasets" rule.** This is a direct guard against
   overfitting/misleading aggregation (CLAUDE.md §3.9). *Build implication:* generalization claims
   across the industry panel are reported as **average ranks + Friedman/Nemenyi**, never as a
   single pooled mean -- a single mean would hide that an approach wins on SaaS but loses on
   manufacturing.

3. **Adopt the parametric-assumptions critique as a hard gate.** Before any t-test/ANOVA on
   cross-industry results, the harness must reject it: normality + commensurability across
   heterogeneous industries does not hold. *Build implication:* the default cross-panel comparator
   is non-parametric (Friedman/Nemenyi or Wilcoxon for k=2), matching Dror (source 03).

## REJECT / DEFER

- **REJECT** repeated-measures ANOVA / pooled-mean comparison across the industry panel
  (assumptions violated; hides per-industry behavior).
- **DEFER** Bayesian alternatives (e.g. Benavoli-style Bayesian classifier comparison) to L2 if a
  reviewer wants posterior probabilities of superiority rather than NHST -- noted as a future
  enhancement, not required for the L1 bar.

## Why this matters to AutoFirm
This is the second peer-reviewed (High-tier) anchor for L1.A9.2 and the *specific* authority for
the cross-industry generalization claim AutoFirm must make (any company, any industry). It turns
"works for all panel rows" (QUESTION-ONTOLOGY B12) into a defensible Friedman/Nemenyi result with
a CD diagram in evidence/, rather than a hand-waved average.
