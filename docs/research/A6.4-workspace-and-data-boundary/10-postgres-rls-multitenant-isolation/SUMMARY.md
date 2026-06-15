# SUMMARY — Multi-Tenant Data Isolation via Row-Level Security (data-layer enforcement)

## Full citation
- **Primary mechanism:** PostgreSQL **Row-Level Security (RLS)** — official Postgres documentation
  (https://www.postgresql.org/docs/current/ddl-rowsecurity.html).
- **Corroborating expositions:** Leapcell, *Achieving Robust Multi-Tenant Data Isolation with
  PostgreSQL Row-Level Security* (https://leapcell.io/blog/achieving-robust-multi-tenant-data-isolation-with-postgresql-row-level-security);
  Microsoft Learn, *Multitenant SaaS patterns — Azure SQL Database* (RLS section)
  (https://learn.microsoft.com/azure/azure-sql/database/saas-tenancy-app-design-patterns);
  DZone, *Multi-Tenant Data Isolation and Row Level Security*.
- **Year:** ongoing (Postgres docs current).

## Question(s) it informs
- **L1.A6.4** (and L1.A8.2) — the requirement that the data boundary / tenant (per-company)
  isolation is enforced **in the data layer, not by application convention** (CLAUDE.md §5.6).

## GRADE tier
- **Tier: Moderate–High** for the mechanism: PostgreSQL RLS is an official, documented database
  feature (primary). Corroborated independently by Microsoft (Azure SQL RLS) — two independent
  vendor primaries describing the same data-layer-enforcement pattern.

## Key claims
1. **RLS shifts tenant filtering from the application to the database engine.** Policies attached to
   tables "evaluate a condition for each row… if the condition evaluates to true, the operation is
   permitted; otherwise, it's denied" — acting "like an automatic WHERE clause on every query."
2. **Unbypassable / fail-safe-by-default:** "RLS enforcement happens before any query results are
   returned to the application, providing an unbypassable layer of security." If a developer "forgets
   the filter in a query, RLS still protects the data."
3. **Application-only isolation is the WEAKEST model:** "the shared-schema model relying entirely on
   application-layer logic offers the weakest isolation, vulnerable to programming errors that can
   lead to data leakage." → exactly why CLAUDE.md §5.6 forbids convention-based isolation.
4. **Isolation spectrum:** silo (DB-per-tenant) > schema-per-tenant > shared-schema+RLS — stronger
   isolation vs. lower cost/operability trade-off (the design choice belongs to L2.A8).

## Up/down-rate reasoning
- Up-rated: the core claim (data-layer enforcement is stronger than app-layer convention) is stated
  identically across PostgreSQL docs, Azure docs, and independent expositions — strong, consistent,
  multi-source agreement on a correctness-critical control.

## Reproducibility note
RLS behavior is verifiable: enable RLS on a table, set a `tenant_id` policy, query without the
WHERE clause, and confirm rows from other tenants are not returned (Postgres docs example).
