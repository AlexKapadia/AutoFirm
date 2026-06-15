# BEST-PARTS — Interface/Ada Lovelace Autonomy Classification

## ADOPT
1. **Adopt the three distinguishing dimensions (generality/scope, control, tool/environment access) as AutoFirm's per-session autonomy descriptor.**
   - *Why:* a single `autonomy_level` integer (source 01) is coarse. These three orthogonal axes let AutoFirm describe *why* a session sits at a level and gate accordingly.
   - *Build implication:* the orchestration contract for every session/subagent carries `{scope, control, tool_access}`. The **tool_access axis maps directly onto least-privilege credential scoping (CLAUDE.md §5.6, branch A8.3)** — broad web/tool access => stricter human gate.

2. **Adopt the liability-shift principle as the audit/provenance requirement.**
   - *Why:* as a session's autonomy rises, accountability shifts from "the human approved each step" to "the developer/orchestrator configured an autonomous agent." AutoFirm must record *which* it was, per action.
   - *Build implication:* the append-only audit log (branch A6.2) stamps each side-effecting action with the `autonomy_level` + which dimension granted it + whether a human approved — making post-hoc liability attribution mechanical, not reconstructed.

## REJECT / DEFER
- **Reject** importing the legal/liability *conclusions* wholesale (UK-AVA-specific). AutoFirm uses the *structure*, not the statutory allocations.
- **Defer** the Level-5 "developers bear liability" framing to the safety branch (A7) — it reinforces, but does not replace, the fail-closed Level-5 prohibition from source 01.
