# BEST-PARTS — NIST SP 800-207 Zero Trust Architecture

## ADOPT
- **Per-session, least-privilege credentials for every agent run.** An AutoFirm agent session = a ZTA subject: it receives credentials scoped to exactly the task, time-bound to the session, and revoked at session end — never standing/persistent access. → drives the secrets model for A8.3: short-lived, task-scoped tokens issued at run start, expired/revoked at run end (composes with HashiCorp-Vault-style dynamic secrets and RFC 8693 narrowing #10).
- **Dynamic, context-informed policy (PE/PA/PEP).** Each consequential tool call is an access request evaluated by a Policy Engine against context (which agent, which tenant, which task, recent behavior). → the capability interpreter (#04) + integration gateway (#02) jointly play PEP; a policy service plays PE/PA.
- **Never trust by location; assume breach; verify explicitly.** No agent or internal service is trusted by virtue of being "inside" — every hop authenticates (pairs with mTLS #02 and tenant RLS #07/#08).

## REJECT / scope
- **Standing, broad agent credentials — REJECT.** The anti-pattern 800-207 exists to kill: long-lived god-keys shared across agents. AutoFirm must never issue an agent its user's full permission set or a non-expiring key.
- 800-207 is a model, not an implementation — it defines WHAT (per-session least privilege, dynamic policy); the HOW comes from a secrets manager + token exchange (#10).

## CONCRETE BUILD IMPLICATION
- **Component:** `secrets_broker/` — issues per-session, least-privilege, short-TTL credentials to agent runs; runtime-injects them (never in prompts/logs); auto-revokes at session end. Decisions logged to the append-only audit (A6.2).
- **Test it drives:** a test proving an agent cannot use a credential outside its session window or beyond its granted scope; a test that no secret appears in logs/prompts (secret-scanning gate, CLAUDE.md §5.6).
- **Generality:** ZTA per-session model is industry- and size-agnostic.
