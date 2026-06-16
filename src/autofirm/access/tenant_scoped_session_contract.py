"""Tenant-scoped data session: the interface that makes RLS testable & deterministic.

What this does
--------------
Models multi-tenant row-level security as a deterministic core behind one
interface so it can be tested without a database AND mapped 1:1 onto the committed
Postgres policy (:mod:`autofirm.access` ships ``postgres_rls_policy.sql``).

* :class:`TenantRow` — a stored row, tagged with the ``tenant_id`` that owns it.
* :class:`RlsBackend` — the Protocol a concrete store implements: ``insert`` /
  ``select`` / ``update`` / ``delete``, each taking the *active* ``tenant_id`` so
  the boundary is enforced in the store, never by the caller remembering to filter.
* :class:`TenantScopedSession` — a thin handle bound to exactly one tenant; every
  operation it exposes forwards that one tenant id to the backend. There is no API
  on the session to read or write another tenant's rows.

Why it exists / where it sits
-----------------------------
Research ``A8.../SYNTHESIS.md`` L1.A8.2: isolation must live "in the data layer,
not by convention". The Postgres deployment enforces this with ``ENABLE`` +
``FORCE ROW LEVEL SECURITY`` and ``USING`` + ``WITH CHECK`` on
``current_setting('app.current_tenant')``. This module is the in-process mirror of
that contract: a tenant-bound session that *structurally* cannot reach across the
boundary, so the same adversarial/property tests that prove isolation here describe
exactly what the SQL policy must guarantee in production.

Security / compliance invariants upheld (CLAUDE.md §5.6)
-------------------------------------------------------
* **Tenant isolation in the data layer:** the active tenant is supplied to every
  backend call; the backend filters/blocks by it. A session is locked to one
  tenant at construction and exposes no cross-tenant operation.
* **Fail closed:** a blank tenant id is refused at session construction; an
  ``update``/``insert`` of a row tagged with a different tenant is rejected by the
  backend (the ``WITH CHECK`` analogue), never silently coerced.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, field_validator

__all__ = [
    "RlsBackend",
    "TenantRow",
    "TenantScopedSession",
]


class TenantRow(BaseModel):
    """One stored row, owned by exactly one tenant.

    ``tenant_id`` is the isolation key -- the analogue of the ``tenant_id`` column
    the Postgres RLS policy filters on. ``row_id`` is unique *within* a tenant;
    ``payload`` is opaque synthetic data (no real PII ever enters tests).
    """

    model_config = ConfigDict(frozen=True)

    tenant_id: str  # tenant isolation: the owning tenant; RLS filters on this
    row_id: str  # unique within a tenant
    payload: str  # opaque synthetic content

    @field_validator("tenant_id", "row_id")
    @classmethod
    def _non_empty(cls, value: str) -> str:
        # fail-closed: a blank tenant_id/row_id would make ownership ambiguous.
        if not value or not value.strip():
            raise ValueError("tenant_id and row_id must be non-empty")
        return value


@runtime_checkable
class RlsBackend(Protocol):
    """The data store contract; every method takes the ACTIVE tenant and enforces it.

    This is the seam the Postgres policy implements in SQL and the in-memory fake
    implements in Python. The active ``tenant_id`` is always an explicit argument so
    isolation is enforced *inside* the store, matching ``current_setting`` +
    ``USING``/``WITH CHECK`` -- a caller can never widen its own reach.
    """

    def insert(self, active_tenant: str, row: TenantRow) -> None:
        """Insert ``row``; reject if ``row.tenant_id`` != ``active_tenant`` (WITH CHECK)."""
        ...

    def select(self, active_tenant: str, row_id: str) -> TenantRow | None:
        """Return the row owned by ``active_tenant`` with ``row_id``, else None (USING)."""
        ...

    def update(self, active_tenant: str, row_id: str, payload: str) -> bool:
        """Update an ``active_tenant``-owned row; return False if not visible (USING)."""
        ...

    def delete(self, active_tenant: str, row_id: str) -> bool:
        """Delete an ``active_tenant``-owned row; return False if not visible (USING)."""
        ...


class TenantScopedSession:
    """A data handle locked to ONE tenant; cannot reach another tenant's rows.

    Constructed with the active tenant id and a backend. Every method forwards that
    single tenant id to the backend, so the boundary is enforced by the store on
    every call and the session offers no API to cross it.
    """

    def __init__(self, tenant_id: str, backend: RlsBackend) -> None:
        """Bind the session to exactly ``tenant_id`` (non-empty, fail-closed)."""
        # fail-closed: a session with no tenant context could see everything; refuse.
        if not tenant_id or not tenant_id.strip():
            raise ValueError("TenantScopedSession requires a non-empty tenant_id")
        # tenant isolation: this is the ONLY tenant this session will ever act as.
        self._tenant_id = tenant_id
        self._backend = backend

    @property
    def tenant_id(self) -> str:
        """The single tenant this session is locked to (read-only)."""
        return self._tenant_id

    def insert(self, row_id: str, payload: str) -> TenantRow:
        """Insert a row OWNED BY THIS SESSION'S TENANT (the only tenant it can write)."""
        # tenant isolation: the row is stamped with this session's tenant; the
        # backend's WITH CHECK analogue refuses any other ownership.
        row = TenantRow(tenant_id=self._tenant_id, row_id=row_id, payload=payload)
        self._backend.insert(self._tenant_id, row)
        return row

    def select(self, row_id: str) -> TenantRow | None:
        """Return this tenant's row with ``row_id``, or None (never another tenant's)."""
        return self._backend.select(self._tenant_id, row_id)

    def update(self, row_id: str, payload: str) -> bool:
        """Update this tenant's row; False if it is not visible to this tenant."""
        return self._backend.update(self._tenant_id, row_id, payload)

    def delete(self, row_id: str) -> bool:
        """Delete this tenant's row; False if it is not visible to this tenant."""
        return self._backend.delete(self._tenant_id, row_id)
