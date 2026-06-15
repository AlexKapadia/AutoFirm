# BEST-PARTS — RFC 9700 OAuth Security BCP (A8.3 credential-scoping hardening)

## ADOPT
- **Audience-restricted, sender-constrained tokens (§2.2/§4.8)** — every credential the secrets_broker issues to an agent or tool hop MUST carry an `aud` bound to the specific downstream resource, and SHOULD be sender-constrained (mTLS / DPoP). This upgrades the RFC 8693 token-exchange chain [#10] from "narrowed scope" to "narrowed scope AND useless if stolen."
- **No tokens in URLs/logs (§4.3.2)** — adopt as an independent, primary-sourced restatement of "secrets never in prompts/logs," giving the rule >=2 standards backing (NIST 800-207 [#09] + RFC 9700 [#12]).
- **Refresh-token rotation + replay detection (§4.14)** — any standing/long-lived agent credential must rotate and detect replay; prefer short-TTL per-session tokens (consistent with our ZTA design [#09]) and reserve refresh tokens for the broker only.
- **Explicit attacker model (§3)** — adopt as the threat-model input for A8.3: assume leaf agents and tools can be compromised and tokens can leak; design so a single leaked token grants neither broad scope nor cross-audience use.

## REJECT
- **Plain bearer tokens with no audience/sender constraint** — RFC 9700 deprecates relying on bearer semantics alone against capable attackers; matches our REJECT of standing god-keys [#09].

## DEFER
- DPoP vs mTLS choice for sender-constraining — a concrete L2.A8 build decision (depends on provider support); DEFER the pick, ADOPT the requirement that *one* of them is used.

## CONCRETE BUILD IMPLICATION
- **Contract:** broker-issued credential = { minimal OAuth scope [#10], audience-bound to one resource (§4.8), sender-constrained key (§2.2), short TTL, act-delegation claim [#10] }.
- **Tests it drives:** (1) a token minted for tool X is **rejected** when replayed against tool Y (wrong `aud`); (2) a token captured from logs/prompt is **rejected** without its binding key (sender-constraint); (3) no credential string ever appears in any log/prompt artifact (scanner test). These give A8.3 behavioural teeth, not just issuance-time scoping.
- **Source count:** A8.3 "per-session least-privilege + scope narrowing + leak-resistance" now rests on NIST 800-207 [#09] + RFC 8693/6749 [#10] + RFC 9700 [#12] (+ CaMeL [#04]) — >=3 independent standards bodies, safety-critical PASS.
- **Generality:** OAuth security BCP is provider-agnostic; ports to any third-party API any AutoFirm-built company integrates.
