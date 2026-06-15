# BEST-PARTS — Dror et al. 2018 (Hitchhiker's Guide to Sig-Testing in NLP)

## ADOPT

1. **Adopt the test-selection protocol verbatim as AutoFirm's "is this difference real?" routine.**
   Whenever AutoFirm compares two approaches on a golden set (CLAUDE.md §3.4 branch-per-experiment,
   §4.5), it must run a significance test before declaring a winner -- not pick by raw mean.
   *Build implication:* the eval harness exposes `compare(a, b, measure_type)` that:
   - continuous score (e.g. accuracy, latency): paired t-test if ~normal, else Wilcoxon signed-rank;
   - binary per-item pass/fail (the common agent case): **McNemar's test** on the paired
     pass/fail contingency table;
   - default robust path: **bootstrap or permutation test** (no distributional assumption).

2. **Default to permutation/bootstrap for agent eval.** Agent pass/fail distributions are
   non-normal and item counts are often small; the paper explicitly favors distribution-free
   resampling. *Build implication:* AutoFirm's default comparator is a paired bootstrap over
   per-item scores, reporting a p-value AND a confidence interval on the difference -- feeding
   evidence/ charts (CLAUDE.md §3.10).

3. **Adopt the "don't apply 0.05 mechanically" caution.** Report effect size + CI alongside the
   p-value so a tiny-but-significant difference isn't oversold. *Build implication:* the
   experiment-decision record (RESEARCH-PROGRAM.md §5) records effect size, CI, AND p-value, and
   the winner must show a *practically* meaningful margin, not just p<0.05.

## REJECT / DEFER

- **REJECT** declaring an `experiment/*` winner on a raw point-estimate difference (mean accuracy
  higher) with no significance test -- this is exactly the "ignored or misused" practice the paper
  documents and would violate CLAUDE.md §3.4's "measure, don't pick by taste."
- **DEFER** the multi-algorithm-over-multiple-datasets case to source 04 (Demsar): when AutoFirm
  compares 3+ approaches across the fixed industry panel, use Friedman + Nemenyi, not pairwise
  t-tests (avoids multiple-comparison inflation).

## Why this matters to AutoFirm
This is the primary methodological authority for L1.A9.2. It turns "the evidence-backed winner"
(CLAUDE.md §3.4) from a slogan into a concrete, defensible statistical procedure -- the difference
between "B looked better" and "B beats A, McNemar p=0.003, 95% CI on diff [+4.1, +9.8] pts."
