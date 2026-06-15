# BEST-PARTS — PostgreSQL Official RLS Documentation

## ADOPT
- **Default-deny on enable** — "If no policy exists for the table, a default-deny policy is used." This is the fail-closed primitive AutoFirm wants: enable RLS first, then add explicit allow policies. → standard migration order: `ENABLE` + `FORCE` before the table holds any tenant data.
- **`USING` (visibility/filter) vs `WITH CHECK` (modification/block) split** — AutoFirm's tenant policy must specify BOTH so a tenant can neither *see* nor *write* outside its boundary: `USING (tenant_id = current_tenant()) WITH CHECK (tenant_id = current_tenant())`. Omitting WITH CHECK would let a tenant INSERT/UPDATE rows tagged with another tenant's id.
- **Explicit superuser/BYPASSRLS/owner-bypass awareness** as a security invariant baked into role provisioning (the app role must be none of those).

## REJECT
- Nothing rejected — this is the authoritative mechanism spec. It is the **source-of-record** that validates the AWS blog (#07); where #07 and any blog disagree, this primary wins.

## CONCRETE BUILD IMPLICATION
- **Contract / invariant (correctness-critical):** every tenant-scoped table has RLS ENABLED + FORCED, a policy with BOTH `USING` and `WITH CHECK` on `tenant_id`, and is owned by a role distinct from the app role; no app role has BYPASSRLS.
- **Test it drives:** a schema-audit test that scans all tenant tables and FAILS the build if any lacks ENABLE+FORCE, lacks a WITH CHECK clause, or is reachable by a BYPASSRLS/owner role — turning the four exact doc guarantees into an automated gate (CLAUDE.md §3.6 tests-with-teeth).
- **Generality:** pure-Postgres semantics; portable to any AutoFirm-built company on Postgres.
