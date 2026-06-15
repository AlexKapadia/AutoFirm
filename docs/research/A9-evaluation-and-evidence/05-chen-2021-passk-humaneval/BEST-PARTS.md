# BEST-PARTS — Chen et al. 2021 (pass@k / HumanEval)

## ADOPT

1. **Adopt the unbiased n>=k pass@k estimator as AutoFirm's stochastic-success metric.** AutoFirm
   agents are stochastic; a naive "ran it once, passed" is high-variance and unscientific.
   *Build implication:* the eval harness implements
   `pass_at_k(n, c, k) = 1 - comb(n-c, k)/comb(n, k)` using the numerically-stable iterative form
   (mirror the official HumanEval `estimate_pass_at_k`), generating n>=k trials per task and
   averaging over tasks. This directly operationalizes CLAUDE.md §3.6's determinism/repeat-trial
   demand and source 02's "only 35.4% repeat" finding.

2. **Pair pass@k with pass^k (source 01) as a two-sided reliability view.** *Build implication:*
   - `pass@k` (>=1 of k succeeds) for *exploratory/generative* steps where one good candidate is
     enough (e.g. draft a marketing headline, propose an architecture).
   - `pass^k` (ALL k succeed) for *critical/deterministic* steps (audit-log writes, financial
     arithmetic) where any failure is unacceptable.
   The harness reports both so reviewers see capability AND reliability.

3. **Adopt the variance critique as doctrine.** "Calculating pass@k in the traditional way can
   have high variance" is the canonical justification for never trusting a single run.
   *Build implication:* evidence/ charts show pass@k with error bars derived from the trial set,
   not point estimates.

## REJECT / DEFER

- **REJECT** reporting a bare single-run success/fail for any stochastic agent step as evidence --
  it is exactly the high-variance practice this paper replaces.
- **REJECT** HumanEval itself as an AutoFirm acceptance bar (it tests isolated Python functions,
  not company-building). Use only as a capability spot-check / sanity benchmark; generality bar is
  the industry panel (CLAUDE.md §3.9).
- **DEFER** the broader "pass@k vs scaling-law" debate (large-language-monkeys line of work) to L2.

## Why this matters to AutoFirm
This supplies the *exact, citable, low-variance estimator* AutoFirm uses to quantify how often a
stochastic step actually works -- the metric that feeds every evidence/ reliability chart and that
makes "verified increment" (CLAUDE.md §3.13) measurable rather than rhetorical.
