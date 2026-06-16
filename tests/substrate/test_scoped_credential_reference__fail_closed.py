"""Adversarial tests for the secret-free credential reference (fail-closed).

The reference is the structural guarantee that a session holds NO secret material:
it is built from a real credential's audit projection (secret-free) and validates
fail-closed on empty fields / no operations, with a boundary-exact expiry check.
These tests pin those edges and prove the build path copies only metadata.
Synthetic only.
"""

from __future__ import annotations

from datetime import timedelta

import pytest
from pydantic import ValidationError

from autofirm.substrate.scoped_credential_reference import ScopedCredentialReference
from tests.substrate.synthetic_substrate_fixtures import (
    FIXED_NOW,
    make_credential_reference,
    make_scoped_credential_with_sentinel,
)


@pytest.mark.unit
def test_is_valid_at_is_boundary_exact() -> None:
    ref = make_credential_reference(expires_at=FIXED_NOW + timedelta(minutes=10))
    expiry = FIXED_NOW + timedelta(minutes=10)
    assert ref.is_valid_at(expiry - timedelta(seconds=1)) is True  # just before
    # fail-closed: the EXACT expiry instant is already invalid (strict '<').
    assert ref.is_valid_at(expiry) is False
    assert ref.is_valid_at(expiry + timedelta(seconds=1)) is False  # after


@pytest.mark.unit
@pytest.mark.parametrize(
    "kwargs",
    [
        {"component": "  "},  # blank component refused
        {"resource": ""},  # blank resource refused
        {"tenant_id": "   "},  # blank tenant refused
        {"operations": ()},  # zero operations refused (never "grants everything")
    ],
)
def test_invalid_reference_construction_is_refused(kwargs: dict[str, object]) -> None:
    with pytest.raises(ValidationError):  # fail-closed at the boundary
        make_credential_reference(**kwargs)  # type: ignore[arg-type]


@pytest.mark.unit
def test_from_scoped_credential_copies_only_metadata() -> None:
    cred = make_scoped_credential_with_sentinel("deadbeef")
    ref = ScopedCredentialReference.from_scoped_credential(cred)
    # The reference mirrors the credential's non-secret scope exactly.
    assert ref.component == "agent"
    assert ref.resource == "pg:db"
    assert ref.tenant_id == "tenant-1"
    assert ref.operations == ("READ",)
    assert ref.expires_at == cred.expires_at
    # ...and no field could even hold the secret (model_fields are metadata only).
    assert "secret" not in ScopedCredentialReference.model_fields


@pytest.mark.unit
def test_reference_is_frozen() -> None:
    ref = make_credential_reference()
    with pytest.raises(ValidationError):  # immutable: cannot widen after build
        ref.tenant_id = "other-tenant"  # type: ignore[misc]
