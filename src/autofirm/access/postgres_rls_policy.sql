-- =============================================================================
-- AutoFirm tenant-isolation row-level-security policy (production artifact).
--
-- WHAT THIS IS
--   The committed, deployable Postgres RLS policy that the runtime applies to
--   every tenant-scoped table. It is the SQL counterpart of the Python contract
--   in autofirm.access.tenant_scoped_session_contract + in_memory_rls_backend:
--   isolation is enforced IN THE DATA LAYER (the engine), not by an app-side
--   WHERE clause that a single missing line could leak.
--
-- RESEARCH BASIS
--   docs/research/A8-integration-and-data-layer/SYNTHESIS.md (L1.A8.2),
--   primary source #08 PostgreSQL official RLS docs, corroborated by #07 AWS
--   multi-tenant RLS. Key facts encoded below:
--     * ENABLE ROW LEVEL SECURITY -> if no policy matches, a DEFAULT-DENY policy
--       applies (fail-closed).                                        [#08]
--     * The table OWNER and BYPASSRLS roles bypass RLS UNLESS FORCE ROW LEVEL
--       SECURITY is set; so we FORCE it and the app connects as a NON-OWNER,
--       NON-BYPASSRLS role.                                            [#08][#07]
--     * A policy must specify BOTH USING (read/visibility) and WITH CHECK
--       (write/modification) so a tenant can neither read nor write across the
--       boundary.                                                      [#08]
--     * Tenant context is set per-transaction via current_setting, using
--       SET LOCAL for pgBouncer transaction-pooling safety.            [#07]
--
-- SECURITY / COMPLIANCE INVARIANTS (CLAUDE.md §5.6)
--   * Fail-closed: missing tenant context -> current_setting(..., true) is NULL,
--     the predicate is false for every row, and NOTHING is visible/writable.
--   * Tenant isolation in the data layer: every row op is filtered by the engine.
--   * Least privilege: the app role is non-owner, non-BYPASSRLS, granted only
--     DML on tenant tables (no DDL, no superuser).
-- =============================================================================

-- ---------------------------------------------------------------------------
-- 1. The least-privilege application role the runtime connects as.
--    NON-owner + NON-BYPASSRLS is what makes FORCE/RLS actually bind to it.
-- ---------------------------------------------------------------------------
-- NOTE: password is injected from the secret manager at deploy time, NEVER here
--       (CLAUDE.md §5.6: secrets via env/secret-manager only, never in repo).
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'autofirm_app') THEN
    -- NOSUPERUSER + NOBYPASSRLS: this role can NEVER bypass row security.
    CREATE ROLE autofirm_app LOGIN NOSUPERUSER NOBYPASSRLS NOCREATEDB NOCREATEROLE;
  END IF;
END
$$;

-- ---------------------------------------------------------------------------
-- 2. A representative tenant-scoped table. Every tenant table MUST carry a
--    NOT NULL tenant_id and follow this exact ENABLE+FORCE+USING+WITH CHECK
--    shape; a schema-audit test fails the build for any table that does not.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS tenant_row (
  tenant_id  text NOT NULL,           -- isolation key; RLS predicate filters on this
  row_id     text NOT NULL,
  payload    text NOT NULL,
  PRIMARY KEY (tenant_id, row_id)      -- tenant is part of the key: no shared keyspace
);

-- least privilege: the app role gets ONLY row DML, never DDL/ownership.
GRANT SELECT, INSERT, UPDATE, DELETE ON tenant_row TO autofirm_app;

-- ---------------------------------------------------------------------------
-- 3. Turn RLS on AND force it for the owner too, so no connection escapes it.
-- ---------------------------------------------------------------------------
ALTER TABLE tenant_row ENABLE ROW LEVEL SECURITY;   -- default-deny once enabled [#08]
ALTER TABLE tenant_row FORCE  ROW LEVEL SECURITY;   -- owner cannot bypass either [#08]

-- ---------------------------------------------------------------------------
-- 4. The single tenant-isolation policy: USING (read) + WITH CHECK (write),
--    both keyed to the per-transaction tenant context.
--
--    current_setting('app.current_tenant', true) returns NULL when the context
--    was never set; NULL = ... is NULL (not true), so the row fails the predicate
--    -> FAIL-CLOSED: no tenant context => no rows visible and no writes allowed.
-- ---------------------------------------------------------------------------
DROP POLICY IF EXISTS tenant_isolation ON tenant_row;
CREATE POLICY tenant_isolation ON tenant_row
  FOR ALL
  TO autofirm_app
  USING      (tenant_id = current_setting('app.current_tenant', true))   -- read boundary
  WITH CHECK (tenant_id = current_setting('app.current_tenant', true));  -- write boundary

-- ---------------------------------------------------------------------------
-- 5. Per-transaction tenant context (the runtime sets this on every txn).
--    SET LOCAL scopes it to the current transaction so a pooled (pgBouncer)
--    connection cannot leak one tenant's context into another's session. [#07]
--
--    USAGE (runtime, parameterised — NEVER string-concatenated):
--        BEGIN;
--        SET LOCAL app.current_tenant = $1;   -- $1 = the active tenant id
--        ... tenant-scoped queries ...
--        COMMIT;
-- ---------------------------------------------------------------------------
