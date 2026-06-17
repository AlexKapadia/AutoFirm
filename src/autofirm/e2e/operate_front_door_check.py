"""Operate-phase front-door check: route a human question over the live company.

A human owner asks a question through the front door; it is classified, matched to
a capable role derived from the LIVE built org, cleared, and delivered over the
real inter-agent bus — returning a provenance-bearing response. The check asserts
the request reaches a real handler (a capable role OR the triage fallback) and is
recorded, proving the human->company surface works end-to-end over the company we
actually built (not a stub org).
"""

from __future__ import annotations

import asyncio

from autofirm.comms.append_only_audit_sink import InMemoryMessageAuditSink
from autofirm.comms.dynamic_agent_registry import DynamicAgentRegistry
from autofirm.comms.injectable_delivery_clock import ManualClock
from autofirm.comms.inter_agent_message_bus import InterAgentMessageBus
from autofirm.comms.message_envelope_contract import MessageEnvelope
from autofirm.e2e.company_build_flow import CEO_ROLE, FOUNDING_EPOCH
from autofirm.e2e.public_company_scenarios import PublicCompanyScenario
from autofirm.e2e.scenario_result_contract import (
    FeatureCheck,
    FeatureName,
    FeatureStatus,
)
from autofirm.frontdoor.front_desk_request_router import FrontDeskRequestRouter
from autofirm.frontdoor.front_door_provenance_trail import (
    InMemoryFrontDoorProvenanceTrail,
)
from autofirm.frontdoor.front_door_request_dispatcher import FrontDoorRequestDispatcher
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
from autofirm.org.org_identifiers import FrozenClock, RoleId, SequentialIdGenerator
from autofirm.org.org_lifecycle_engine import DynamicOrg


def check_front_door_routing(
    scenario: PublicCompanyScenario, org: DynamicOrg
) -> FeatureCheck:
    """Route the owner's question over the live company; assert it reaches a handler.

    Every founded role is public-cleared and given a live (silent) bus handler, so
    the request is delivered to whichever role the router selects — a capable role
    when the question matches one's vocabulary, else the CEO triage fallback. The
    response must name a non-empty handler and be recorded in the provenance trail.
    """
    role_ids = tuple(str(rid) for rid in org.state.hierarchy.role_ids())
    clearances = {RoleId(rid): PUBLIC_CLEARANCE for rid in role_ids}
    index = RoleCapabilityIndex.from_org_state(
        org.state,
        triage_role_id=RoleId(CEO_ROLE),
        required_clearances=clearances,
    )
    router = FrontDeskRequestRouter(
        capability_index=index,
        classifier=KeywordIntentClassifier(),
        clock=FrozenClock(FOUNDING_EPOCH, step_seconds=1.0),
    )

    registry = DynamicAgentRegistry()
    for rid in role_ids:
        registry.register_agent(rid, _silent_handler)
    audit = InMemoryMessageAuditSink()
    bus = InterAgentMessageBus(registry=registry, audit_sink=audit, clock=ManualClock())
    trail = InMemoryFrontDoorProvenanceTrail()
    dispatcher = FrontDoorRequestDispatcher(
        router=router,
        message_bus=bus,
        provenance_trail=trail,
        clock=FrozenClock(FOUNDING_EPOCH, step_seconds=1.0),
        id_generator=SequentialIdGenerator(),
    )

    request = HumanRequest(
        correlation_id=f"owner-{scenario.slug}",
        requester=RequesterIdentity(
            requester_id=f"owner-{scenario.slug}",
            display_name="Company Owner",
            clearances=frozenset(),
        ),
        channel=RequestChannel.API,
        body=scenario.owner_question,
        received_at=FOUNDING_EPOCH,
    )
    response = asyncio.run(dispatcher.handle(request))
    routed = (
        response.handler_role_id != ""  # a real handler always receives it
        and response.accepted  # the chosen handler actually received it over the bus
        and len(trail.entries()) == 1  # the routing is recorded end-to-end
    )
    return FeatureCheck(
        feature=FeatureName.FRONT_DOOR_ROUTING,
        phase="operate",
        status=FeatureStatus.PASSED if routed else FeatureStatus.FAILED,
        detail="human question routed to a real handler over the live bus",
        evidence={
            "handler_role": response.handler_role_id,
            "outcome": response.routing_outcome.value,
        },
    )


async def _silent_handler(envelope: MessageEnvelope) -> None:
    """A live but silent bus handler so every routed request is deliverable."""
    return None
