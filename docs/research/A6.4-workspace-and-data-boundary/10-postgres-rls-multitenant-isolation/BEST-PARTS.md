# BEST-PARTS — Data-Layer Isolation (RLS) → AutoFirm

## ADOPT
1. **Enforce per-company (tenant) isolation in the data layer, not by agent convention.** AutoFirm's
   private store for each company's data uses **data-layer-enforced isolation** (RLS policies keyed
   on `company_id`, or schema/DB-per-company for high-sensitivity companies). This is the direct
   operationalization of CLAUDE.md §5.6 "enforce isolation in the data layer, not by convention" and
   the database half of the A6.4 boundary (the git half is sources 01/05/08; this is the store half).
   **Build implication:** every query to the private store carries a tenant context the DB enforces;
   a query that forgets the filter still returns nothing cross-company (fail-safe).
2. **Default-deny posture:** RLS denies rows unless a policy permits them — matches CLAUDE.md §5.6
   "deny by default / fail closed". Adopt as the store's baseline.
3. **Isolation tier by company sensitivity (high-water-mark, source 02):** shared-schema+RLS for
   ordinary companies; schema- or DB-per-company for HIGH-confidentiality companies (regulated
   finance/health panel rows, QUESTION-ONTOLOGY B12). The choice itself is an L2.A8 experiment, but
   A6.4 fixes the *principle*: isolation is a data-layer control.

## REJECT / QUALIFY
- **Reject application/agent-layer-only tenant filtering** (a "remember to add `WHERE company_id`"
  convention) — named the weakest, leak-prone model by the sources; forbidden by §5.6.
- **Qualify RLS pitfalls:** superuser/`BYPASSRLS` roles and `FORCE ROW LEVEL SECURITY` for table
  owners must be configured, or the policy is silently bypassed — the custodian (source 07) owns
  this hardening.

## Concrete build implication
- **Component:** `private-store` with RLS (or schema/DB-per-company) keyed on `company_id`,
  encryption-at-rest (source 09), default-deny.
- **Contract:** no cross-company row is reachable without an explicit, audited, owner-authorized
  cross-tenant operation; the agent layer cannot disable RLS.
- **Test (tests-with-teeth):** a red-team test that runs every read path with a *missing/forged*
  tenant context and asserts ZERO cross-company rows leak (boundary-exact, fail-closed),
  mutation-tested so a weakened policy is killed (CLAUDE.md §3.6).
