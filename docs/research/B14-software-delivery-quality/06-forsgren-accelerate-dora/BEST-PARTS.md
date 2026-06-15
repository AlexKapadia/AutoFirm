# BEST-PARTS — Accelerate / DORA

## ADOPT
1. **The Four Keys as AutoFirm's client-delivery KPIs.** Deployment Frequency, Lead Time for Changes, Change Failure Rate, Time to Restore — measured per client product and surfaced in `evidence/`. They give an evidence-backed, industry-standard definition of "good software delivery" that generalises across any industry/size (satisfies generality, CLAUDE.md §3.9).
2. **The CD capability set as the CI/CD pipeline contract.** Version control of all artifacts, **trunk-based development**, test automation, deployment automation, continuous integration, shift-left security, loosely coupled architecture — these are *empirically* the levers, so AutoFirm's pipeline implements all of them by default.
3. **Trunk-based development validates CLAUDE.md's always-clean-main + short-lived-experiment-branches doctrine** with hard numbers: <3 active branches, branch life <1 day, no code freezes. AutoFirm's git hygiene (experiment/* branches that land or die fast, clean main) is the DORA-optimal pattern — cite this as the evidence.
4. **No speed-vs-stability tradeoff.** Justifies demanding *both* fast delivery and low change-failure-rate from client builds, not trading one for the other.

## REJECT
- Reject long-lived feature branches / GitFlow-style release branches for client delivery — DORA evidence ties them to lower performance. (Exception: regulated clients that mandate it.)

## Concrete artifact this drives
- A pipeline-template contract embedding the CD capabilities + a Four-Keys telemetry emitter; CFR target band 0-15%; trunk-based branch policy enforced (branch-age alarm > 1 day). Feeds the `evidence/` delivery-performance dashboard.
