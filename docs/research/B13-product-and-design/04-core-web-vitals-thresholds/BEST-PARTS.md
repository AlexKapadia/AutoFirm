# BEST-PARTS — Core Web Vitals

## What AutoFirm should ADOPT and why

1. **The three "good" thresholds as the hard performance budget.** ADOPT LCP <= 2.5 s, CLS <= 0.1,
   INP <= 200 ms (exactly the §4.9.7 budget) as a CI-enforced gate. Build implication: a client UI
   fails the Definition-of-Done if any Core Web Vital exceeds "good"; Lighthouse CI / PageSpeed
   Insights produces the number, and it flows into `evidence/` as a latency chart with the 2.5 s /
   0.1 / 200 ms reference lines.

2. **75th-percentile assessment rule.** ADOPT: measure at p75, not the mean — a single fast run is
   not proof. Build implication: the performance test runs the page many times (or uses field/CrUX
   data) and reports p75, matching the §3.6 statistical-rigor bar (CIs, percentiles, not point
   estimates).

3. **INP (not FID) as the responsiveness metric.** ADOPT INP <= 200 ms — FID is deprecated since
   March 2024. Build implication: keeps the perf gate current; the test harness measures INP across
   real interactions (ties to the Playwright E2E suite, source 05, which already drives every
   control).

4. **The achievability + perception methodology as design rationale.** ADOPT the documented basis
   (Miller/Card attention windows; ~100 ms causality threshold) so the budget is justified by HCI
   research, not arbitrary. Build implication: the design brief explains WHY the budget exists,
   satisfying "explain every decision" (§3.11), and lets the CDO trade off (e.g. skeleton screens,
   source 09) against measured LCP/CLS.

## What AutoFirm should REJECT / DEFER

- **REJECT lab-only (synthetic) scores as sole proof.** Lab Lighthouse approximates; the canonical
  assessment is field/CrUX p75. Use lab in CI as a fast gate but acknowledge field is the standard
  of record (don't misrepresent a lab pass as a field pass).
- **DEFER non-Core Web Vitals (TTFB, FCP, TBT)** to diagnostic-only status — they explain *why* a
  Core Web Vital is poor but are not the acceptance gate themselves.

## Concrete build implication
Core Web Vitals are the second, quantitative half of the UI Definition-of-Done (WCAG AA being the
first, source 03). They give three exact, CI-enforceable numbers (LCP<=2.5s, CLS<=0.1, INP<=200ms)
measured at p75, justified by HCI research, and charted in `evidence/`. They directly constrain
design choices (skeleton/loading states, image/layout strategy) that the design-build playbook
(L2.B13) must generate to pass.
