"""Boundary tests for the access value-object validators (fail-closed construction).

Covers the contract edges that the broker/RLS suites exercise indirectly: empty
scope fields, empty operation sets, empty secrets, empty TenantRow ids, the session
tenant getter, and the containment helper's short-path branch. Synthetic only.
"""

from __future__ import annotations

from pathlib import PurePosixPath

import pytest

from autofirm.access.credential_scope_contract import (
    CredentialScope,
    Operation,
    RedactedSecret,
)
from autofirm.access.in_memory_rls_backend import InMemoryRlsBackend
from autofirm.access.tenant_scoped_session_contract import (
    TenantRow,
    TenantScopedSession,
)
from autofirm.access.workspace_data_boundary import _is_relative_to


@pytest.mark.security
@pytest.mark.parametrize("blank", ["", "   "])
def test_scope_empty_resource_is_refused(blank: str) -> None:
    with pytest.raises(ValueError):
        CredentialScope(
            resource=blank, operations=frozenset({Operation.READ}), tenant_id="t1"
        )


@pytest.mark.security
@pytest.mark.parametrize("blank", ["", "   "])
def test_scope_empty_tenant_is_refused(blank: str) -> None:
    with pytest.raises(ValueError):
        CredentialScope(
            resource="r", operations=frozenset({Operation.READ}), tenant_id=blank
        )


@pytest.mark.security
def test_scope_empty_operation_set_is_refused() -> None:
    # fail-closed: an empty op set must never be read as "grants everything".
    with pytest.raises(ValueError):
        CredentialScope(resource="r", operations=frozenset(), tenant_id="t1")


@pytest.mark.security
def test_empty_secret_is_refused() -> None:
    # fail-closed: an empty secret is not a usable credential.
    with pytest.raises(ValueError):
        RedactedSecret(secret_value="")


@pytest.mark.security
@pytest.mark.parametrize("blank", ["", "   "])
def test_tenant_row_empty_ids_are_refused(blank: str) -> None:
    with pytest.raises(ValueError):
        TenantRow(tenant_id=blank, row_id="r1", payload="x")
    with pytest.raises(ValueError):
        TenantRow(tenant_id="t1", row_id=blank, payload="x")


@pytest.mark.unit
def test_session_exposes_its_locked_tenant_id() -> None:
    session = TenantScopedSession("tenant-a", InMemoryRlsBackend())
    assert session.tenant_id == "tenant-a"  # read-only getter


@pytest.mark.unit
def test_is_relative_to_short_path_is_not_contained() -> None:
    # A path shorter than the base cannot be inside it.
    assert _is_relative_to(PurePosixPath("/a"), PurePosixPath("/a/b/c")) is False
    assert _is_relative_to(PurePosixPath("/a/b"), PurePosixPath("/a/b")) is True
