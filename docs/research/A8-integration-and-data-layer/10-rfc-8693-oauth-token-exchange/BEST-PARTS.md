# BEST-PARTS — RFC 8693 OAuth 2.0 Token Exchange (+ RFC 6749 scopes)

## ADOPT
- **OAuth scopes (RFC 6749 §3.3) as the least-privilege primitive** for every third-party integration AutoFirm uses on a client's behalf — request the minimum scopes, prefer read-only, tokens are revocable without password rotation. → the concrete mechanism behind A8.3 scoping for SaaS integrations (Gmail, Drive, Stripe-class APIs, etc.).
- **Token Exchange (RFC 8693) to NARROW scope across each agent->tool hop.** When authority must propagate (gateway -> backend tool, orchestrator -> sub-agent), exchange the inbound token for one with fewer scopes and a specific audience, limiting blast radius if the downstream token leaks. → the gateway (#02) performs token exchange before proxying; sub-agents never inherit the full token.
- **`act` (actor) claim for auditable delegation chains.** Represent human->orchestrator->agent->tool delegation as nested `act` claims, so every action's full delegation lineage is recorded. → feeds the A6 provenance/audit trail (who-acting-for-whom).

## REJECT / scope
- **Passing one broad token down the whole chain — REJECT.** Without exchange, a compromised leaf agent holds full upstream authority. Exchange-and-narrow is mandatory at trust boundaries.
- **Note:** OAuth was designed for human-delegated access; non-human agent identity is an evolving area — AutoFirm uses OAuth scoping/exchange where the integration supports it and falls back to dynamic-secret brokering (#09) where it does not.

## CONCRETE BUILD IMPLICATION
- **Component:** the `integration_gateway/` token-exchange step + an `act`-claim emitter feeding the audit log; scope-narrowing policy per agent role.
- **Test it drives:** a test that a downstream/leaf token carries strictly fewer scopes than its parent and the correct audience; an audit test that every privileged external action has a complete `act` delegation chain back to a human authorizer.
- **Generality:** OAuth scope+exchange is a cross-industry standard; applies to any client's third-party stack.
