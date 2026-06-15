# BEST-PARTS — Camuffo et al. (2024) Large-Scale Replication

## ADOPT
1. **Cap and discipline pivots - don't maximize them.** The nonlinear finding tells AutoFirm's
   validation engine to recommend pivots only on disconfirming evidence, and to flag THRASHING
   (excessive pivots without convergence) as a failure mode. Build implication: a pivot-count
   guardrail in the validation playbook - after K evidence-backed pivots without convergence,
   escalate to a "terminate or fundamentally re-scope" verdict (fail-closed, auditable).
2. **Use the EUR 6,999.327 (p=.030) result as the citable evidence that disciplined validation
   has a measurable, significant performance payoff** - this is the number AutoFirm cites to justify
   building a rigorous validation function at all (feeds evidence/ and the L3 doctrine rationale).
3. **"It can be taught" -> it can be operationalized as an agent procedure.** The treatment was a
   teachable protocol, which is exactly what AutoFirm encodes as a deterministic playbook.

## REJECT / DEFER
- **Do NOT hard-code EUR 6,999.327 as a target/constant in any product code** - it is an effect-size
  estimate from a specific population, not a platform parameter (avoids overfitting, CLAUDE SS3.9).
  It belongs in evidence/citations, never in runtime logic.
- **Defer the 4-RCT extension's moderators** (which firm types benefit most) to L2.B12
  industry-parameterization work; cite here, design later.

## Quantified targets for evidence/
- Pivot-discipline metric: validation runs should converge in a *bounded, moderate* number of
  evidence-backed pivots on the fixed industry panel, never unbounded thrashing.
