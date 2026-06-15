# BEST-PARTS — OWASP LLM Prompt Injection Prevention Cheat Sheet

## ADOPT
- **Least privilege for LLM tooling** — "read-only DB accounts where possible; restrict API access scopes." → AutoFirm agents get the narrowest tool scopes (composes with RFC 8693 token exchange #10 and ZTA per-session creds #09). Read-only by default; write/execute scopes are explicitly granted per task.
- **Human-in-the-loop for high-risk operations** — approval gates triggered on sensitive keywords / high-impact actions. → drives a `requires_human_approval` policy on consequential tools (payments, data deletion, external sends), aligning with CLAUDE.md §1 autonomy gates and A7 HITL.
- **Segregate trusted/untrusted content + structured separation** — corroborates dual-LLM (#03). → instruction/data separation is mandatory in prompt construction.
- **Treat LLM output as untrusted** — "a guardrail LLM is itself susceptible to injection." → AutoFirm does NOT rely on an LLM guardrail alone; the non-LLM capability interpreter (#04) is the real enforcement boundary.
- **Output encoding/sanitization** of rendered web/doc content.

## REJECT / DEFER
- **LLM-only guardrails as the primary defense — REJECT.** The cheat sheet itself warns guardrail LLMs are injectable and that "existing defensive approaches have significant limitations against persistent attackers." AutoFirm treats input/output filtering as defense-in-depth layers, not the load-bearing control (which is architectural — dual-LLM + capabilities).

## CONCRETE BUILD IMPLICATION
- **Contract:** a tool-permission manifest per agent role (default read-only; scopes explicitly elevated) + a `high_risk_action` policy gating HITL approval.
- **Test it drives:** a red-team suite confirming (a) agents cannot exceed their declared scopes, (b) high-risk actions are blocked without approval, (c) an injected "ignore instructions" payload cannot bypass the non-LLM enforcement.
- **Generality:** permission-manifest + HITL-gate model is industry-agnostic.
