"""Adversarial + stateful property tests: tenant isolation holds in the data layer.

The headline guarantee: over ARBITRARY interleavings of tenant operations, one
tenant can NEVER read, update, or delete another tenant's row, and can never
insert a row it would not own. Models USING (visibility) + WITH CHECK (write)
exactly as the committed Postgres policy does. Synthetic in-memory store; no DB.
"""

from __future__ import annotations

import pytest
from hypothesis import given
from hypothesis import strategies as st
from hypothesis.stateful import RuleBasedStateMachine, invariant, rule

from autofirm.access.in_memory_rls_backend import (
    CrossTenantWriteRejected,
    InMemoryRlsBackend,
)
from autofirm.access.tenant_scoped_session_contract import (
    TenantRow,
    TenantScopedSession,
)

_tenant_names = st.sampled_from(["tenant-a", "tenant-b", "tenant-c"])
_row_ids = st.sampled_from(["r1", "r2", "r3"])
_payloads = st.text(min_size=0, max_size=12)


def _session(backend: InMemoryRlsBackend, tenant: str) -> TenantScopedSession:
    return TenantScopedSession(tenant, backend)


# --- Direct adversarial cases -----------------------------------------------


@pytest.mark.security
def test_tenant_cannot_read_another_tenants_row() -> None:
    backend = InMemoryRlsBackend()
    _session(backend, "tenant-a").insert("r1", "a-secret-payload")
    # tenant isolation: B's session must NOT see A's row (USING).
    assert _session(backend, "tenant-b").select("r1") is None
    # ...but A still sees its own.
    assert _session(backend, "tenant-a").select("r1").payload == "a-secret-payload"


@pytest.mark.security
def test_tenant_cannot_update_another_tenants_row() -> None:
    backend = InMemoryRlsBackend()
    _session(backend, "tenant-a").insert("r1", "original")
    # USING: the row is invisible to B, so the update is a no-op (False).
    assert _session(backend, "tenant-b").update("r1", "hijacked") is False
    # A's data is untouched.
    assert _session(backend, "tenant-a").select("r1").payload == "original"


@pytest.mark.security
def test_tenant_cannot_delete_another_tenants_row() -> None:
    backend = InMemoryRlsBackend()
    _session(backend, "tenant-a").insert("r1", "keep-me")
    assert _session(backend, "tenant-b").delete("r1") is False
    assert _session(backend, "tenant-a").select("r1") is not None  # still there


@pytest.mark.security
def test_same_row_id_across_tenants_does_not_collide() -> None:
    backend = InMemoryRlsBackend()
    _session(backend, "tenant-a").insert("r1", "A-data")
    _session(backend, "tenant-b").insert("r1", "B-data")  # same row_id, different tenant
    assert _session(backend, "tenant-a").select("r1").payload == "A-data"
    assert _session(backend, "tenant-b").select("r1").payload == "B-data"


@pytest.mark.security
def test_backend_rejects_cross_tenant_insert_with_check() -> None:
    backend = InMemoryRlsBackend()
    # WITH CHECK: active tenant A may not insert a row owned by B (raises).
    foreign_row = TenantRow(tenant_id="tenant-b", row_id="r1", payload="x")
    with pytest.raises(CrossTenantWriteRejected):
        backend.insert("tenant-a", foreign_row)


@pytest.mark.security
def test_session_requires_non_empty_tenant() -> None:
    backend = InMemoryRlsBackend()
    # fail-closed: a tenant-less session could see everything -> refuse construction.
    with pytest.raises(ValueError):
        TenantScopedSession("", backend)
    with pytest.raises(ValueError):
        TenantScopedSession("   ", backend)


# --- PROPERTY: a victim row is invisible to every other tenant --------------


@pytest.mark.property
@given(
    owner=_tenant_names,
    other=_tenant_names,
    row_id=_row_ids,
    payload=st.text(min_size=1, max_size=12),
)
def test_property_only_owner_sees_its_row(
    owner: str, other: str, row_id: str, payload: str
) -> None:
    backend = InMemoryRlsBackend()
    _session(backend, owner).insert(row_id, payload)
    if other == owner:
        assert _session(backend, other).select(row_id).payload == payload
    else:
        # tenant isolation: any DIFFERENT tenant sees nothing and cannot mutate it.
        assert _session(backend, other).select(row_id) is None
        assert _session(backend, other).update(row_id, "x") is False
        assert _session(backend, other).delete(row_id) is False
        # The owner's data survived every foreign attempt.
        assert _session(backend, owner).select(row_id).payload == payload


# --- STATEFUL: isolation holds over arbitrary operation sequences -----------


class TenantIsolationMachine(RuleBasedStateMachine):
    """Drives arbitrary interleaved tenant ops and asserts isolation never breaks.

    A shadow model records, per tenant, what each tenant *should* own; the
    invariant cross-checks that no tenant can ever observe a row the shadow model
    says belongs to a different tenant.
    """

    def __init__(self) -> None:
        """Start a fresh backend + an empty ownership shadow model."""
        super().__init__()
        self.backend = InMemoryRlsBackend()
        # shadow: (tenant, row_id) -> payload, the ground truth of ownership.
        self.shadow: dict[tuple[str, str], str] = {}

    @rule(tenant=_tenant_names, row_id=_row_ids, payload=_payloads)
    def insert(self, tenant: str, row_id: str, payload: str) -> None:
        TenantScopedSession(tenant, self.backend).insert(row_id, payload)
        self.shadow[(tenant, row_id)] = payload

    @rule(tenant=_tenant_names, row_id=_row_ids, payload=_payloads)
    def update(self, tenant: str, row_id: str, payload: str) -> None:
        ok = TenantScopedSession(tenant, self.backend).update(row_id, payload)
        # Update only succeeds for a row this tenant owns -> shadow agrees.
        if (tenant, row_id) in self.shadow:
            assert ok
            self.shadow[(tenant, row_id)] = payload
        else:
            assert ok is False  # foreign/missing row never updated

    @rule(tenant=_tenant_names, row_id=_row_ids)
    def delete(self, tenant: str, row_id: str) -> None:
        ok = TenantScopedSession(tenant, self.backend).delete(row_id)
        if (tenant, row_id) in self.shadow:
            assert ok
            del self.shadow[(tenant, row_id)]
        else:
            assert ok is False

    @invariant()
    def no_cross_tenant_visibility(self) -> None:
        # For every tenant and row, the session sees EXACTLY the shadow's owned row
        # and never a foreign tenant's row with the same id.
        for tenant in ["tenant-a", "tenant-b", "tenant-c"]:
            session = TenantScopedSession(tenant, self.backend)
            for row_id in ["r1", "r2", "r3"]:
                seen = session.select(row_id)
                expected = self.shadow.get((tenant, row_id))
                if expected is None:
                    assert seen is None  # no leak of any other tenant's row
                else:
                    assert seen is not None and seen.payload == expected


TestTenantIsolationStateful = TenantIsolationMachine.TestCase
