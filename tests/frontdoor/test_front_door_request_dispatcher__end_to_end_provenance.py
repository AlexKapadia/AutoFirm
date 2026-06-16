"""End-to-end dispatcher tests: delivery over the bus + always-complete provenance.

Prove the dispatcher drives the whole flow — route, deliver to the chosen role over the
real inter-agent bus, append provenance, respond — and that provenance/audit is ALWAYS
complete and the response is fail-closed-honest (a dead-lettered delivery is reported as
NOT accepted, never as success).
"""

from __future__ import annotations

import pytest

from autofirm.comms.delivery_outcome_types import DeliveryStatus
from autofirm.frontdoor.routing_decision_contract import RoutingOutcome
from tests.frontdoor.synthetic_frontdoor_fixtures import (
    BILLING_ROLE,
    SECURITY_ROLE,
    SUPPORT_ROLE,
    TRIAGE_ROLE,
    dispatcher_with_recording_handlers,
    human_request,
    requester,
)

pytestmark = pytest.mark.anyio


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.mark.unit
async def test_capable_request_delivered_to_the_right_role_with_provenance() -> None:
    dispatcher, handlers, trail = dispatcher_with_recording_handlers()
    response = await dispatcher.handle(human_request("refund my invoice payment"))

    # delivered to EXACTLY the billing role over the real bus, no one else.
    assert len(handlers.received[BILLING_ROLE]) == 1
    assert handlers.received[BILLING_ROLE][0].payload["body"] == "refund my invoice payment"
    assert all(
        not handlers.received[other]
        for other in (TRIAGE_ROLE, SUPPORT_ROLE, SECURITY_ROLE)
    )

    # response provenance is complete + accepted.
    assert response.accepted is True
    assert response.routing_outcome is RoutingOutcome.ROUTED_TO_CAPABLE_ROLE
    assert response.handler_role_id == BILLING_ROLE
    assert response.delivery_status is DeliveryStatus.DELIVERED
    assert response.correlation_id == "corr-1"

    # exactly one provenance entry, fully populated, joined by correlation id.
    assert len(trail) == 1
    entry = trail.entries()[0]
    assert entry.correlation_id == "corr-1"
    assert entry.handler_role_id == BILLING_ROLE
    assert entry.delivery_status is DeliveryStatus.DELIVERED
    assert "invoice" in entry.routing_reason or "billing" in entry.routing_reason.lower()


@pytest.mark.security
async def test_no_match_is_delivered_to_triage_and_audited() -> None:
    dispatcher, handlers, trail = dispatcher_with_recording_handlers()
    response = await dispatcher.handle(human_request("banana weather nonsense xyzzy"))

    assert len(handlers.received[TRIAGE_ROLE]) == 1  # fell back to triage handler
    assert response.routing_outcome is RoutingOutcome.TRIAGED_NO_CAPABLE_ROLE
    assert response.handler_role_id == TRIAGE_ROLE
    assert response.accepted is True  # triage IS a valid handler that received it
    assert len(trail) == 1 and trail.entries()[0].handler_role_id == TRIAGE_ROLE


@pytest.mark.security
async def test_restricted_request_without_clearance_goes_to_triage() -> None:
    dispatcher, handlers, _ = dispatcher_with_recording_handlers()
    response = await dispatcher.handle(
        human_request("security breach incident report", who=requester())
    )
    assert response.routing_outcome is RoutingOutcome.TRIAGED_NO_PERMITTED_ROLE
    assert len(handlers.received[SECURITY_ROLE]) == 0  # never reached the restricted role
    assert len(handlers.received[TRIAGE_ROLE]) == 1


@pytest.mark.security
async def test_undeliverable_handler_is_not_reported_as_accepted() -> None:
    # routing is correct but the billing role has NO registered bus handler -> the bus
    # dead-letters it. The response must say accepted=False (fail-closed honesty) and the
    # provenance must still be recorded with the dead-letter status.
    dispatcher, handlers, trail = dispatcher_with_recording_handlers(
        register_roles=(TRIAGE_ROLE,)  # only triage has a handler
    )
    response = await dispatcher.handle(human_request("refund my invoice"))

    assert response.routing_outcome is RoutingOutcome.ROUTED_TO_CAPABLE_ROLE
    assert response.handler_role_id == BILLING_ROLE  # routed correctly...
    assert response.accepted is False  # ...but NOT delivered -> not accepted
    assert response.delivery_status is DeliveryStatus.DEAD_LETTERED
    assert len(handlers.bus.dead_letters) == 1  # observable, never silently dropped
    # provenance is STILL recorded for the fail-closed delivery (audit completeness).
    assert len(trail) == 1
    assert trail.entries()[0].delivery_status is DeliveryStatus.DEAD_LETTERED


@pytest.mark.unit
async def test_every_handled_request_appends_exactly_one_provenance_entry() -> None:
    dispatcher, _, trail = dispatcher_with_recording_handlers()
    bodies = [
        "refund invoice",  # billing
        "onboarding tutorial",  # support
        "banana nonsense",  # triage (no match)
    ]
    for i, body in enumerate(bodies):
        await dispatcher.handle(human_request(body, correlation_id=f"corr-{i}"))
    # audit completeness: one entry per request, none lost, correlation ids preserved.
    assert len(trail) == len(bodies)
    assert [e.correlation_id for e in trail.entries()] == ["corr-0", "corr-1", "corr-2"]
