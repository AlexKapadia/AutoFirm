# BEST-PARTS — CSA Autonomy Levels

## ADOPT
1. **Adopt the 6-level (0–5) autonomy ladder as AutoFirm's declared operating-level vocabulary.**
   - *Why:* AutoFirm's CLAUDE.md already distinguishes "confirm the plan first" vs. "run autonomously / you can walk away." Mapping those onto explicit levels lets every spawned agent/session carry a declared `autonomy_level` field instead of an implicit mode.
   - *Build implication:* add an `autonomy_level ∈ {0..5}` attribute to the orchestration contract for every session/subagent. The orchestrator default = **Level 3 (Conditional)**: act within boundaries, escalate on out-of-bounds. "Run autonomously" raises specific phases to **Level 4** but **never Level 5**.

2. **Adopt the in-/on-/out-of-the-loop oversight mapping as the gate-placement rule.**
   - *Build implication:* §4.9 HITL gates and §3.13 commit-at-every-gate become level-dependent — Level ≤2 phases require human approval before side-effecting tool calls; Level 3 only escalates on boundary breach; Level 4 runs monitored with the North Star/CCO heartbeat (§2) as the "on-the-loop" observer.

3. **Adopt the explicit Level-5 prohibition.**
   - *Why:* directly aligns with CLAUDE.md §5.6 fail-closed + §3.2 institution-grade. An agent that can "set goals and modify its own behavior" with only strategic oversight is exactly what the kill-switch and least-privilege controls must forbid.
   - *Build implication:* hard-code an invariant that no AutoFirm session may self-elevate to Level 5; goal-setting stays with the human principal or an audited management agent under §2 ORG. Test: a property test asserting no role can author a role-spec granting itself unbounded goal-modification.

## REJECT / DEFER
- **Reject** treating the levels as a *capability* ladder (higher = better). Per CSA and the Swarmia practitioner piece, higher autonomy is not always desirable; AutoFirm should choose the **lowest level that fits** the task risk (mirrors the global settings-hierarchy "lowest scope that fits" rule).
- **Defer** using CSA's framing as a sole citation for any safety-critical control — it is Low-tier; corroborate with sources 02/03 and the safety branch (A7).
