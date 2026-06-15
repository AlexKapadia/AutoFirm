# SUMMARY — Evaluating Large Language Models Trained on Code (Codex / HumanEval / pass@k)

## Full citation
- **Title:** Evaluating Large Language Models Trained on Code
- **Authors:** Mark Chen, Jerry Tworek, Heewoo Jun, Qiming Yuan, et al. (OpenAI; 58 authors)
- **Year:** 2021
- **Venue:** arXiv preprint (cs.LG)
- **DOI/URL:** arXiv:2107.03374 | https://arxiv.org/abs/2107.03374

## Questions informed
- **L1.A9.2** Statistical rigor for stochastic systems -- the unbiased pass@k estimator (PRIMARY).
- Supporting L1.A9.1 (introduces the HumanEval benchmark used across agent-eval literature).

## GRADE tier: Moderate
arXiv preprint (DEPTH-RUBRIC §2 -> Moderate). Up-rate factors: enormous adoption (HumanEval and
pass@k are now de-facto standards), the estimator is a closed-form mathematical result (verifiable
independent of empirical claims), and the formula is independently reproduced by multiple
secondary sources. The estimator (the load-bearing claim) is High-confidence as mathematics; the
empirical Codex numbers are Moderate.

## Key claims

### The unbiased pass@k estimator (reproduced exactly)
Generate n >= k samples per problem; let c <= n be the number of correct samples that pass all
unit tests. The unbiased estimator is:

    pass@k := E_problems [ 1 - ( C(n-c, k) / C(n, k) ) ]

where C(a, b) = "a choose b" is the binomial coefficient. Interpretation: the probability that at
least one of k randomly drawn samples (from the n generated) is correct, averaged over problems.

- Motivation: "calculating pass@k in the traditional way" (generate exactly k, check >=1 pass)
  "can have high variance"; the n>=k estimator reduces variance "as many sampling combinations are
  now considered."
- Numerical-stability note: "directly computing this estimator is numerically unstable, so a
  numerically stable numpy implementation was introduced" (compute the product term iteratively
  rather than evaluating the binomial coefficients directly).

### Headline empirical results (HumanEval)
- "our model solves 28.8% of the problems, while GPT-3 solves 0% and GPT-J solves 11.4%" (pass@1).
- "we solve 70.2% of our problems with 100 samples per problem" (pass@100).

## Reproducibility note
pass@k formula independently corroborated by two secondary sources quoting Chen et al. 2021
(leehanchung.github.io 2025; Y. Chen, Medium). The binomial form and the n>=k construction are a
safety-critical formula under DEPTH-RUBRIC §3.5; reproduce from the paper's Eq. and the official
HumanEval repo `estimate_pass_at_k` before coding. Empirical 28.8% / 70.2% quoted verbatim from
the abstract.
