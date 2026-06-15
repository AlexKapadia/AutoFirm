# BEST-PARTS — Petrovic & Ivankovic 2018 (Mutation Testing at Google)

## ADOPT

1. **Adopt diff-based + arid-line mutation as AutoFirm's scaling strategy.** AutoFirm runs
   continuously across many client repos; full-repo mutation is infeasible (Google: 2B LOC).
   *Build implication:* the QA harness mutates only **changed + covered** lines per increment (the
   diff under review), and suppresses arid (uncovered/uninteresting) lines -- exactly mirroring the
   technique proven at Google scale. This makes CLAUDE.md §3.6's mutation mandate affordable on
   every commit (§3.13 commit cadence) rather than a once-in-a-while batch.

2. **Adopt the "productive mutant" concept + developer-feedback loop.** Not every surviving mutant
   warrants a test; surfacing low-value mutants erodes trust. *Build implication:* AutoFirm
   classifies survivors and routes only *productive* ones into the iterate-to-perfection loop;
   flagged-unproductive mutants are recorded (audited) so the score isn't gamed and the operator
   set self-improves. This prevents the failure mode where a high mutant count becomes noise.

3. **Adopt the empirical "covered but not asserted upon" finding as independent corroboration of
   coverage-insufficiency.** Two independent sources now say it: Google (this) + Cao et al. 2025
   (source 02, "Over 90% did not consider coverage as oracle"). *Build implication:* strengthens
   the evidence base for gating on mutation, not coverage -- AutoFirm can cite a real
   2-billion-LOC deployment, not just theory.

## REJECT / DEFER

- **REJECT** whole-repo, every-mutant mutation as AutoFirm's default -- proven infeasible at scale;
  diff-based is the practitioner-validated path.
- **REJECT** treating raw surviving-mutant count as the metric -- without the productive/unproductive
  distinction it generates noise and developer distrust (Google's explicit lesson).
- **DEFER** Google's exact arid-line heuristics and operator weights -- AutoFirm must derive its own
  per-language set (L2.A9 / L2.B14); adopt the *principle*, tune the *parameters* (generality,
  CLAUDE.md §3.9 -- no magic constants copied wholesale).

## Why this matters to AutoFirm
This is the proof that mutation testing is *operationally viable at industrial scale* and the
recipe for doing it: diff-based, arid-suppressed, productivity-filtered, integrated at review time.
It turns CLAUDE.md §3.6 from an aspiration into a continuously-runnable gate and supplies the
second independent source for "coverage is not enough" -- both feeding L2.A9 (platform eval harness)
and L1.B14.2 (client-product test strategy).
