"""AutoFirm front door: the human->company interaction & intelligent-routing surface.

This package is the outer interface where a HUMAN asks a question or makes a request and
it is routed to the correct role/team and answered — distinct from the internal
agent<->agent message bus (:mod:`autofirm.comms`), which this layer routes *over*. A human
does not need to know the org chart: they send a typed :class:`HumanRequest` and the front
desk resolves the right handler from capabilities derived from the live org, fails closed
to a single triage role when nothing capable/permitted matches, delivers over the bus, and
returns a provenance-bearing :class:`FrontDoorResponse` — auditable end-to-end.

Layering (low -> high):
* :mod:`~autofirm.frontdoor.human_request_contract` — the validated, untrusted-input
  boundary (:class:`HumanRequest` / :class:`RequesterIdentity` / :class:`RequestChannel`).
* :mod:`~autofirm.frontdoor.role_capability_index` — routable capabilities derived from
  the live :class:`~autofirm.org.org_state.OrgState`, with least-privilege clearances and
  one validated triage fallback.
* :mod:`~autofirm.frontdoor.request_intent_classifier` — the injectable classifier seam
  (deterministic keyword reference impl; swappable for a learned classifier).
* :mod:`~autofirm.frontdoor.requester_clearance_gate` — the least-privilege predicate.
* :mod:`~autofirm.frontdoor.routing_decision_contract` — the explainable decision.
* :mod:`~autofirm.frontdoor.front_desk_request_router` — classify -> match -> clearance ->
  select-or-triage (fail-closed; no request lost, no mis-route).
* :mod:`~autofirm.frontdoor.front_door_provenance_trail` — the append-only human-facing
  audit seam.
* :mod:`~autofirm.frontdoor.front_door_request_dispatcher` — the end-to-end service
  (route -> deliver over the bus -> audit -> respond).
"""

from __future__ import annotations

from autofirm.frontdoor.front_desk_request_router import FrontDeskRequestRouter
from autofirm.frontdoor.front_door_provenance_trail import (
    FrontDoorProvenanceEntry,
    FrontDoorProvenanceTrail,
    InMemoryFrontDoorProvenanceTrail,
)
from autofirm.frontdoor.front_door_request_dispatcher import FrontDoorRequestDispatcher
from autofirm.frontdoor.front_door_response_contract import FrontDoorResponse
from autofirm.frontdoor.human_request_contract import (
    HumanRequest,
    RequestChannel,
    RequesterIdentity,
)
from autofirm.frontdoor.request_intent_classifier import (
    KeywordIntentClassifier,
    RequestIntentClassifier,
)
from autofirm.frontdoor.requester_clearance_gate import requester_may_reach
from autofirm.frontdoor.role_capability_index import (
    PUBLIC_CLEARANCE,
    UNREACHABLE_CLEARANCE,
    RoleCapability,
    RoleCapabilityIndex,
)
from autofirm.frontdoor.routing_decision_contract import RoutingDecision, RoutingOutcome

__all__ = [
    "PUBLIC_CLEARANCE",
    "UNREACHABLE_CLEARANCE",
    "FrontDeskRequestRouter",
    "FrontDoorProvenanceEntry",
    "FrontDoorProvenanceTrail",
    "FrontDoorRequestDispatcher",
    "FrontDoorResponse",
    "HumanRequest",
    "InMemoryFrontDoorProvenanceTrail",
    "KeywordIntentClassifier",
    "RequestChannel",
    "RequestIntentClassifier",
    "RequesterIdentity",
    "RoleCapability",
    "RoleCapabilityIndex",
    "RoutingDecision",
    "RoutingOutcome",
    "requester_may_reach",
]
