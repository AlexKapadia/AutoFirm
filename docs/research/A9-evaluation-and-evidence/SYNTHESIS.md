# SYNTHESIS — A9: Evaluation, Evidence & QA of the Platform

Branch A9, Layer-1. Covers L1.A9.1 (agent-eval taxonomy & reproducibility pitfalls), L1.A9.2 (statistical rigor for stochastic systems), L1.A9.3 (mutation testing & test-adequacy theory). 9 sources, one folder each. This file surveys the option space and gives AutoFirm a concrete, cited recommendation. Build decisions belong to L2.A9 (gated on this passing).

## Source ledger
| # | Source | Year | Tier | Question |
|---|--------|------|------|----------|
| 01 | Mohammadi et al., Evaluation & Benchmarking of LLM Agents: A Survey (KDD25) | 2025 | Moderate | A9.1 |
| 02 | Cao et al., Rigor/Reliability/Reproducibility: 572 Code Benchmarks (arXiv) | 2025 | Moderate | A9.1/A9.2 |
| 03 | Dror et al., Hitchhikers Guide to Sig-Testing in NLP (ACL18) | 2018 | High | A9.2 |
| 04 | Demsar, Statistical Comparisons of Classifiers over Multiple Data Sets (JMLR) | 2006 | High | A9.2 |
| 05 | Chen et al., Evaluating LLMs Trained on Code (pass@k, HumanEval; arXiv) | 2021 | Moderate | A9.2/A9.1 |
| 06 | DeMillo, Lipton & Sayward, Hints on Test Data Selection (IEEE Computer) | 1978 | High | A9.3 |
| 07 | Jia & Harman, Analysis & Survey of Mutation Testing (IEEE TSE) | 2011 | High | A9.3 |
| 08 | Andrews, Briand & Labiche, Is Mutation Appropriate for Testing Experiments? (ICSE) | 2005 | High | A9.3 |
| 09 | Petrovic & Ivankovic, State of Mutation Testing at Google (ICSE-SEIP) | 2018 | Mod-High | A9.3 |

## L1.A9.1 — Agent-eval taxonomy & reproducibility pitfalls

OPTION SPACE surveyed (WHAT-axis): behavior (task completion / quality / cost-latency), capabilities (tool use, planning, memory, multi-agent), reliability (consistency, robustness), safety & alignment. (HOW-axis): static-offline vs dynamic-online; synthetic vs real data; code-based vs LLM-as-Judge vs human-in-loop; tooling; context. (Source 01.)

EVIDENCE on pitfalls is damning and CONVERGENT across two independent surveys:
- only 35.4% of code-benchmark evaluations are repeated; ~80% ignore data contamination; >90% use passing tests as oracle without considering coverage; 52.6% do not disclose prompts; 16.7% publish logged results; 3.6% give the experiment environment (source 02).
- agent stochasticity makes single-run results meaningless; pass^k is needed for mission-critical consistency (source 01).

RECOMMENDATION for AutoFirm (feeds L2.A9):
1. Adopt source 01 two-axis taxonomy as the eval-harness spine; grade Reliability and Safety as first-class (matches CCO/North-Star review, CLAUDE.md section 2).
2. Adopt HOW2BENCH 5-phase rigor lifecycle (source 02) as the reproducibility contract for any benchmark AutoFirm runs; publish prompts, environment, and logged results by default.
3. NEVER accept a single-run result; always N>=k repeated trials with reported variance.
4. Use public agent benchmarks (SWE-bench etc.) only as capability spot-checks, never as the acceptance bar -- generality is proven on the fixed industry panel (CLAUDE.md section 3.9).

## L1.A9.2 — Statistical rigor for stochastic systems

OPTION SPACE surveyed: point estimates (rejected -- high variance, source 05); parametric tests (t-test/ANOVA -- only when assumptions hold, source 03; rejected for cross-dataset, source 04); non-parametric paired tests (Wilcoxon signed-rank, McNemar for binary, sign test, source 03); resampling (bootstrap, permutation -- the robust default, source 03); multi-system/multi-dataset omnibus + post-hoc (Friedman + Nemenyi, source 04); stochastic-success estimators (unbiased pass@k with n>=k, source 05; pass^k for all-of-k, source 01).

RECOMMENDATION (a concrete decision tree for AutoFirm comparator -- feeds L2.A9):
- Quantify a stochastic step success with the unbiased pass@k estimator 1 - C(n-c,k)/C(n,k) (n>=k trials), and pass^k for critical/deterministic steps.
- Compare TWO approaches on one golden set: per-item binary pass/fail -> McNemar; continuous score -> Wilcoxon signed-rank (or paired t-test only if normality holds); default robust path -> paired bootstrap/permutation reporting p-value + effect size + CI.
- Compare >=3 approaches across the 8-row industry panel -> Friedman omnibus + Nemenyi post-hoc with CD = q_alpha*sqrt(k(k+1)/(6N)), emit a CD diagram to evidence/. NEVER average accuracies across industries (source 04) -- it hides per-industry failure and overstates power.
- Report effect size + CI alongside every p-value; do not apply alpha=0.05 mechanically (source 03).

This makes CLAUDE.md section 3.4 pick-the-evidence-backed-winner a defensible statistical procedure.

## L1.A9.3 — Mutation testing & test-adequacy (tests with teeth)

OPTION SPACE surveyed for adequacy criteria: statement/branch coverage (necessary, NOT sufficient -- sources 02, 09); mutation testing (the teeth -- sources 06/07/08/09). Mutation cost-reduction menu: selective mutation, mutant sampling, weak vs strong mutation, higher-order mutation (source 07); diff-based + arid-line suppression + productive-mutant filtering (source 09).

THE EVIDENCE CHAIN (>=3 independent sources for the critical claim):
- THEORY: mutation adequacy works because of the Coupling Effect -- killing simple-fault mutants catches complex real faults (source 06, DeMillo 1978; operationalized by Offutt via source 07).
- FORMULA: mutation score MS = killed / non-equivalent mutants; equivalent mutants are undecidable and must be excluded (source 07, Jia & Harman TSE).
- VALIDATION: mutants empirically resemble real faults and are a better proxy than hand-seeded faults -- so MS predicts real-fault detection (source 08, Andrews ICSE 2005).
- SCALE/PRACTICE: diff-based, arid-suppressed, productivity-filtered mutation is feasible at 2B LOC (source 09, Google) -- and coverage alone is misleading (covered but consequences not asserted).

RECOMMENDATION (feeds L2.A9 platform QA + L1.B14.2 client-code QA):
1. Gate on mutation score = killed/non-equivalent, NOT coverage alone. Target MS=1 on security-/correctness-critical modules (CLAUDE.md section 3.6), documented threshold elsewhere.
2. Exclude equivalent mutants from the denominator; triage suspected-equivalent survivors and audit the rationale -- never silently inflate the score.
3. Scale with diff-based + selective + arid-line mutation (mutate changed/covered lines only); weak mutation for fast feedback, strong at the gate.
4. Filter to productive mutants; a surviving productive mutant -> write a harder adversarial test, re-run (CLAUDE.md section 3.6/3.7 iterate-to-perfection loop).
5. Cite source 08 in evidence/ to claim, defensibly, that the mutation gate measures REAL quality.

## Cross-cutting recommendation
A9 turns AutoFirm QA slogans into a runnable, cited harness: (a) a taxonomy-driven eval surface covering behavior/capability/reliability/safety; (b) a statistically-rigorous comparator (pass@k / pass^k + McNemar/Wilcoxon/bootstrap for k=2, Friedman/Nemenyi across the industry panel) that reports CIs and effect sizes; (c) a mutation-score gate (killed/non-equivalent, diff-based, productive-filtered) empirically validated as a real-quality proxy. All findings feed the evidence/ showcase (CLAUDE.md section 3.10) and the CCO heartbeat (section 2).

## Open questions / handoffs to L2
- Exact mutation tooling per language stack (mutmut/cosmic-ray/Stryker) -> L2.A9 / L2.B14.
- Reconcile source 02 exact denominator (572 vs analyzed subset) against the camera-ready before any percentage is used as a safety-critical number (DEPTH-RUBRIC section 3.5 flag).
- LLM-as-Judge variance characterization (when, if ever, a judge may grade non-deterministic artifacts) -> needs a dedicated L1 sub-study; currently restricted to non-critical outputs.
- Bayesian alternatives to NHST for classifier/approach comparison -> optional L2 enhancement.
