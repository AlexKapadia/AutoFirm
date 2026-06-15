# BEST-PARTS — Hooks for AutoFirm

## ADOPT

- **`SessionStart` / `SessionEnd` / `PreToolUse` / `PostToolUse` hooks as the append-only audit
  spine.** Every hook receives `session_id`, `cwd`, `agent_id`, `agent_type`, `permission_mode`
  on stdin (claim 4) — exactly the who/when/what an immutable audit log needs (CLAUDE.md §5.6,
  L1.A6.2). Build implication: a `command`/`http` audit hook appends a signed JSONL record per
  tool call to the run ledger; this is how AutoFirm gets provenance "for free" at the substrate.
- **`PreToolUse` deterministic policy gates** (claim 3): a hook can return
  `permissionDecision: "deny"` with a reason, or rewrite args via `updatedInput`. Use for
  domain-specific guardrails (e.g. deny writes outside the tenant's directory, deny network
  egress to non-allowlisted hosts) layered on top of permission rules.
- **`Stop`/`SubagentStop` exit-2 to enforce the iterate-to-perfection loop** (CLAUDE.md §3.7):
  a Stop hook can refuse to let an agent finish until the test suite is green / mutation
  survivors are killed — the doc's own example reason is "Test suite must pass before proceeding."
  This makes "don't stop until zero issues" a substrate-enforced invariant, not a hope.
- **`mcp_tool` / `agent` hooks for security scanning** at tool boundaries (e.g. SAST/secret-scan
  on PostToolUse Edit) — feeds CLAUDE.md §5.6 SAST/DAST-in-CI and A7 oversight.

## REJECT / CRITICAL CAVEAT

- **DO NOT use hooks as AutoFirm's hard security boundary.** The doc is explicit and repeated:
  "Hooks are **fail-open by default**" — a crash/timeout/invalid-JSON lets the action proceed,
  and HTTP/`if`-filter failures fail open (claims 6, 7). This DIRECTLY CONFLICTS with CLAUDE.md
  §5.6 ("fail closed everywhere"). **Resolution (binding, A7 veto under RESEARCH-PROGRAM §5.2):**
  - Hard allow/deny MUST be expressed as **permission `deny` rules** (source 05) and **sandbox
    boundaries** (source 06), which the doc itself says to use "for hard allow/deny rules (not
    hooks)."
  - Hooks are used for **audit, validation, transformation, and the iterate-loop gate** — defense
    in depth, never the sole control.
  - Where a hook MUST gate, it must be a `command` hook using **exit 2** (the only reliably
    blocking path), wrapped so any internal error path also exits 2 (manufacture fail-closed on
    top of a fail-open primitive), and **mirrored by a permission deny rule** so the boundary
    survives a hook crash.
- **Lock hooks down with `allowManagedHooksOnly`** (claim 10) in AutoFirm's managed settings so a
  tenant/project cannot inject a hook that weakens governance.

## Concrete build implications
- Component: `audit-hook` (SessionStart/PostToolUse -> append-only signed ledger) +
  `policy-gate-hook` (PreToolUse exit-2, mirrored by permission deny) + `green-gate-hook`
  (Stop exit-2 until suite/mutation pass).
- Contract: every hard control has BOTH a permission deny rule AND (optionally) a hook; the
  permission rule is the source of truth, the hook is belt-and-braces.
- Test: kill the policy hook process mid-call and assert the permission deny rule still blocks
  (proves fail-closed does not depend on the fail-open hook). Mutation-test the exit-2 path.
