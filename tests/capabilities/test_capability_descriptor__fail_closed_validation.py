"""Adversarial fail-closed validation tests for CapabilityDescriptor + provenance.

Every refusal here targets a SPECIFIC fail-closed control (deny-by-default
clearance, routable-or-refuse keywords, PII-free non-empty rationale, closed
maturity set). A test that merely constructed a valid descriptor would be
tautological; these construct the INVALID variant and assert it is rejected — so
weakening any validator (e.g. defaulting clearance, accepting an empty keyword set)
makes a test fail.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from autofirm.capabilities.capability_descriptor import (
    UNSET_CLEARANCE,
    CapabilityDescriptor,
    CapabilityId,
    CapabilityProvenance,
)
from autofirm.org.org_identifiers import RoleId
from tests.capabilities.synthetic_capability_factory import valid_descriptor


def _provenance(**overrides: object) -> CapabilityProvenance:
    base = {"kind": "hire", "org_event_seq": 0, "rationale": "why it exists"}
    base.update(overrides)
    return CapabilityProvenance(**base)  # type: ignore[arg-type]


@pytest.mark.security
def test_empty_keyword_set_is_refused_unroutable_defect() -> None:
    with pytest.raises(ValidationError, match="non-empty set"):
        valid_descriptor(keywords=frozenset())


@pytest.mark.security
def test_whitespace_only_keyword_token_is_refused() -> None:
    with pytest.raises(ValidationError, match="non-empty tokens"):
        valid_descriptor(keywords=frozenset({"alpha", "   "}))


def _descriptor_with(**overrides: object) -> CapabilityDescriptor:
    """Build a valid descriptor then override one field (to make it invalid)."""
    base: dict[str, object] = {
        "capability_id": CapabilityId("cap-x"),
        "name": "a capability",
        "keywords": frozenset({"alpha"}),
        "owning_role_id": RoleId("role-x"),
        "required_clearance": "public",
        "provenance": _provenance(),
        "maturity": "active",
    }
    base.update(overrides)
    return CapabilityDescriptor(**base)  # type: ignore[arg-type]


@pytest.mark.security
@pytest.mark.parametrize("field", ["capability_id", "name", "required_clearance"])
def test_empty_required_text_field_is_refused(field: str) -> None:
    with pytest.raises(ValidationError, match="non-empty"):
        _descriptor_with(**{field: "   "})


@pytest.mark.unit
def test_unknown_maturity_is_refused_closed_set() -> None:
    with pytest.raises(ValidationError):
        valid_descriptor(maturity="retired")  # not in {proposed,active,deprecated}


@pytest.mark.security
def test_deny_by_default_sentinel_marks_capability_unreachable() -> None:
    # A descriptor still carrying the deny-by-default sentinel is NOT reachable;
    # any real clearance label makes it reachable. This is the explicit, self-
    # justifying check the routing layer relies on (never "open by omission").
    denied = valid_descriptor(clearance=UNSET_CLEARANCE)
    granted = valid_descriptor(clearance="public")
    assert denied.is_reachable() is False
    assert granted.is_reachable() is True


@pytest.mark.security
def test_provenance_rejects_empty_rationale_and_negative_seq() -> None:
    with pytest.raises(ValidationError, match="rationale"):
        _provenance(rationale="   ")
    with pytest.raises(ValidationError, match=">= 0"):
        _provenance(org_event_seq=-1)


@pytest.mark.unit
def test_descriptor_is_frozen_immutable() -> None:
    # Kills the frozen=True -> frozen=False mutant: a frozen model REFUSES assignment
    # AND leaves the field unchanged; a mutated (mutable) model would silently accept
    # the write, failing both assertions.
    descriptor = valid_descriptor(maturity="active")
    with pytest.raises(ValidationError):
        descriptor.maturity = "deprecated"  # type: ignore[misc]
    assert descriptor.maturity == "active"  # the value never changed (still frozen)


@pytest.mark.unit
def test_provenance_is_frozen_immutable() -> None:
    # Same frozen=True teeth for the nested provenance model.
    provenance = _provenance(rationale="original reason")
    with pytest.raises(ValidationError):
        provenance.rationale = "overwritten"  # type: ignore[misc]
    assert provenance.rationale == "original reason"
