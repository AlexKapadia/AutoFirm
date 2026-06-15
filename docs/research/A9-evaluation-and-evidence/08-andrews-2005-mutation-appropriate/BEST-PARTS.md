# BEST-PARTS — Andrews, Briand & Labiche 2005

## ADOPT

1. **Adopt this as the EVIDENCE that mutation score measures real quality, not a proxy artifact.**
   CLAUDE.md §3.6 requires tests that "would actually FAIL if the code were wrong" and §3.10
   requires evidence the system is *measurably good*. This paper is the citation that closes the
   loop: a high mutation score empirically predicts real-fault detection. *Build implication:*
   AutoFirm's evidence/ showcase can state, with a High-tier ICSE citation, that its mutation gate
   corresponds to real-world fault-catching ability -- not merely "we ran a tool."

2. **Adopt "mutants > hand-seeded faults" as a methodology rule.** When AutoFirm validates a test
   suite's strength, it uses generated mutants, NOT manually-inserted faults (which the paper shows
   are less representative). *Build implication:* the QA loop and any "tests with teeth" validation
   use automated mutation operators; manual fault-seeding is explicitly rejected as the weaker
   method.

3. **Adopt the validity argument for the iterate-to-perfection loop.** Because mutation score
   tracks real-fault detection, the CLAUDE.md §3.7 loop (run -> mutate -> kill survivors -> repeat)
   provably drives toward real quality, justifying the loop as worthwhile rather than busywork.

## REJECT / DEFER

- **REJECT** substituting hand-seeded/manual fault injection for mutation in any AutoFirm quality
  experiment -- this paper shows it is less valid.
- **DEFER** the (later, ongoing) debate on *which* operators best resemble *modern* real faults
  (e.g. real-bug datasets like Defects4J) to L2 -- the 2005 result is sufficient for the L1 claim
  that mutation is an appropriate, trustworthy tool.

## Why this matters to AutoFirm
This source converts "mutation testing" from a ritual into *evidence*. It is the empirical warrant
that AutoFirm's mutation-score gate (sources 06/07) actually measures the thing that matters --
real-fault detection -- satisfying the DEPTH-RUBRIC's >=3-source bar for the critical claim and
letting the evidence/ showcase make a defensible, cited statement about test quality.
