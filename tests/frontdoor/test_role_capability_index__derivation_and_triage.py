"""Tests for capability derivation, deny-by-default clearances, and the triage invariant.

Prove the index derives keywords from the live org's charter responsibilities, defaults
un-granted roles to the UNREACHABLE sentinel (deny by default, §5.6), and REFUSES any
index without exactly one triage fallback (the whole fail-closed routing guarantee rests
on this).
"""

from __future__ import annotations

import pytest

from autofirm.frontdoor.role_capability_index import (
    UNREACHABLE_CLEARANCE,
    RoleCapability,
    RoleCapabilityIndex,
    extract_capability_keywords,
)
from autofirm.org.org_identifiers import RoleId
from tests.frontdoor.synthetic_frontdoor_fixtures import (
    BILLING_ROLE,
    SECURITY_ROLE,
    TRIAGE_ROLE,
    capability_index,
    realistic_org_state,
)


@pytest.mark.unit
def test_keywords_derived_lowercased_and_min_length() -> None:
    kws = extract_capability_keywords(("Handle INVOICE billing", "a to of"))
    assert "invoice" in kws and "billing" in kws and "handle" in kws
    # short tokens (<3 chars) carry no routing signal and are dropped.
    assert "to" not in kws and "of" not in kws and "a" not in kws


@pytest.mark.property
def test_keyword_extraction_is_order_independent() -> None:
    # determinism: responsibility order must not change the derived capability surface.
    a = extract_capability_keywords(("alpha task", "beta task"))
    b = extract_capability_keywords(("beta task", "alpha task"))
    assert a == b


@pytest.mark.unit
def test_index_derives_capability_from_charter_responsibilities() -> None:
    index = capability_index()
    billing = index.capability_for(RoleId(BILLING_ROLE))
    assert billing is not None
    assert "invoice" in billing.keywords and "refund" in billing.keywords


@pytest.mark.security
def test_ungranted_role_defaults_to_unreachable_sentinel() -> None:
    # deny by default: a role absent from the clearance map is unreachable, not public.
    state = realistic_org_state()
    index = RoleCapabilityIndex.from_org_state(
        state, triage_role_id=RoleId(TRIAGE_ROLE), required_clearances={}
    )
    billing = index.capability_for(RoleId(BILLING_ROLE))
    assert billing is not None
    assert billing.required_clearance == UNREACHABLE_CLEARANCE


@pytest.mark.security
def test_index_with_no_triage_role_is_refused() -> None:
    # fail-closed: without exactly one triage fallback the router has nowhere to send an
    # unmatched request — construction must refuse it.
    cap = RoleCapability(
        role_id=RoleId("x"),
        title="X",
        keywords=frozenset({"foo"}),
        required_clearance="public",
        is_triage=False,
    )
    with pytest.raises(ValueError, match="exactly one triage"):
        RoleCapabilityIndex((cap,))


@pytest.mark.security
def test_index_with_many_triage_roles_is_refused() -> None:
    caps = tuple(
        RoleCapability(
            role_id=RoleId(rid),
            title=rid,
            keywords=frozenset(),
            required_clearance="public",
            is_triage=True,
        )
        for rid in ("a", "b")
    )
    with pytest.raises(ValueError, match="exactly one triage"):
        RoleCapabilityIndex(caps)


@pytest.mark.security
def test_triage_role_must_be_a_live_org_role() -> None:
    state = realistic_org_state()
    with pytest.raises(ValueError, match="not a live org role"):
        RoleCapabilityIndex.from_org_state(
            state,
            triage_role_id=RoleId("ghost-role"),
            required_clearances={},
        )


@pytest.mark.unit
def test_triage_excluded_from_scored_candidates() -> None:
    index = capability_index()
    non_triage = {c.role_id for c in index.non_triage_capabilities()}
    assert RoleId(TRIAGE_ROLE) not in non_triage
    assert index.triage_capability().role_id == RoleId(TRIAGE_ROLE)
    # the security role IS a scored candidate (it is not triage).
    assert RoleId(SECURITY_ROLE) in non_triage
