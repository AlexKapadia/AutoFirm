# BEST-PARTS — SEC EDGAR APIs

## What AutoFirm ADOPTS (and the build implication)

1. **SEC EDGAR is AutoFirm's primary REAL public-financial-data source for the §3.12 validation gate.** It is free, keyless, XBRL-structured, and authoritative (the regulator's own filings). Build implication for `L2.B4`: an `edgar_client` module that pulls `companyfacts/CIK##########.json` and maps XBRL `us-gaap` concepts (Revenues, NetIncomeLoss, Assets, Liabilities, StockholdersEquity, CashAndCashEquivalents, etc.) into AutoFirm's typed 3-statement contract. The DCF/CLV engines then run on real filings, not synthetic data.

2. **The Fair-Access policy becomes fail-closed client invariants** (CLAUDE §5.6): (a) the client MUST send a descriptive `User-Agent: <app> <contact-email>` header — absent it, the request is refused *before* sending (fail-closed), since EDGAR returns 403 anyway; (b) a **token-bucket rate limiter capped at <= 10 req/s** is mandatory and non-bypassable. Build implication: these are enforced in code with adversarial tests (e.g. a test that the client refuses to issue a request with an empty User-Agent; a test that 11 rapid calls are throttled to <=10/s).

3. **Frames API for cross-company / peer-set assembly.** The `frames` endpoint returns one fact per entity for a calendrical period — ideal for building the comparable-firm peer sets the relative-valuation engine (source 02) needs. Build implication: `frames/us-gaap/<Concept>/USD/CY2025.json` -> peer multiples across an industry, feeding the harmonic-mean multiple aggregation.

4. **Period-format discipline** (`CY####`, `CY####Q#`, `CY####Q#I`) maps directly onto the model's period typing (annual vs quarterly vs instantaneous/point-in-time). Instantaneous (`I`) concepts are balance-sheet items; duration concepts are income/cash-flow items — a typed distinction that prevents mixing stocks and flows (a real modeling bug).

5. **Provenance for the audit log.** Every datapoint carries accession number + fiscal year + period + form type. Build implication: AutoFirm records the SEC accession number as the provenance key in its append-only audit log (CLAUDE §5.6 / ties to L1.A6 governance) — every number in a valuation traces back to a specific filing.

## What AutoFirm REJECTS (and why)
- **Reject scraping the EDGAR HTML/full-text UI when the JSON API exists** — the structured `data.sec.gov` API is faster, lower-risk, and policy-blessed; HTML scraping risks the rate-block and brittle parsing.
- **Reject hard-coding a single CIK or company** — the client is parameterized by CIK/ticker so it generalizes across the entire industry panel (overfitting guard, CLAUDE §3.9).

## Generality check
EDGAR covers all SEC-reporting US issuers and foreign filers (20-F/40-F/6-K), spanning every industry on the B12 panel. For non-US/private firms the same contract is fed by other public registries (Companies House, etc.) — the *contract* is general; the *adapter* varies (documented as a boundary in SYNTHESIS).
