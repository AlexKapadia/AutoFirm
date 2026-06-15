# BEST-PARTS — Goal Misgeneralization

## ADOPT (safety-critical — this is WHY goals must be externalized, not inferred)
1. **Adopt "externalize and re-ground the goal on every resume" as a hard resume-protocol invariant.**
   - *Why:* goal misgeneralization is the failure where an agent stays *competent* but pursues the *wrong* goal — precisely the silent, dangerous long-horizon drift (it won't look broken). A resumed AutoFirm session that re-infers its goal from a long, drifted transcript is at maximum risk.
   - *Build implication:* the checkpoint payload (sources 08–10) stores the **original, human/manager-authored goal verbatim**; on resume the agent is re-grounded against *that stored goal*, never against its own inferred-from-context restatement. Test: a metamorphic/adversarial test where the transcript drifts toward a plausible-but-wrong objective and the resume protocol must re-assert the stored goal (kills the drift mutant).

2. **Adopt the capability-vs-goal distinction as two separate North Star/CCO checks (CLAUDE.md §2).**
   - *Build implication:* the ~30-min alignment review grades *two* axes separately: "is it still capable?" AND "is it still pursuing the *intended* goal?" — because a system can be GREEN on capability and RED on goal-fidelity. This makes "still on North Star? yes/no" a concrete goal-fidelity test, not a vibe.

3. **Adopt goal-fidelity as a fail-closed trigger (branch A7).**
   - *Build implication:* if the running agent's stated objective diverges from the stored goal beyond a threshold, **halt and escalate** (fail closed, §5.6) rather than proceed competently in the wrong direction.

## REJECT / DEFER
- **Note indirectness:** this is deep-RL, not LLM agents. Use it as the *conceptual* basis for goal-externalization; corroborate the LLM-specific manifestation with source 05 ("False Assumption", drift) — together they clear the >=2-source bar for this safety-relevant design choice.
- **Defer** RL-specific mitigations (reward design); AutoFirm's mitigation is architectural (stored-goal re-grounding), not training-time.
