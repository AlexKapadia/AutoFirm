# SUMMARY — Multi-tenant data isolation with PostgreSQL Row Level Security (AWS Database Blog)

## Full citation
- **Title:** Multi-tenant data isolation with PostgreSQL Row Level Security.
- **Author:** Michael Beardsley (AWS).
- **Year:** 18 May 2020.
- **Venue/Publisher:** AWS Database Blog.
- **URL:** https://aws.amazon.com/blogs/database/multi-tenant-data-isolation-with-postgresql-row-level-security/

## Questions informed
- **L1.A8.2** Multi-tenant data isolation (data-layer enforcement, not convention) — the canonical Pool-model RLS pattern.

## GRADE tier
**Low->Moderate.** Vendor engineering blog (Low base), up-rated because the SQL it shows is directly corroborated by the official PostgreSQL documentation (#08) — the load-bearing facts are independently verifiable.

## Key claims (exact SQL + locators)
1. **Enable RLS:** `ALTER TABLE tenant ENABLE ROW LEVEL SECURITY;`
2. **Isolation policy (session-variable form, recommended for shared login):**
   `CREATE POLICY tenant_isolation_policy ON tenant USING (tenant_id = current_setting('app.current_tenant')::UUID);`
   Application sets context per connection: `SET app.current_tenant = '[tenant_id]'`. "PostgreSQL scopes these variables to the current session," so each connection stays isolated.
3. **FORCE RLS (exact):** "the table owner bypasses RLS policies unless the table is altered with `FORCE ROW LEVEL SECURITY`" -> `ALTER TABLE tenant FORCE ROW LEVEL SECURITY;`. The app "should connect to the database as a user OTHER THAN the owner."
4. **Bypass warnings (exact):** "PostgreSQL super users and any role created with the `BYPASSRLS` attribute aren't subject to table policies." Recommended: restricted application roles (non-owners) without BYPASSRLS.
5. **Caveat (exact):** session variables "may be incompatible with server-side connection pooling such as pgBouncer" (transaction-pooling mode can leak `SET` state) — mitigate with `SET LOCAL` inside a transaction or per-transaction context-setting.

## Up/down-rate reasoning
- Up-rated: every critical SQL/behavior claim matches the official PostgreSQL docs (#08); two independent orgs (AWS + PostgreSQL) -> safety-critical claim corroborated.
- Down-rated: vendor blog, AWS-flavored; the RLS mechanics are generic Postgres, not AWS-specific, so portability holds.

## Reproducibility note
SQL reproducible against any PostgreSQL >= 9.5; the FORCE-RLS / BYPASSRLS / superuser-bypass behaviors are confirmed verbatim in the official docs (#08).
