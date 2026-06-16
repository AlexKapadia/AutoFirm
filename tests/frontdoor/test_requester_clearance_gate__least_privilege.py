"""Least-privilege tests for the requester clearance gate (deny-by-default, fail-closed).

Prove :func:`requester_may_reach` is True on EXACTLY two paths (public role, or holding
the explicit clearance) and False everywhere else — the unreachable sentinel, a missing
label, the empty-clearance public requester reaching a restricted role.
"""

from __future__ import annotations

import pytest
from hypothesis import given
from hypothesis import strategies as st

from autofirm.frontdoor.requester_clearance_gate import requester_may_reach
from autofirm.frontdoor.role_capability_index import (
    PUBLIC_CLEARANCE,
    UNREACHABLE_CLEARANCE,
    RoleCapability,
)
from autofirm.org.org_identifiers import RoleId
from tests.frontdoor.synthetic_frontdoor_fixtures import requester


def _cap(required: str) -> RoleCapability:
    return RoleCapability(
        role_id=RoleId("r"),
        title="R",
        keywords=frozenset({"k"}),
        required_clearance=required,
        is_triage=False,
    )


@pytest.mark.security
def test_public_role_reachable_by_unprivileged_requester() -> None:
    assert requester_may_reach(requester(clearances=frozenset()), _cap(PUBLIC_CLEARANCE))


@pytest.mark.security
def test_unreachable_sentinel_role_reachable_by_no_one() -> None:
    # deny by default: even a requester holding the sentinel string cannot reach it.
    who = requester(clearances=frozenset({UNREACHABLE_CLEARANCE}))
    assert not requester_may_reach(who, _cap(UNREACHABLE_CLEARANCE))


@pytest.mark.security
def test_restricted_role_requires_exact_clearance() -> None:
    restricted = _cap("security-cleared")
    assert not requester_may_reach(requester(clearances=frozenset()), restricted)
    assert not requester_may_reach(
        requester(clearances=frozenset({"billing-cleared"})), restricted
    )
    assert requester_may_reach(
        requester(clearances=frozenset({"security-cleared"})), restricted
    )


@pytest.mark.property
@given(
    held=st.sets(st.sampled_from(["a", "b", "c", "security-cleared"]), max_size=4),
    required=st.sampled_from(["a", "b", "c", "security-cleared", "missing"]),
)
def test_gate_true_iff_required_held_for_non_public(
    held: set[str], required: str
) -> None:
    # property over a restricted (non-public, non-sentinel) role: reachable IFF the exact
    # required label is held — never on a near-miss, never by holding extra clearances.
    who = requester(clearances=frozenset(held))
    assert requester_may_reach(who, _cap(required)) == (required in held)
