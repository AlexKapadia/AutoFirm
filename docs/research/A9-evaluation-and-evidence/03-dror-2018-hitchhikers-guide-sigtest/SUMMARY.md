# SUMMARY — The Hitchhiker's Guide to Testing Statistical Significance in NLP

## Full citation
- **Title:** The Hitchhiker's Guide to Testing Statistical Significance in Natural Language Processing
- **Authors:** Rotem Dror, Gili Baumer, Segev Shlomov, Roi Reichart
- **Year:** 2018
- **Venue:** Proceedings of the 56th Annual Meeting of the Association for Computational
  Linguistics (ACL 2018), Volume 1: Long Papers, pages 1383-1392, Melbourne, Australia
- **DOI/URL:** 10.18653/v1/P18-1128 | https://aclanthology.org/P18-1128/

## Questions informed
- **L1.A9.2** Statistical rigor for stochastic systems -- significance-test selection (PRIMARY).

## GRADE tier: High
Peer-reviewed full paper at ACL (top-tier NLP venue), methodological/prescriptive, widely cited.
No down-rate. Corroborated for the multi-dataset case by Demsar 2006 (source 04, peer-reviewed
JMLR), giving two independent High/peer-reviewed anchors for the significance-testing claims.

## Key claims

### Motivating survey finding
The authors surveyed empirical papers in ACL and TACL during 2017 and report that statistical
significance testing "is often ignored or misused" in the community despite high value placed on
experimental results. (Qualitative finding; exact counts not reproduced here -- treat as
supporting, not a precise statistic.)

### Test-selection protocol (the prescriptive core)
1. Determine the **outcome / evaluation-measure type** (continuous vs. binary/categorical).
2. Check assumptions (normality, independence of observations).
3. Choose **parametric** test if assumptions hold; otherwise the **non-parametric** alternative.
4. Prefer **resampling** methods (bootstrap, permutation/randomization) for robustness because they
   make no distributional assumption.

### Recommended tests by measure type
- Continuous metrics: **paired t-test** (parametric) / **Wilcoxon signed-rank test**
  (non-parametric alternative when normality is violated).
- Binary / paired categorical outcomes: **McNemar's test**.
- Distribution-free robust inference: **bootstrap** and **permutation (randomization) tests**;
  also **sign test** for paired comparisons and the **Pitman permutation test**.

### Significance threshold
Conventional alpha = 0.05 is referenced, but the paper "cautions against mechanical threshold
application," advocating contextual interpretation rather than rigid cutoffs.

## Reproducibility note
Protocol and test list extracted from the ACL Anthology HTML and the official P18-1128 PDF. The
parametric/non-parametric pairing (t-test/Wilcoxon, McNemar for binary, bootstrap/permutation as
distribution-free) is the load-bearing recommendation and is reproducible from the paper's
"practical protocol" section. The 2017 ACL/TACL survey claim is qualitative.
