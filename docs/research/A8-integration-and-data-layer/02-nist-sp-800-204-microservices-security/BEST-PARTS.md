# BEST-PARTS — NIST SP 800-204

## ADOPT
- **API gateway as the single, mandatory ingress/policy-enforcement point** for AutoFirm's integration layer. Every external call (agent->tool, tool->external API) traverses a gateway that does: authentication, request schema validation, rate-limiting/throttling, TLS termination, and audit logging. → this is the natural home for the OWASP "untrusted-by-default" validation (source #01) and the LLM injection guardrails (#03/#04).
- **mTLS + workload identity between internal services** (service mesh, per 800-204A). Each AutoFirm component (orchestrator, memory store, tool-runners, per-company workspaces) gets its own cryptographic workload identity; no anonymous internal traffic. → enforces A8.2 isolation and A8.3 least-privilege at the transport layer.
- **Throttling + circuit breakers** as security controls, not just reliability ones → a runaway or hijacked agent cannot DoS an external provider or rack up unbounded cost; bounds blast radius.
- **Least privilege for service-to-service auth** → each service holds only the scopes it needs (composes with RFC 8693 token exchange, #10).

## REJECT
- Nothing rejected wholesale; 800-204 is foundational. **Scope note:** it does not address LLM-specific injection — that gap is filled by #03/#04/#06, so 800-204 is the *transport/gateway* layer, not the *semantic* defense.

## CONCRETE BUILD IMPLICATION
- **Component:** `integration_gateway/` — a dedicated, single-responsibility ingress/egress service. Contract: all external I/O flows through it; direct socket access from agent code is forbidden (enforced by network policy, not convention).
- **Test it drives:** an integration test asserting no component can reach an external host except via the gateway (deny-by-default egress); a throttle test proving rate caps fail-closed.
- **Generality:** gateway+mesh blueprint is industry-agnostic — identical whether the client company is fintech, health, or retail.
