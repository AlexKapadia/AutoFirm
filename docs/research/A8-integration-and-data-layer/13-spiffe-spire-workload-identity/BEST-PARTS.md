# BEST-PARTS — SPIFFE/SPIRE Workload Identity (A8.3 non-human identity foundation)

## ADOPT
- **SPIFFE ID as the agent/session identity primitive** — give every agent session a SPIFFE ID `spiffe://<company-trust-domain>/agent/<role>/session/<id>`. This is the stable, parseable, non-human identity that the secrets_broker scopes credentials to and that the append-only audit (A6) records as the actor — turning "which agent did this" into a first-class, verifiable fact.
- **SVID-backed sender-constraining** — use the short-lived X.509-SVID as the binding key for RFC 9700 sender-constrained tokens [#12]; a leaked OAuth token is useless without the workload's SVID key, and the SVID itself auto-rotates.
- **Workload API runtime attestation (no secrets to manage)** — adopt the attestation-then-fetch model so agents hold **no long-lived secret**; identity is delivered at runtime after the platform attests the workload. Directly satisfies "credentials runtime-injected, never in prompts/logs" [#09] with a concrete mechanism.
- **Trust-domain per company/tenant** — use the SPIFFE trust-domain as an isolation boundary so one company's agent identities cannot impersonate another's (reinforces A8.2 isolation at the identity layer).

## REJECT
- **Static API keys / shared service accounts for agents** — SPIFFE exists specifically to replace standing shared credentials with attested, short-lived identity; matches our REJECT of god-keys [#09].

## DEFER
- SPIRE deployment topology (node vs. nested SPIRE servers, federation across trust domains) — an L2.A8 operational decision; DEFER the topology, ADOPT the SPIFFE-identity contract now.

## CONCRETE BUILD IMPLICATION
- **Contract:** agent identity = SPIFFE ID (per session) -> SVID (short-lived, auto-rotated) -> used to obtain audience-bound, sender-constrained OAuth tokens [#10][#12] for each tool hop, all logged via the act delegation chain [#10].
- **Test it drives:** (1) an agent with no valid SVID **cannot** obtain any credential (fail-closed identity); (2) an SVID issued for `agent/reader` **cannot** be presented as `agent/admin` (identity not forgeable); (3) SVID TTL expiry forces rotation within the configured window (no standing credential). These give the non-human-identity layer adversarial teeth.
- **Closes open item:** the SYNTHESIS "Non-human agent identity for OAuth: evolving area" item is now grounded in a CNCF-graduated specification rather than deferred to per-provider guesswork.
- **Generality:** SPIFFE is platform/provider-agnostic (any workload, any cloud); ports to any AutoFirm-built company.
