"""The front-door response: the provenance-bearing answer handed back to the human.

What this does
--------------
Defines :class:`FrontDoorResponse` — the immutable object the front door returns to a
requester for every request. It carries the correlation id (so the human knows which
request this answers), the routing decision's provenance (which role handled it, why),
and the internal delivery status (whether the chosen handler actually received it). It is
the human-facing counterpart of the internal bus
:class:`~autofirm.comms.delivery_outcome_types.DeliveryReport`.

Why it exists / where it sits
-----------------------------
The front door's response path must return the handler's result "WITH PROVENANCE (which
role handled it, when, why it was routed there)". Making that a typed value guarantees
every response — successful route, triage fallback, or a delivery that dead-lettered —
carries the same complete provenance shape, so a caller can always answer "who is
handling this and why?" without reaching into internal state.

Security / compliance invariants upheld
---------------------------------------
* **Provenance always complete (CLAUDE.md §3.11):** every response names the handling
  role, the routing reason, and the delivery status — there is no partial / provenance-
  less response.
* **Fail-closed visibility (§5.6):** a request that was triaged or whose delivery
  dead-lettered returns a response that SAYS SO (``accepted`` is False on a dead-letter),
  rather than a misleading success — the human is never told an unhandled request was
  handled.
* **Immutability:** frozen — the response a caller inspects is exactly what the front
  door produced.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from autofirm.comms.delivery_outcome_types import DeliveryStatus
from autofirm.frontdoor.routing_decision_contract import RoutingOutcome

__all__ = ["FrontDoorResponse"]


class FrontDoorResponse(BaseModel):
    """The immutable, provenance-bearing answer the front door returns to a requester.

    ``accepted`` is the single bottom-line signal: True iff the request was delivered to
    its chosen handler (the bus reported DELIVERED). A triaged request whose triage
    handler accepted it is still ``accepted`` — triage IS a valid handler — but the
    ``routing_outcome`` makes the fallback visible. A request whose delivery dead-lettered
    is ``accepted=False`` so the human is never falsely told it was handled.
    """

    model_config = ConfigDict(frozen=True)

    correlation_id: str  # threads back to the originating request
    accepted: bool  # True iff the chosen handler actually received it (fail-closed signal)
    routing_outcome: RoutingOutcome  # routed-to-capable / triaged-no-capable / triaged-no-permitted
    handler_role_id: str  # WHICH role handled it (capable role OR triage — never empty)
    handler_role_title: str  # the handler's human-readable title
    routing_reason: str  # WHY it was routed there (explain-every-decision)
    delivery_status: DeliveryStatus  # how the internal bus delivery resolved
    responded_at: datetime  # WHEN (injected clock, never the wall clock)
