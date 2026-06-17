"""Tests that pin the fail-closed defensive branches (mutation-killing teeth).

Each test exercises a SPECIFIC defensive guard so a mutant that flips it (e.g.
``< 0`` -> ``<= 0``, ``if charter is None`` -> ``if charter is not None``, dropping a
``return None``) is killed by a failing assertion. These are the nooks an auditor
probes: malformed events, un-keyworded roles, missing charters, and the empty/no-op
recording paths.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from autofirm.capabilities.capability_growth_log import CapabilityGrowthLog
from autofirm.capabilities.capability_registry_event import CapabilityRegistryEvent
from autofirm.capabilities.org_event_to_capability_projection import (
    _charter_for,
    project_org_event,
)
from autofirm.org.org_identifiers import RoleId
from autofirm.org.org_lifecycle_events import OrgEvent, OrgEventKind
from tests.capabilities.synthetic_capability_factory import (
    CEO,
    EPOCH,
    founded_recording_org,
    report_charter,
    sealed_event,
)


@pytest.mark.security
def test_event_refuses_negative_seq_and_negative_org_event_ref() -> None:
    good = sealed_event(CapabilityGrowthLog())
    payload = good.model_dump()
    payload["seq"] = -1
    with pytest.raises(ValidationError, match=">= 0"):
        CapabilityRegistryEvent.model_validate(payload)
    payload2 = good.model_dump()
    payload2["org_event_ref"] = -5
    with pytest.raises(ValidationError, match=">= 0"):
        CapabilityRegistryEvent.model_validate(payload2)


@pytest.mark.security
def test_event_refuses_empty_rationale() -> None:
    good = sealed_event(CapabilityGrowthLog())
    payload = good.model_dump()
    payload["rationale"] = "   "
    with pytest.raises(ValidationError, match="rationale must be non-empty"):
        CapabilityRegistryEvent.model_validate(payload)


@pytest.mark.unit
def test_projection_returns_none_when_role_charter_is_absent() -> None:
    # _charter_for over a hierarchy missing the subject role yields None, so the
    # projection refuses to advertise (fail-closed: no charter -> no capability).
    rec = founded_recording_org(CEO).hire(report_charter("r", ("own alpha work",)))
    hierarchy = rec.org.state.hierarchy
    phantom = OrgEvent(
        seq=99,
        kind=OrgEventKind.ROLE_HIRED,
        subject_role_id="does-not-exist",
        detail="hired",
        timestamp=EPOCH,
    )
    assert _charter_for(phantom, hierarchy) is None
    assert project_org_event(phantom, hierarchy) is None


@pytest.mark.unit
def test_projection_returns_none_when_responsibilities_yield_no_keywords() -> None:
    # A role whose responsibilities tokenise to nothing routable (only sub-3-char
    # tokens) cannot advertise a capability — the projection skips it (no unroutable
    # capability is ever built).
    rec = founded_recording_org(CEO)
    # All tokens < 3 chars -> extract_capability_keywords yields the empty set.
    rec_org = rec.org.hire(report_charter("tiny", ("a to of by",)))
    event = rec_org.state.trail.events[-1]
    assert project_org_event(event, rec_org.state.hierarchy) is None
    # And growing through the recording wrapper seals NO event for such a role.
    grown = founded_recording_org(CEO)
    grown_after = grown.hire(report_charter("tiny", ("a to of by",)))
    assert len(grown_after.growth_log.events()) == len(grown.growth_log.events())


@pytest.mark.security
def test_verify_detects_a_correct_seq_but_wrong_prev_hash_link() -> None:
    # Isolate the chain-link branch of verify (distinct from the seq-position branch):
    # a 2-event tuple where event[1] has the RIGHT seq (1) but a prev_hash that does
    # not chain event[0]'s record_hash must fail verification.
    log = CapabilityGrowthLog()
    e0 = sealed_event(log)
    log1 = log.append(e0)
    e1 = sealed_event(log1, org_event_ref=1)  # correctly chained over e0
    forged_e1 = e1.model_copy(update={"prev_hash": b"\x11" * 32})  # break the link only
    smuggled = CapabilityGrowthLog.__new__(CapabilityGrowthLog)
    object.__setattr__(smuggled, "_events", (e0, forged_e1))
    assert smuggled.verify() is False  # seq is fine; the prev_hash link is broken


@pytest.mark.unit
def test_firing_an_unadvertised_role_grows_no_deprecation_event() -> None:
    # A role hired with only sub-3-char tokens is never advertised (no live
    # descriptor). Firing it must find nothing to deprecate -> the growth log does
    # NOT gain a deprecation event (the never-advertised no-op path).
    rec = founded_recording_org(CEO)
    rec = rec.hire(report_charter("ghost", ("a to of by",)))  # un-keyworded -> unadvertised
    before = len(rec.growth_log.events())
    assert rec.live_registry().descriptor_for(RoleId("ghost")) is None
    rec = rec.fire(RoleId("ghost"))
    assert len(rec.growth_log.events()) == before  # no spurious deprecation event
