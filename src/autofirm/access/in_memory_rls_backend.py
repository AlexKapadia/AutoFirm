"""In-memory RLS backend: the deterministic Python mirror of the Postgres policy.

What this does
--------------
:class:`InMemoryRlsBackend` is a synthetic, no-network store that enforces the same
row-level-security semantics as the committed Postgres policy, so the isolation
property can be proven in fast unit/property tests without a database.

It implements the four
:class:`~autofirm.access.tenant_scoped_session_contract.RlsBackend` operations such
that each enforces the policy clause it mirrors:

* ``select`` / ``update`` / ``delete`` — apply the **USING** clause: a row is
  visible only when ``row.tenant_id == active_tenant``; anything else is invisible
  (returns ``None`` / ``False``), exactly as RLS hides non-owned rows.
* ``insert`` — applies the **WITH CHECK** clause: a row whose ``tenant_id`` differs
  from the active tenant is rejected (raises), mirroring RLS blocking a write that
  would land outside the writer's boundary.

Why it exists / where it sits
-----------------------------
Research ``A8.../SYNTHESIS.md`` L1.A8.2: the Postgres policy uses ``ENABLE`` +
``FORCE ROW LEVEL SECURITY`` with ``USING (tenant_id = current_setting(...))`` and
``WITH CHECK (...)``. This class is the in-process analogue used as the fake in
unit tests (no real DB / network), so the cross-tenant denial property is asserted
against behaviour identical to production's.

Security / compliance invariants upheld (CLAUDE.md §5.6)
-------------------------------------------------------
* **Tenant isolation in the data layer:** visibility and modification are decided
  here by ``row.tenant_id == active_tenant``; the caller cannot override it.
* **Fail closed:** an insert whose row tenant != active tenant is *rejected*
  (``CrossTenantWriteRejected``), never silently re-tagged; a non-visible row is
  never returned or modified.
* **Default deny:** an unknown row id, or a row owned by another tenant, yields
  "not found" -- there is no path that leaks a foreign row.
"""

from __future__ import annotations

from autofirm.access.tenant_scoped_session_contract import TenantRow

__all__ = ["CrossTenantWriteRejected", "InMemoryRlsBackend"]


class CrossTenantWriteRejected(Exception):
    """Raised when an insert's row tenant != active tenant (the WITH CHECK block).

    Mirrors Postgres raising on a ``WITH CHECK`` violation; carries only tenant ids
    (no payload) so the refusal is debuggable without leaking row content.
    """


class InMemoryRlsBackend:
    """A synthetic store enforcing USING + WITH CHECK row-level security in memory.

    Rows are keyed by ``(tenant_id, row_id)`` so two tenants may legitimately reuse
    the same ``row_id`` without collision, and a lookup with the wrong tenant simply
    misses -- there is no shared keyspace a tenant could probe to reach another's
    row.
    """

    def __init__(self) -> None:
        """Start with an empty store. State lives only in process memory (synthetic)."""
        # Keyed by (tenant_id, row_id): the tenant is part of the key, so a query
        # under the wrong tenant structurally cannot hit another tenant's row.
        self._rows: dict[tuple[str, str], TenantRow] = {}

    def insert(self, active_tenant: str, row: TenantRow) -> None:
        """Insert ``row`` only if it is owned by ``active_tenant`` (WITH CHECK)."""
        # fail-closed WITH CHECK: a writer may only insert rows it will own; a
        # mismatched tenant is rejected, never silently re-stamped.
        if row.tenant_id != active_tenant:
            raise CrossTenantWriteRejected(
                f"insert blocked: active tenant {active_tenant!r} "
                f"may not write a row owned by {row.tenant_id!r}"
            )
        self._rows[(active_tenant, row.row_id)] = row

    def select(self, active_tenant: str, row_id: str) -> TenantRow | None:
        """Return the ``active_tenant``-owned row with ``row_id``, else None (USING)."""
        # USING: the tenant is part of the key, so this only ever returns a row the
        # active tenant owns; a foreign row is invisible (default deny -> None).
        return self._rows.get((active_tenant, row_id))

    def update(self, active_tenant: str, row_id: str, payload: str) -> bool:
        """Update an ``active_tenant``-owned row; False if not visible (USING)."""
        key = (active_tenant, row_id)
        existing = self._rows.get(key)
        # USING: only a row visible to the active tenant can be updated; a foreign
        # or missing row is not visible -> no-op, report False (default deny).
        if existing is None:
            return False
        # Re-stamp with the same tenant (frozen model) -- ownership cannot change.
        self._rows[key] = TenantRow(
            tenant_id=active_tenant, row_id=row_id, payload=payload
        )
        return True

    def delete(self, active_tenant: str, row_id: str) -> bool:
        """Delete an ``active_tenant``-owned row; False if not visible (USING)."""
        key = (active_tenant, row_id)
        # USING: a foreign/missing row is invisible to this tenant -> nothing to
        # delete, report False; a tenant can never delete another's row.
        if key not in self._rows:
            return False
        del self._rows[key]
        return True
