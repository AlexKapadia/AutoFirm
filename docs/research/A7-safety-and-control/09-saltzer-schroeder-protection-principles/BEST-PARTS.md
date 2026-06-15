# BEST-PARTS — Saltzer & Schroeder (1975)

## ADOPT (these are the bedrock of AutoFirm's A7 fail-closed/least-privilege answer)
1. **Fail-safe defaults = AutoFirm's fail-closed default (CLAUDE.md §5.6 verbatim alignment).** "Permission rather than exclusion": an agent has NO capability until one is explicitly granted; when a permission/key/check is missing or ambiguous, **refuse** (CLAUDE.md §5.6 "fail closed"). *Build:* the A7 policy engine denies by default; an absent capability tag (source 05) = deny, never allow.
2. **Least privilege = per-agent scoped credentials.** Each subagent operates with the minimum tool/data/API set its brief requires (CLAUDE.md §5.6 "least privilege: each component gets its own scoped credentials. No shared god-keys."). *Build:* subagent dispatch attaches a capability set scoped to the task; the orchestrator never hands a worker more than it needs (progressive disclosure, CLAUDE.md §4.1).
3. **Complete mediation = check every tool call, every time.** No cached "already-authorized" shortcut; every privileged action re-checks authority against the current capability/policy. *Build:* the A7 layer intercepts every tool invocation (corroborates source 10 "runtime monitoring / verify before each invocation").
4. **Separation of privilege = two-key for high-risk/irreversible actions.** Realizes OWASP #5 / challenge-response (sources 02, 07): irreversible spend/legal/delete actions need a second condition (HITL or a second agent's sign-off). *Build:* high-risk actions require orchestrator-grant + HITL, not a single agent's decision.
5. **Economy of mechanism + psychological acceptability.** Keep the security layer small/auditable (CLAUDE.md §5.2 simplicity, §5.7 <=300-line files) and usable, so it is not bypassed.

## REJECT / DEFER
- Nothing to reject — these are timeless principles. Note: they are *principles*, not mechanisms; pair with the agent-specific capability mechanism (source 05) and runtime enforcement (source 10).

## Concrete build implications
- These eight principles are the **named, citable foundation** of AutoFirm's A7 doctrine — every fail-closed/least-privilege control in the threat model cites Saltzer & Schroeder (1975) as its primary authority, satisfying DEPTH-RUBRIC §1 (a safety-critical principle backed by the primary source + corroboration).
- Directly maps: fail-safe defaults -> §5.6 fail-closed; least privilege -> §5.6 scoped creds; complete mediation -> intercept-every-tool-call; separation of privilege -> HITL two-key.
