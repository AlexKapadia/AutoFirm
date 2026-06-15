# BEST-PARTS — PostgreSQL RLS for Multi-Tenant Isolation (AWS pattern)

## ADOPT
- **Pool-model + Row-Level Security as the default tenant-isolation mechanism** for shared AutoFirm tables. Isolation is enforced **in the database engine**, not in application code — this is precisely CLAUDE.md §5.6's "enforce isolation in the data layer, not by convention." → drives the `tenant_id` column + `CREATE POLICY tenant_isolation USING (tenant_id = current_setting('app.current_tenant')::uuid)` on every tenant-scoped table.
- **`FORCE ROW LEVEL SECURITY` + non-owner application role** — MANDATORY. The app must connect as a restricted, non-owner role WITHOUT `BYPASSRLS`. → fail-closed: even a SQL-injection or logic bug cannot read another tenant's rows because the engine filters first.
- **Session-variable tenant context** set per connection/transaction (`SET LOCAL app.current_tenant = ...` inside a transaction to be pgBouncer-safe).
- **Pooled model for low-margin/high-scale clients; reserve Silo (dedicated DB) for heavy-compliance/high-ACV** — the silo/bridge/pool selection becomes an AutoFirm per-company configuration knob.

## REJECT
- **App-layer-only `WHERE tenant_id = ?` filtering as the sole isolation — REJECT.** One missing clause leaks all tenants; RLS makes the boundary engine-enforced and default-deny. App filtering may stay as defense-in-depth but is never the only line.
- **Connecting as the table owner / superuser for app traffic — REJECT** (owner + BYPASSRLS roles silently bypass policies).

## CONCRETE BUILD IMPLICATION
- **Component:** `data_layer/tenant_isolation/` — migration helpers that, for every tenant table, enable+FORCE RLS and attach the standard policy; a connection wrapper that always sets `app.current_tenant` per transaction and forbids the owner role.
- **Test it drives (correctness-critical):** a property/adversarial test that, with tenant A's context set, NO query (SELECT/UPDATE/DELETE, even crafted) returns or mutates tenant B's rows; a test that the app role lacks BYPASSRLS and is not the table owner; a pgBouncer-mode test proving context doesn't leak across pooled connections.
- **Generality:** mechanism is industry-agnostic; the silo/bridge/pool choice parameterizes by compliance weight (panel-safe across fintech/health vs. SaaS/retail).
