# BEST-PARTS — Inozemtseva & Holmes ICSE 2014

## ADOPT
1. **Coverage is a gate, never a quality claim.** Independent corroboration (with source 01) that high coverage does not imply a strong suite. AutoFirm keeps coverage thresholds (CLAUDE.md line/branch gates) but **must not** present coverage as evidence of effectiveness in `evidence/` — only mutation score and efficacy tests can claim that.
2. **Control for suite size when reporting test quality.** Because effectiveness tracks suite size more than coverage, AutoFirm's QA reporting should normalise by test count / report mutation score, not raw coverage deltas, so it cannot be gamed by adding trivial high-coverage tests.
3. **Don't over-invest in exotic coverage criteria.** The paper shows stronger coverage forms (MC/DC etc.) add little predictive value over statement coverage for effectiveness. AutoFirm should spend the budget on **mutation + property + fuzz** rather than chasing higher-order coverage metrics.

## REJECT
- Reject any CI rule of the form "raise coverage to X% to improve quality" as the primary quality lever.

## Concrete artifact this drives
- The `evidence/` test-quality panel separates two charts: **coverage (gate, dimmed)** and **mutation score + efficacy accuracy (the quality claim, highlighted)** — enforcing the CLAUDE.md §3.6 hierarchy visually.
