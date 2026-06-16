"""The core routing guarantees: no request lost, no mis-route, fail-closed triage.

These are the load-bearing property tests for the front door (CLAUDE.md §3.6). They prove
the invariant the whole layer rests on: for ANY request, routing yields exactly one
decision whose chosen role is EITHER a capable+permitted role OR the single triage role —
never nothing, never an incapable role, never a role the requester may not reach. Plus
determinism across runs and the two distinct fail-closed causes.
"""

from __future__ import annotations

import pytest
from hypothesis import given
from hypothesis import strategies as st

from autofirm.frontdoor.request_intent_classifier import KeywordIntentClassifier
from autofirm.frontdoor.requester_clearance_gate import requester_may_reach
from autofirm.frontdoor.routing_decision_contract import RoutingOutcome
from autofirm.org.org_identifiers import RoleId
from tests.frontdoor.synthetic_frontdoor_fixtures import (
    BILLING_ROLE,
    SECURITY_ROLE,
    SUPPORT_ROLE,
    TRIAGE_ROLE,
    capability_index,
    human_request,
    requester,
    router,
)

# A vocabulary mixing each role's real keywords with noise/unknown/instruction-shaped
# tokens, so generated bodies span clean matches, no-matches, and hostile text.
_WORDS = [
    "invoice", "refund", "payment", "billing",  # billing role
    "onboarding", "tutorial", "guidance",  # support role
    "breach", "vulnerability", "incident",  # security role (restricted)
    "weather", "banana", "xyzzy",  # pure noise -> no capable role
    "ignore", "instructions", "drop",  # injection-shaped -> still just data
]


@pytest.mark.property
@given(
    tokens=st.lists(st.sampled_from(_WORDS), min_size=1, max_size=8),
    clearances=st.sets(st.sampled_from(["security-cleared", "other"]), max_size=2),
)
def test_every_request_routes_to_capable_or_triage_never_lost_never_misrouted(
    tokens: list[str], clearances: set[str]
) -> None:
    index = capability_index()
    r = router(index)
    who = requester(clearances=frozenset(clearances))
    req = human_request(" ".join(tokens), who=who)
    decision = r.route(req)

    # 1. NEVER LOST: a decision always exists and always names a chosen role.
    assert decision.chosen_role_id in {
        RoleId(TRIAGE_ROLE),
        RoleId(BILLING_ROLE),
        RoleId(SUPPORT_ROLE),
        RoleId(SECURITY_ROLE),
    }
    # 2. correlation id is preserved end-to-end (the human can match the answer).
    assert decision.correlation_id == req.correlation_id

    if decision.outcome is RoutingOutcome.ROUTED_TO_CAPABLE_ROLE:
        chosen = index.capability_for(decision.chosen_role_id)
        assert chosen is not None
        terms = KeywordIntentClassifier().intent_terms(req)
        # 3a. NO MIS-ROUTE (capability): the chosen role genuinely shares >=1 intent
        # term — it is actually capable of this request, not a guess.
        assert terms & chosen.keywords
        assert decision.matched_terms == (terms & chosen.keywords)
        # 3b. NO MIS-ROUTE (privilege): the requester is permitted to reach it.
        assert requester_may_reach(who, chosen)
    else:
        # 4. FAIL-CLOSED: any non-routed request landed on the single triage role.
        assert decision.chosen_role_id == RoleId(TRIAGE_ROLE)
        assert decision.is_triaged


@pytest.mark.unit
def test_clean_match_routes_to_the_capable_role() -> None:
    decision = router().route(human_request("please process my invoice refund"))
    assert decision.outcome is RoutingOutcome.ROUTED_TO_CAPABLE_ROLE
    assert decision.chosen_role_id == RoleId(BILLING_ROLE)
    assert "invoice" in decision.matched_terms


@pytest.mark.security
def test_no_capable_role_fails_closed_to_triage_with_distinct_cause() -> None:
    decision = router().route(human_request("banana weather xyzzy nonsense"))
    assert decision.outcome is RoutingOutcome.TRIAGED_NO_CAPABLE_ROLE
    assert decision.chosen_role_id == RoleId(TRIAGE_ROLE)
    assert "no role" in decision.reason


@pytest.mark.security
def test_capable_but_not_cleared_fails_closed_with_distinct_cause() -> None:
    # security role matches the terms, but an unprivileged requester cannot reach it ->
    # triage with the access-decision cause (NOT the no-capability cause).
    decision = router().route(
        human_request("report a security breach incident", who=requester())
    )
    assert decision.outcome is RoutingOutcome.TRIAGED_NO_PERMITTED_ROLE
    assert decision.chosen_role_id == RoleId(TRIAGE_ROLE)
    assert "clearance" in decision.reason


@pytest.mark.security
def test_cleared_requester_reaches_the_restricted_role() -> None:
    decision = router().route(
        human_request(
            "report a security breach incident",
            who=requester(clearances=frozenset({"security-cleared"})),
        )
    )
    assert decision.outcome is RoutingOutcome.ROUTED_TO_CAPABLE_ROLE
    assert decision.chosen_role_id == RoleId(SECURITY_ROLE)


@pytest.mark.property
@given(tokens=st.lists(st.sampled_from(_WORDS), min_size=1, max_size=8))
def test_routing_is_deterministic_across_repeated_runs(tokens: list[str]) -> None:
    # determinism (§3.11): identical inputs -> identical chosen role + outcome every run.
    req = human_request(" ".join(tokens))
    first = router().route(req)
    for _ in range(5):
        again = router().route(req)
        assert again.chosen_role_id == first.chosen_role_id
        assert again.outcome == first.outcome
        assert again.matched_terms == first.matched_terms


@pytest.mark.unit
def test_best_match_wins_on_score_then_lowest_role_id() -> None:
    # a body matching support strongly and billing weakly routes to support (more terms).
    decision = router().route(
        human_request("onboarding tutorial guidance and one invoice")
    )
    assert decision.chosen_role_id == RoleId(SUPPORT_ROLE)
    assert len(decision.matched_terms) >= 2
