# BEST-PARTS — SAST effectiveness & limits

## ADOPT
1. **Defense-in-depth, not single-scanner trust.** With FN rates of 47-80% per tool and only 30-69% even when combined, AutoFirm must layer **SAST + DAST + SCA/dependency scan + secrets scan + fuzzing + property tests + independent review** — no single gate is allowed to be the sole security assurance. This is the empirical justification for the multi-layer secure-SDLC (sources 07/08).
2. **Triage, don't auto-trust, SAST output.** FP rates of 3-48% mean raw scanner output is noisy; AutoFirm routes findings through a triage step (dedupe, rank, confirm) before gating — and confirms criticality before failing the build, while still **failing closed** on high/critical confirmed findings (CLAUDE.md §5.6).
3. **Prioritise false-negative reduction.** Matching the developer-preference finding, AutoFirm weights coverage of *real* vulnerability classes (combining tools + fuzz + manual) over chasing a clean FP rate.

## REJECT
- Reject "SAST is green therefore secure" as an assurance claim — the data shows it can have zero true-positive rate while reporting few false positives.

## Concrete artifact this drives
- A `security-gate` that aggregates multiple scanners + fuzz + dep/secret scans, triages and dedupes findings, and fails closed on confirmed high/critical issues; the manifest records which techniques ran (so the FN-coverage argument is auditable).
