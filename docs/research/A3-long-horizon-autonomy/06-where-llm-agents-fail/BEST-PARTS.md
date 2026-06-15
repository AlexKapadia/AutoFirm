# BEST-PARTS — Where LLM Agents Fail / AgentDebug

## ADOPT
1. **Adopt AgentDebug-style root-cause attribution as the post-mortem step in AutoFirm's iterate-to-perfection loop (CLAUDE.md §3.7).**
   - *Why:* the 24% / 17% / up-to-26% gains come from attributing a failure to its *root-cause step + module*, then correcting *that* — not retrying blindly. This is exactly the "launch agents to read the results/outputs, correct, re-test" loop AutoFirm mandates.
   - *Build implication:* when a run/test fails, a scoped **failure-attribution subagent** classifies the failure into the five modules (memory/reflection/planning/action/system) and pins the root-cause step; the fix targets that module. Feeds the §3.10 evidence showcase (failure-module distribution, kill-rate after fix).

2. **Adopt the five-module taxonomy as the schema for AutoFirm's audit-log failure records (branch A6).**
   - *Build implication:* every logged failure carries `{module, root_cause_step}`. Over many runs this yields a measurable map of *where* AutoFirm breaks, prioritizing hardening — and is testable: a property test asserts every failure record is classified into exactly one module.

3. **Adopt the error-propagation/cascade finding to justify checkpoint-and-validate frequency.**
   - *Why:* "early mistakes cascade and derail the whole trajectory" => the cheapest fix is catching them early. Reinforces source 05's milestone-checkpointing and source 10's independent validation: validate *before* an error can compound, not at the end.

## REJECT / DEFER
- **Reject** importing AgentDebug's exact benchmark numbers (ALFWorld/GAIA/WebShop) as AutoFirm targets — different task domain; re-measure on AutoFirm's golden suite (branch A9).
- **Defer** adopting the AgentDebug code directly (license/fit unverified) — adopt the *method*, re-implement against the Claude Code CLI substrate (branch A5).
