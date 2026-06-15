# SUMMARY — PostgreSQL Official Documentation: Row Security Policies (5.9 / ddl-rowsecurity)

## Full citation
- **Title:** PostgreSQL Documentation — "Row Security Policies" (Chapter 5.9, ddl-rowsecurity); CREATE POLICY reference.
- **Author/Org:** The PostgreSQL Global Development Group.
- **Year:** current (versioned; behavior stable since PostgreSQL 9.5, 2016).
- **Venue/Publisher:** postgresql.org official documentation.
- **URL:** https://www.postgresql.org/docs/current/ddl-rowsecurity.html · CREATE POLICY: https://www.postgresql.org/docs/current/sql-createpolicy.html

## Questions informed
- **L1.A8.2** Multi-tenant data isolation enforced in the data layer (the authoritative primary for RLS semantics).

## GRADE tier
**High.** Official primary documentation of the database engine itself — authoritative source of record for RLS behavior.

## Key claims (exact quotes + locators)
1. **Default-deny once enabled (exact):** "When row security is enabled on a table (with ALTER TABLE ... ENABLE ROW LEVEL SECURITY), all normal access to the table for selecting rows or modifying rows must be allowed by a row security policy. If no policy exists for the table, a default-deny policy is used, meaning that no rows are visible or can be modified."
2. **No policy => all rows visible BEFORE enabling (exact):** "By default, tables do not have any policies, so that if a user has access privileges to a table according to the SQL privilege system, all rows within it are equally available for querying or updating."
3. **Superuser/BYPASSRLS bypass (exact):** "Superusers and roles with the BYPASSRLS attribute always bypass the row security system when accessing a table."
4. **Owner bypass + FORCE (exact):** "Table owners normally bypass row security as well, though a table owner can choose to be subject to row security with ALTER TABLE ... FORCE ROW LEVEL SECURITY."
5. **USING vs WITH CHECK (exact):** "Separate expressions may be specified to provide independent control over the rows which are visible and the rows which are allowed to be modified." USING controls visibility (filter); WITH CHECK controls modification (block) — illustrated by the `user_mod_policy` example.

## Up/down-rate reasoning
- Up-rated: this IS the primary; no indirection. Used as the source-of-record that grades #07 up.
- Down-rate (scope only): documents the mechanism, not the multi-tenant *application* of it — pair with #07 for the tenant pattern.

## Reproducibility note
All five quotes are on ddl-rowsecurity.html / sql-createpolicy.html for the current version; verbatim-stable across recent major versions.
