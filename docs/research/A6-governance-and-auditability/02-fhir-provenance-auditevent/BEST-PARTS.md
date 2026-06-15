# BEST-PARTS — FHIR Provenance/AuditEvent for AutoFirm

## ADOPT

1. **Adopt the two-record split: Provenance (lineage assertion) vs. AuditEvent (operational security log).** AutoFirm should emit BOTH for every sensitive action: a **Provenance** record (durable "this output wasGeneratedBy this activity, attributed to this agent") and an **AuditEvent** (append-only security log "agent X invoked tool Y at time T"). This cleanly separates *why an artifact exists* (CLAUDE.md §3.11 explain-every-decision) from *the tamper-evident security trail* (CLAUDE.md §5.6).

2. **Adopt AuditEvent's no-update/no-delete invariant as a hard fail-closed control.** The standard's refusal of update/delete on audit records is exactly CLAUDE.md §5.6's "immutable, append-only audit log." *Build implication:* the AutoFirm audit store rejects UPDATE/DELETE at the data layer (not by convention), corroborating tamper-evidence sources 03/04/06.

3. **Adopt the REQUIRED `recorded` instant + `agent.who` + `agent.onBehalfOf` fields as mandatory audit-contract fields.** These make "when" and "who (and on whose behalf)" non-optional — matching PROV's `actedOnBehalfOf` and giving institution-grade provenance with no nullable principals.

4. **Adopt `entity.role` enum (derivation/revision/quotation/source/removal) for memory + artifact lineage** (drives L2.A4 governed memory): a deletion is itself a logged provenance event with role `removal` — enabling deletion-verification (L1.A4.4).

5. **Adopt the optional `signature` element** as the hook for cryptographic sealing of audit records (ties to source 03/04 tamper-evidence).

## REJECT / DEFER
- **Reject adopting the full FHIR resource graph / healthcare-specific value sets.** AutoFirm is cross-industry; take the *structure and invariants*, not the clinical vocabulary.
- **Defer FHIR REST API conformance.** Only relevant if AutoFirm builds a healthcare client; the audit model is reused regardless.

## Why (cited)
FHIR's split and its no-mutate audit rule are battle-tested in a heavily regulated domain, giving AutoFirm a proven institution-grade template (CLAUDE.md §3.2) that is already W3C-PROV-interoperable (source 01).
