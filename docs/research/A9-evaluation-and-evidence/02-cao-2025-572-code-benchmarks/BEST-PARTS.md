# BEST-PARTS — Cao et al. 2025 (572 Code Benchmarks survey)

## ADOPT

1. **Treat "only 35.4% of evaluations are repeated" as the empirical justification for AutoFirm's
   mandatory repeat-trial rule.** This is the hard number behind CLAUDE.md's determinism tests and
   the DEPTH-RUBRIC's "<20% verify their numbers" concern. *Build implication:* AutoFirm's eval
   harness ALWAYS runs N>=k repeated trials for any stochastic step and reports variance -- never a
   single run. A single-run result is treated as not-yet-evidence.

2. **Adopt the coverage-is-insufficient finding ("Over 90% did not consider code coverage when
   using passing test cases as an oracle").** This is independent corroboration of CLAUDE.md §3.6
   ("coverage gates necessary but not sufficient") and of the Google mutation paper (source 09).
   *Build implication:* AutoFirm gates on mutation score, not coverage alone.

3. **Port HOW2BENCH's 5-phase lifecycle into AutoFirm's evidence/ and eval-harness checklists.**
   Design -> Construction -> Evaluation -> Analysis -> Release maps cleanly onto AutoFirm's gate
   model (CLAUDE.md §4.2). *Build implication:* the evidence/ showcase folder gets a per-phase
   rigor checklist; Release-phase items (publish prompts, environment, logged results) become the
   reproducibility contract for any benchmark AutoFirm itself runs.

4. **Adopt data-contamination + deduplication discipline ("near 80% did not handle contamination",
   "62% did not deduplicate").** *Build implication:* any golden set AutoFirm builds (CLAUDE.md
   §4.5) must be deduped and contamination-checked against training data, and labelled
   public-data-only (CLAUDE.md §3.12).

## REJECT / DEFER

- **DEFER** wholesale adoption of all 55 HOW2BENCH items -- many are specific to publishing a
  public LLM code benchmark, not to a private internal eval harness. Cherry-pick the
  rigor/reproducibility/release items; defer the academic-publication items.
- **REJECT** using the raw percentages as safety-critical numbers until the exact denominator
  (572 vs analyzed subset) is reconciled with the camera-ready -- flagged in SUMMARY.

## Why this matters to AutoFirm
This is the empirical backbone for L1.A9.1/A9.2: it quantifies *how bad* current eval practice is
(no repeats, no variance, no contamination checks, coverage-as-oracle) and gives AutoFirm a
ready-made rigor checklist (HOW2BENCH) to be visibly better than the field -- feeding the
evidence/ showcase and the DEPTH-RUBRIC's own QA spot-fetch rule.
