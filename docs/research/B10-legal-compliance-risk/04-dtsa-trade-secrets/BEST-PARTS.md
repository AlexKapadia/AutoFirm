# BEST-PARTS — DTSA / trade secrets

## ADOPT
- **A1. "Reasonable measures to keep secret" → concrete, testable controls.** Trade-secret status is
  **forfeited** if reasonable secrecy measures are not taken (18 U.S.C. §1839(3)). AutoFirm operationalizes
  this as enforced controls: gitignored private workspace (A6.4), least-privilege credential scoping
  (A8.3), encryption at rest, and an **append-only access log** of who touched company-confidential IP
  (CLAUDE.md §5.6). Build implication: trade-secret classification is only granted when these controls
  are provably ON — a **fail-closed legal-precondition gate**.
- **A2. Misappropriation-avoidance guardrail on data ingestion.** Because "improper means" includes
  acquiring a secret via breach of a confidentiality duty, AutoFirm's data-sourcing layer must **refuse
  to ingest** third-party confidential material lacking a lawful provenance — and must record that
  reverse-engineering / independent derivation / public sources ARE lawful (§1839(6)). Ties to L1.B4.4
  public-data-only sourcing: AutoFirm only uses **public** corporate data, which is by definition not
  misappropriation.
- **A3. Audit log doubles as litigation evidence.** The immutable audit log (A6.2) is what proves
  "reasonable measures" AND proves AutoFirm did NOT misappropriate — it is dual-purpose. Adopt the log
  schema to capture what/when/who for every IP-touching action.

## REJECT / DEFER
- **R1. REJECT treating reverse-engineering / independent derivation as risky.** The statute expressly
  excludes them from "improper means" — AutoFirm may lawfully analyze public products. Do not over-block.
- **R2. DEFER criminal-EEA exposure** (18 U.S.C. §1831-1832 economic espionage) and state-UTSA variants
  to a risk-register note — the civil DTSA path is the L1 core; criminal exposure is an edge risk flag.

## Build implication (concrete)
- **Component:** `legal/ip/trade_secret_gate.py` (precondition gate) + reuse of A6.2 audit log.
- **Contract:** `TradeSecretClaim{ asset_id, secrecy_controls: {gitignored, encrypted_at_rest,
  least_priv, access_logged}, lawful_provenance: bool }` — all booleans must be true to grant status.
- **Test (adversarial):** revoke any one secrecy control → status must be DENIED (fail-closed); ingest
  material with unlawful provenance → ingestion REFUSED; reverse-engineered public data → ALLOWED.
