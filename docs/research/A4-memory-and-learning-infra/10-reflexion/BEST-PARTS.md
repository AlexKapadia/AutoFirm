# BEST-PARTS — Reflexion

## ADOPT
- **No-gradient, memory-based self-improvement as AutoFirm's learning mechanism.** This is the single
  most important adoption for L1.A4.3: AutoFirm cannot fine-tune the hosted Claude model per task, so
  it learns the SAME way Reflexion does — by writing **verbal reflections to memory** and conditioning
  future actions on them. Build implication: the reflection record type and the "condition next
  attempt on past reflections" loop are core to L2.A4.
- **Actor / Evaluator / Self-Reflection separation as a generator-evaluator split** — already AutoFirm
  doctrine (CLAUDE.md s4.9 visual-verification, generator/evaluator). Build implication: the agent
  that acts is not the agent that judges; the judgment is what gets reflected and stored.
- **Quantified efficacy as an `evidence/` target.** The 80.1% -> 91.0% HumanEval jump is the kind of
  measurable "memory makes the agent better at its job" result AutoFirm must reproduce on its own
  golden task set (CLAUDE.md s3.6 efficacy tests): show accuracy-vs-trial learning curves.

## REJECT / DEFER
- **Reject unbounded reflection accumulation** — Reflexion bounds memory to ~1-3 experiences for a
  reason (context limits, folder 08). AutoFirm must summarize/abstract reflections (-> ExpeL, folder
  11) rather than retain all of them verbatim.
- **Defer reliance on a clean scalar reward** — most company-operations tasks lack one; AutoFirm will
  lean on the LLM-evaluator and heuristic signals.

## Build implication (concrete)
Establishes the **reflection-write -> condition-next-attempt learning loop** and the **acting-vs-judging
split** for L2.A4, plus the **accuracy-vs-trial learning-curve** evidence chart.
