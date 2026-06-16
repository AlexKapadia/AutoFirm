"""Tests for the routing-decision provenance accessors (every field is retrievable).

A decision is the audited provenance record; every field an auditor needs — requester
id, decided-at timestamp, outcome, chosen role, matched terms, reason — must be exposed
and preserved exactly as constructed.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from autofirm.frontdoor.routing_decision_contract import RoutingDecision, RoutingOutcome
from autofirm.org.org_identifiers import RoleId

_WHEN = datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)


def _decision(outcome: RoutingOutcome) -> RoutingDecision:
    return RoutingDecision(
        correlation_id="corr-9",
        requester_id="owner-acme",
        outcome=outcome,
        chosen_role_id=RoleId("billing-lead"),
        chosen_role_title="Billing Lead",
        matched_terms=frozenset({"invoice"}),
        reason="routed: matched invoice",
        decided_at=_WHEN,
    )


@pytest.mark.unit
def test_all_provenance_fields_are_exposed_and_exact() -> None:
    d = _decision(RoutingOutcome.ROUTED_TO_CAPABLE_ROLE)
    assert d.correlation_id == "corr-9"
    assert d.requester_id == "owner-acme"
    assert d.outcome is RoutingOutcome.ROUTED_TO_CAPABLE_ROLE
    assert d.chosen_role_id == RoleId("billing-lead")
    assert d.chosen_role_title == "Billing Lead"
    assert d.matched_terms == frozenset({"invoice"})
    assert d.reason == "routed: matched invoice"
    assert d.decided_at == _WHEN
    assert d.is_triaged is False


@pytest.mark.unit
@pytest.mark.parametrize(
    "outcome",
    [
        RoutingOutcome.TRIAGED_NO_CAPABLE_ROLE,
        RoutingOutcome.TRIAGED_NO_PERMITTED_ROLE,
    ],
)
def test_both_triage_outcomes_report_is_triaged(outcome: RoutingOutcome) -> None:
    assert _decision(outcome).is_triaged is True
