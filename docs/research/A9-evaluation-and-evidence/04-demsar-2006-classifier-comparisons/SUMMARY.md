# SUMMARY — Statistical Comparisons of Classifiers over Multiple Data Sets

## Full citation
- **Title:** Statistical Comparisons of Classifiers over Multiple Data Sets
- **Author:** Janez Demsar
- **Year:** 2006
- **Venue:** Journal of Machine Learning Research (JMLR), Vol. 7, pages 1-30
- **DOI/URL:** https://jmlr.org/papers/v7/demsar06a.html | PDF: https://www.jmlr.org/papers/volume7/demsar06a/demsar06a.pdf

## Questions informed
- **L1.A9.2** Statistical rigor -- multi-system / multi-dataset comparison (PRIMARY).

## GRADE tier: High
Peer-reviewed JMLR, one of the most-cited methodology papers in ML (>12,000 citations). The
recommended tests and their formulae are reproduced from the paper. No down-rate.

## Key claims (with formulae reproduced exactly)

### Recommended tests
- Comparing **two** classifiers over multiple data sets: **Wilcoxon signed-ranks test**
  (non-parametric).
- Comparing **multiple** (>=3) classifiers over multiple data sets: **Friedman test** followed by
  the **Nemenyi post-hoc test**.

### Friedman statistic (reproduced)
    chi^2_F = (12N) / (k(k+1)) * [ sum_j (R_j)^2 - (k(k+1)^2)/4 ]
(equivalently written with the -3N(k+1) form), where:
- N = number of data sets,
- k = number of classifiers,
- R_j = average rank of classifier j over the N data sets.
NOTE: the standard textbook form is
    chi^2_F = (12N)/(k(k+1)) * [ sum_j R_j^2 - k(k+1)^2/4 ];
the extracted "-3N(k+1)" expansion is algebraically equivalent. Reproduce the JMLR Eq. exactly
when citing; both forms appear in the literature.

### Nemenyi critical difference (reproduced)
    CD = q_alpha * sqrt( k(k+1) / (6N) )
where q_alpha is the critical value from the **Studentized range statistic** divided by sqrt(2).
Two classifiers differ significantly if their average ranks differ by at least CD.

### Critique of parametric tests for this setting
Paired t-test and repeated-measures ANOVA assume **normality** and **commensurability /
homogeneity of variance** across data sets; these assumptions "typically do not hold" when
comparing classifiers across heterogeneous data sets, so the parametric tests are not safe here.

### Against averaging accuracies across data sets
Computing a single mean accuracy across data sets and analyzing that "discards important
dataset-level information and inflates statistical power estimates, producing misleading
conclusions." Demsar argues comparisons should be **rank-based across data sets**, not on pooled
or averaged scores.

## Reproducibility note
Formulae extracted from the JMLR PDF. The two key formulae (Friedman chi^2_F, Nemenyi CD) are
safety-critical per DEPTH-RUBRIC §3.5 and must be cross-checked against JMLR v7 Eqs. before use in
AutoFirm code; the equivalent textbook form is noted to avoid a transcription error.
