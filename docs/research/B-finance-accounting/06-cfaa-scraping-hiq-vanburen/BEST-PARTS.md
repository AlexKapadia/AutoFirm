# BEST-PARTS — CFAA / data-access legality

## What AutoFirm ADOPTS (and the build implication)

1. **A codified, fail-closed data-access policy gate for the §3.12 public-data-only validation.** The legal line is precise: public, unauthenticated data is accessible (hiQ/Van Buren), but auth-walls, ToS breaches, and personal/PII data are NOT. Build implication: a `public_data_policy` guard that, before any external fetch, asserts: (a) the source requires **no login/authentication** (no gate to bypass); (b) the fetch respects the source's documented programmatic-access terms (e.g. SEC Fair-Access User-Agent + 10 req/s, source 05; robots/ToS where binding); (c) the payload contains **no real PII / client / confidential deal data** (CLAUDE §3.12 hard boundary). Any ambiguity -> **refuse** (fail-closed, CLAUDE §5.6).

2. **The "gates-up-or-down" rule becomes the decision predicate.** Build implication: classify each prospective source as gate-up (public, no auth) or gate-down (auth required / paywalled / personal). Only gate-up corporate/financial sources (SEC EDGAR, Companies House, public filings, public market data) are allowed into tests and validation; gate-down sources are categorically rejected for the autonomous path.

3. **Separate the CFAA question from the ToS/privacy questions.** Because hiQ ultimately settled on ToS/contract grounds even after winning the CFAA point, AutoFirm must treat **ToS and data-protection law as independent constraints**, not subsumed by "it's public." Build implication: the policy gate has three independent checks (CFAA-style access, contract/ToS, privacy/GDPR-CCPA), all of which must pass; this is an auditable, logged decision (ties to L1.A6 provenance + L1.B10 legal playbook).

4. **PII boundary is hard and synthetic-only.** Real public *corporate* data (filings, registries, market data) is allowed; real PII / client / confidential documents are NEVER used in tests or validation — anything sensitive stays synthetic (CLAUDE §3.12 binding). Build implication: a content classifier / allowlist enforces that only corporate-entity public data enters the real-data path; PII detection triggers a fail-closed refusal.

## What AutoFirm REJECTS (and why)
- **Reject "it's on the internet so it's fair game."** Van Buren/hiQ narrow the *CFAA* only; ToS, copyright, and privacy law still bind. Treating public-availability as blanket permission is a compliance defect.
- **Reject scraping behind any authentication wall in the autonomous path** — that is squarely the gate-down case the courts did NOT protect; it requires explicit human authorization and lawful credentials (least-privilege, CLAUDE §5.6).
- **Reject reliance on a single jurisdiction's case law as global truth** — hiQ is 9th-Circuit US; non-US operations need local legal review (documented boundary, not silently assumed).

## Generality check
The policy gate is industry-agnostic: it operates on source properties (auth? ToS? PII?), not on the company being modeled, so it applies uniformly across the B12 panel and across jurisdictions (with the explicit caveat that the case law is US/9th-Cir. and local review is required elsewhere).
