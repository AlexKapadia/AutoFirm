"""Cutover gate: the front-door router routes correctly via the LIVE registry.

This is the W4 cutover-step-1 gate (gate1-decision #3): it must pass BEFORE any
static capability tuples are deleted. It proves a multi-hire org, grown through the
:class:`CapabilityRecordingOrg`, drives the REAL
:class:`~autofirm.frontdoor.front_desk_request_router.FrontDeskRequestRouter` to the
correct handler via :meth:`RoleCapabilityIndex.from_capability_registry` — covering
unambiguous matches, score-ranked matches, deterministic ties, deny-by-default
clearance, and the fail-closed triage fallback. If routing-through-the-registry were
wrong, these would fail (they are not tautologies — each asserts a SPECIFIC chosen
role and outcome that only the correct keyword/score/clearance logic produces).
"""

from __future__ import annotations

import pytest

from autofirm.capabilities.live_capability_registry import LiveCapabilityRegistry
from autofirm.frontdoor.front_desk_request_router import FrontDeskRequestRouter
from autofirm.frontdoor.human_request_contract import (
    HumanRequest,
    RequestChannel,
    RequesterIdentity,
)
from autofirm.frontdoor.request_intent_classifier import KeywordIntentClassifier
from autofirm.frontdoor.role_capability_index import (
    PUBLIC_CLEARANCE,
    RoleCapabilityIndex,
)
from autofirm.frontdoor.routing_decision_contract import RoutingOutcome
from autofirm.org.org_identifiers import RoleId
from tests.capabilities.synthetic_capability_factory import (
    CEO,
    EPOCH,
    founded_recording_org,
    fresh_clock,
    report_charter,
)

# Three capable roles with DISTINCT, non-overlapping vocabularies plus the CEO
# triage fallback (whose own responsibilities deliberately share no term with the
# routed questions, so it is never a spurious capable match).
_BILLING = "billing-lead"
_SUPPORT = "support-lead"
_SECURITY = "security-lead"


def _multi_hire_registry() -> LiveCapabilityRegistry:
    """Grow a 4-role org through the recording wrapper and replay its live registry."""
    rec = founded_recording_org(CEO)
    rec = rec.hire(report_charter(_BILLING, ("handle invoice billing refund payment",)))
    rec = rec.hire(report_charter(_SUPPORT, ("resolve onboarding tutorial guidance",)))
    rec = rec.hire(report_charter(_SECURITY, ("investigate breach vulnerability incident",)))
    return rec.live_registry()


def _index(*, security_clearance: str = "security-cleared") -> RoleCapabilityIndex:
    """Build the front-door index from the live registry (the cutover seam)."""
    clearances = {
        RoleId(CEO): PUBLIC_CLEARANCE,
        RoleId(_BILLING): PUBLIC_CLEARANCE,
        RoleId(_SUPPORT): PUBLIC_CLEARANCE,
        RoleId(_SECURITY): security_clearance,
    }
    return RoleCapabilityIndex.from_capability_registry(
        _multi_hire_registry(),
        triage_role_id=RoleId(CEO),
        required_clearances=clearances,
    )


def _router(index: RoleCapabilityIndex) -> FrontDeskRequestRouter:
    return FrontDeskRequestRouter(
        capability_index=index,
        classifier=KeywordIntentClassifier(),
        clock=fresh_clock(),
    )


def _request(body: str, *, clearances: frozenset[str] = frozenset()) -> HumanRequest:
    return HumanRequest(
        correlation_id="corr-cutover",
        requester=RequesterIdentity(
            requester_id="owner-acme", display_name="Owner", clearances=clearances
        ),
        channel=RequestChannel.API,
        body=body,
        received_at=EPOCH,
    )


@pytest.mark.unit
def test_unambiguous_question_routes_to_the_one_matching_role() -> None:
    decision = _router(_index()).route(_request("I need an invoice and refund for a payment"))
    assert decision.outcome is RoutingOutcome.ROUTED_TO_CAPABLE_ROLE
    assert decision.chosen_role_id == RoleId(_BILLING)  # billing's vocabulary only
    assert {"invoice", "refund", "payment"} <= decision.matched_terms


@pytest.mark.unit
def test_score_ranked_match_picks_the_more_overlapping_role() -> None:
    # The question shares THREE terms with security and none with the others, so the
    # score-ranked selection must pick security (most matched intent terms).
    request = _request(
        "investigate the breach vulnerability incident on our systems",
        clearances=frozenset({"security-cleared"}),
    )
    decision = _router(_index()).route(request)
    assert decision.chosen_role_id == RoleId(_SECURITY)
    assert {"investigate", "breach", "vulnerability", "incident"} & decision.matched_terms


@pytest.mark.unit
def test_unmatched_question_fails_closed_to_triage() -> None:
    # No live capability shares a term with this question -> the single triage role.
    decision = _router(_index()).route(_request("philosophy poetry astronomy"))
    assert decision.outcome is RoutingOutcome.TRIAGED_NO_CAPABLE_ROLE
    assert decision.chosen_role_id == RoleId(CEO)


@pytest.mark.security
def test_capable_but_uncleared_role_fails_closed_to_triage() -> None:
    # A requester with NO clearance asks a security question: security is capable but
    # not reachable, and no other role matches -> triage, NOT the capable role (§5.6).
    decision = _router(_index()).route(_request("investigate breach incident"))
    assert decision.outcome is RoutingOutcome.TRIAGED_NO_PERMITTED_ROLE
    assert decision.chosen_role_id == RoleId(CEO)


@pytest.mark.unit
def test_tie_breaks_deterministically_to_lowest_role_id() -> None:
    # Two roles share the SAME single overlapping term ("reports"); the tie-break is
    # the lowest role-id. "alpha-team" < "beta-team", so alpha-team must win, every run.
    rec = founded_recording_org(CEO)
    rec = rec.hire(report_charter("alpha-team", ("file quarterly reports",)))
    rec = rec.hire(report_charter("beta-team", ("publish annual reports",)))
    index = RoleCapabilityIndex.from_capability_registry(
        rec.live_registry(),
        triage_role_id=RoleId(CEO),
        required_clearances={
            RoleId(CEO): PUBLIC_CLEARANCE,
            RoleId("alpha-team"): PUBLIC_CLEARANCE,
            RoleId("beta-team"): PUBLIC_CLEARANCE,
        },
    )
    decision = _router(index).route(_request("where are the reports"))
    assert decision.chosen_role_id == RoleId("alpha-team")
    assert decision.matched_terms == frozenset({"reports"})


@pytest.mark.unit
def test_fired_role_is_not_a_routing_target() -> None:
    # A hired-then-fired role's capability is deprecated, so it must NOT be routable;
    # its question falls through to triage (capability follows the LIVE org exactly).
    rec = founded_recording_org(CEO)
    rec = rec.hire(report_charter(_BILLING, ("handle invoice billing refund",)))
    rec = rec.fire(RoleId(_BILLING))
    index = RoleCapabilityIndex.from_capability_registry(
        rec.live_registry(),
        triage_role_id=RoleId(CEO),
        required_clearances={RoleId(CEO): PUBLIC_CLEARANCE},
    )
    decision = _router(index).route(_request("invoice refund please"))
    assert decision.outcome is RoutingOutcome.TRIAGED_NO_CAPABLE_ROLE
    assert decision.chosen_role_id == RoleId(CEO)
