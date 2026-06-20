# 12 — Fail-closed quality gates & defect escape rate (software-release analogue)

- **Author / org:** Professional QA / release-engineering practice; SonarQube quality-gate model;
  agile defect-escape-rate literature.
- **Year:** current practice.
- **Link:** SonarQube quality gates (sonarsource.com); escape-rate benchmarks (e.g. plandek.com,
  devstats.com glossaries).
- **Tier:** Moderate (professional practice; corroborates Boehm 09).

## Faithful structured summary

A **quality gate** is a set of pass/fail conditions a build must satisfy before promotion; if any
condition fails the gate **blocks the release** ("fail-closed" — promotion proceeds only on an
explicit PASS, never by default). SonarQube's per-PR quality gate **blocks merges when defect density
exceeds a threshold**, making the gate actionable rather than retrospective.

**Defect escape rate** = proportion of defects that reach production / the end user. Benchmarks:
**<10% excellent, 10–20% good, 20–40% concerning, >40% broken QA process.**

**Critical warning relevant to us:** *"A test suite can show 95% pass rate and still have a terrible
escape rate because tests might be passing trivially ... or be flaky and give false confidence."* —
pass-rate and coverage are **not** proof of quality (exactly CLAUDE §3.6).

## Best parts to take (for our gate) and why

1. **The `ReleaseDecision` is a fail-closed quality gate done right:** PASS is the *only* path to
   delivery; absent/ambiguous/unauthorised -> refuse (CLAUDE §5.6). The plan's design matches the
   professional pattern.
2. **Escape rate is our top-line outcome KPI** — the fraction of planted/known defects that would
   have reached a human if not for the gate. Target ~0% on the controlled golden set; report it.
3. **Do NOT report pass-rate/coverage as the proof** — report **defect-detection rate, false-pass
   (escape) rate, and kappa vs gold reviewer**, because (per the warning) a green-looking gate can
   still be hollow. This shapes the §D.3 efficacy section and the `evidence/` metrics.
