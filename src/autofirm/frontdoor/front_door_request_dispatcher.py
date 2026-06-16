"""The front-door request dispatcher: the end-to-end human->company handling service.

What this does
--------------
Defines :class:`FrontDoorRequestDispatcher` — the single service that takes a validated
:class:`~autofirm.frontdoor.human_request_contract.HumanRequest` and drives the WHOLE
front-door flow: it routes the request (via the front-desk request router), delivers it
to the chosen role over the inter-agent
:class:`~autofirm.comms.inter_agent_message_bus.InterAgentMessageBus`, records a complete
provenance entry to the append-only trail, and returns a provenance-bearing
:class:`~autofirm.frontdoor.front_door_response_contract.FrontDoorResponse`.

Why it exists / where it sits
-----------------------------
This is where the human-facing surface meets the existing internal machinery: the front
desk decides WHO handles a request; the comms bus is HOW the request reaches that handler
(reusing its dedup, ordering, fail-closed dead-lettering, and its own audit). The
dispatcher is the join point and the only place that touches all three subsystems, so the
end-to-end guarantee — every request routed, delivered (or fail-closed), and audited with
full provenance — lives in one auditable place.

Security / compliance invariants upheld
---------------------------------------
* **No request lost (fail-closed end-to-end, CLAUDE.md §5.6):** the router always yields
  a decision (a capable role or triage), so a handler address always exists; the bus
  fail-closes any undeliverable message to its dead-letter sink; the dispatcher records
  provenance and returns a response on EVERY path — there is no silent drop anywhere.
* **Provenance / audit always complete (§3.11):** every handled request appends exactly
  one provenance entry (routed or triaged, delivered or dead-lettered) AND the bus
  appends its own delivery audit — the request is auditable end-to-end via the shared
  correlation id.
* **Least privilege (§5.6):** routing already removed roles the requester may not reach,
  so the dispatcher can only ever address a permitted role (or triage) — it never widens
  access.
* **Determinism (§3.11):** every timestamp and every id (dedup / correlation) comes from
  injected seams (clock, id-generator); the dispatcher reads no wall clock and no
  randomness, so a fixed request + fixed seams replay identically.
"""

from __future__ import annotations

from autofirm.comms.delivery_outcome_types import DeliveryReport, DeliveryStatus
from autofirm.comms.inter_agent_message_bus import InterAgentMessageBus
from autofirm.comms.message_envelope_contract import MessageEnvelope, Performative
from autofirm.frontdoor.front_desk_request_router import FrontDeskRequestRouter
from autofirm.frontdoor.front_door_provenance_trail import (
    FrontDoorProvenanceEntry,
    FrontDoorProvenanceTrail,
)
from autofirm.frontdoor.front_door_response_contract import FrontDoorResponse
from autofirm.frontdoor.human_request_contract import HumanRequest
from autofirm.frontdoor.routing_decision_contract import RoutingDecision
from autofirm.org.org_identifiers import Clock, IdGenerator

__all__ = ["FrontDoorRequestDispatcher"]

# The conversation/causal position the front door assigns to the single inbound human
# request. Each human request opens a FRESH conversation (its correlation id), so it is
# always the first message in that conversation — position 0 (the bus requires a
# non-negative monotonic counter; the human turn is always the opener).
_FIRST_TURN_IN_CONVERSATION = 0


class FrontDoorRequestDispatcher:
    """Routes, delivers, audits, and answers one human request end-to-end.

    Stateless across calls apart from its injected collaborators (router, bus, provenance
    trail, clock, id-generator), all supplied at construction — fail-closed configuration
    with no hidden global state.
    """

    __slots__ = ("_bus", "_clock", "_ids", "_provenance", "_router")

    def __init__(
        self,
        *,
        router: FrontDeskRequestRouter,
        message_bus: InterAgentMessageBus,
        provenance_trail: FrontDoorProvenanceTrail,
        clock: Clock,
        id_generator: IdGenerator,
    ) -> None:
        """Wire the dispatcher from its collaborators (dependency injection, fail-closed).

        All five are mandatory (no defaults): the dispatcher refuses to exist without a
        router (whom to send to), a bus (how to send), a provenance trail (the audit
        seam), a clock, and an id-generator (deterministic time + ids) — §5.6.
        """
        self._router = router
        self._bus = message_bus
        self._provenance = provenance_trail
        self._clock = clock
        self._ids = id_generator

    async def handle(self, request: HumanRequest) -> FrontDoorResponse:
        """Route, deliver, audit, and answer ``request`` — the full front-door flow.

        Always returns a :class:`FrontDoorResponse` and always appends exactly one
        provenance entry, on every path (routed or triaged, delivered or dead-lettered).
        """
        decision = self._router.route(request)
        delivery = await self._deliver_to_handler(request, decision)
        # Provenance is recorded for EVERY outcome — including a triage fallback or a
        # dead-lettered delivery — so the trail proves what happened, not just successes.
        self._record_provenance(request, decision, delivery.status)
        # `accepted` is the fail-closed bottom line: True ONLY when the bus actually
        # delivered to the chosen handler. A dead-letter or suppression is NOT acceptance,
        # so the human is never told an unhandled request was handled (§5.6).
        accepted = delivery.status is DeliveryStatus.DELIVERED
        return FrontDoorResponse(
            correlation_id=request.correlation_id,
            accepted=accepted,
            routing_outcome=decision.outcome,
            handler_role_id=str(decision.chosen_role_id),
            handler_role_title=decision.chosen_role_title,
            routing_reason=decision.reason,
            delivery_status=delivery.status,
            responded_at=self._clock.now(),  # injected clock, never the wall clock
        )

    async def _deliver_to_handler(
        self, request: HumanRequest, decision: RoutingDecision
    ) -> DeliveryReport:
        """Deliver the request to the decision's chosen role over the inter-agent bus.

        The chosen role id (a capable role OR triage — always present) is the directed
        recipient. The bus re-validates the envelope and fail-closes any undeliverable
        message (e.g. the role has no registered handler) to its dead-letter sink with a
        named reason — so even a routing-correct-but-undeliverable request is observable,
        never dropped.
        """
        envelope = MessageEnvelope(
            performative=Performative.REQUEST,  # a human asking the company to act
            sender=request.requester.requester_id,  # provenance: WHO originated it
            recipient=str(decision.chosen_role_id),  # the resolved handler (or triage)
            conversation_id=request.correlation_id,  # shared end-to-end trace key
            causal_seq=_FIRST_TURN_IN_CONVERSATION,  # the human turn opens the conversation
            # A fresh, deterministic dedup key per request: re-handling the SAME request
            # object would re-route, but each `handle` call mints a new key from the
            # injected id-generator, so delivery idempotency is the bus's concern, not
            # an accidental cross-request collision.
            dedup_key=self._ids.next_id(f"frontdoor-{request.correlation_id}"),
            # The UNTRUSTED human body is carried as opaque payload data; the bus routes
            # it but never interprets it, and the boundary already capped its size.
            payload={"body": request.body, "channel": request.channel.value},
            timestamp=self._clock.now(),  # injected clock, never the wall clock
        )
        return await self._bus.deliver(envelope)

    def _record_provenance(
        self,
        request: HumanRequest,
        decision: RoutingDecision,
        delivery_status: DeliveryStatus,
    ) -> None:
        """Append the complete provenance entry for this request (append-only, §5.6)."""
        self._provenance.record(
            FrontDoorProvenanceEntry(
                correlation_id=request.correlation_id,
                requester_id=request.requester.requester_id,
                requester_display_name=request.requester.display_name,
                routing_outcome=decision.outcome,
                handler_role_id=str(decision.chosen_role_id),
                handler_role_title=decision.chosen_role_title,
                routing_reason=decision.reason,
                delivery_status=delivery_status,
                recorded_at=self._clock.now(),  # injected clock, never the wall clock
            )
        )
