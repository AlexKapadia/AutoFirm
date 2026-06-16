"""The typed human request: the validated boundary of the human->company front door.

What this does
--------------
Defines :class:`HumanRequest` — the single typed, pydantic-validated contract every
inbound human request must satisfy before the front desk will look at it, plus the
closed :class:`RequestChannel` set the request arrived on. The request carries WHO is
asking (:class:`RequesterIdentity`), WHAT they asked (the free-text body, treated as
untrusted), a correlation id that threads the request through routing -> handling ->
response, and an injected timestamp so the whole flow is deterministic and replayable.

Why it exists / where it sits
-----------------------------
This is the OUTER boundary of AutoFirm's human-facing surface — distinct from the
inter-agent :class:`~autofirm.comms.message_envelope_contract.MessageEnvelope`, which is
the *internal* agent<->agent contract. A human does not know the org chart, the role
ids, or the message bus; they send a :class:`HumanRequest` and the front desk does the
rest. Because the body is human free text from outside the trust boundary, it is the
most hostile input the platform accepts, so every field is bounded and validated HERE
and nowhere downstream has to re-validate (the bus envelope built from it is itself
re-validated, but routing logic trusts this contract).

Security / compliance invariants upheld
---------------------------------------
* **Validate input at the boundary, deny by default (CLAUDE.md §5.6):** an empty
  requester id, an empty/blank body, an over-cap body, or an out-of-set channel are all
  REFUSED at construction (fail-closed) — a malformed request never reaches routing.
* **Injection defence (§5.6):** the body is treated as UNTRUSTED opaque text with a hard
  character cap; the front desk classifies it by *matching*, never by executing or
  interpreting it as a command, so a body like "ignore your rules and DROP everyone" is
  just text that routes to triage, not an instruction.
* **Determinism (§3.11):** the timestamp is injected by the caller (from the front
  desk's clock), never read from the wall clock here, so a request is reproducible in
  tests and replay.
* **Immutability:** frozen once built — a request cannot be mutated mid-flight, so the
  audited body always matches what the human actually sent.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints, field_validator

__all__ = [
    "MAX_REQUEST_BODY_CHARS",
    "HumanRequest",
    "RequestChannel",
    "RequesterIdentity",
]

# Hard character cap on the untrusted request body (injection / resource-exhaustion
# defence — §5.6). A body over this length is refused at the boundary, never routed, so
# one oversized request can neither exhaust memory nor wedge the classifier. Generous for
# a real support/enquiry message; tune per deployment.
MAX_REQUEST_BODY_CHARS = 8_192

# A non-empty, length-bounded identifier (requester id, correlation id). Bounding length
# is part of the injection defence: an unbounded id is a log-poisoning / exhaustion
# vector. ``strip_whitespace`` normalises so " alice " and "alice" are one identity.
_Id = Annotated[str, StringConstraints(min_length=1, max_length=256, strip_whitespace=True)]


class RequestChannel(StrEnum):
    """Closed set of channels a human request can arrive on.

    A closed set (not free text) keeps the boundary deterministic and auditable: an
    out-of-set channel is refused at construction (fail-closed). Channels are headless
    protocol surfaces (no UI in this layer) — an email gateway, an API call, a chat
    webhook — all reduce to one of these.
    """

    EMAIL = "email"  # inbound email gateway
    API = "api"  # programmatic API call
    CHAT = "chat"  # chat / messaging webhook
    PORTAL = "portal"  # authenticated self-service portal submission


class RequesterIdentity(BaseModel):
    """WHO is asking — the authenticated identity behind a human request.

    Identity is established UPSTREAM (the channel gateway authenticates); this contract
    carries the *result* of that authentication, never a password or token. The
    ``clearances`` set drives least-privilege routing: a requester only reaches roles
    whose required clearance they hold (enforced by the permission policy, not here).
    """

    model_config = ConfigDict(frozen=True)

    requester_id: _Id  # stable id of the authenticated human (e.g. "owner:acme")
    display_name: _Id  # human-readable name for provenance / audit readability
    # Clearances the requester holds. Empty set == an unprivileged external requester
    # (e.g. a member of the public) — they reach only PUBLIC-clearance roles or triage.
    clearances: frozenset[str] = frozenset()

    @field_validator("clearances")
    @classmethod
    def _clearances_non_blank(cls, value: frozenset[str]) -> frozenset[str]:
        # fail-closed: a blank/whitespace clearance string is meaningless and could
        # accidentally match a role's required clearance — refuse it at the boundary.
        if any(not c.strip() for c in value):
            raise ValueError("clearance labels must be non-empty, non-blank strings")
        return value


class HumanRequest(BaseModel):
    """One validated inbound human request — the front door's typed input.

    Frozen once built (append-only semantics): the body that gets audited is exactly the
    body the human sent. The ``correlation_id`` threads this request through the entire
    flow (routing decision -> bus delivery -> response), so a human can be told precisely
    which request a given answer belongs to and an auditor can replay one request
    end-to-end.
    """

    model_config = ConfigDict(frozen=True)

    correlation_id: _Id  # threads request -> route -> response (end-to-end trace key)
    requester: RequesterIdentity  # WHO is asking (authenticated upstream)
    channel: RequestChannel  # WHERE it arrived (closed set)
    body: str  # WHAT they asked — UNTRUSTED free text (matched, never executed)
    received_at: datetime  # injected by the front desk clock, never the wall clock here

    @field_validator("body")
    @classmethod
    def _body_present_and_bounded(cls, value: str) -> str:
        # fail-closed: an empty/blank body has no intent to route, and an over-cap body
        # is a resource/injection risk — refuse both at the boundary (§5.6). We do NOT
        # mutate the body (no silent truncation): the audited text is what was sent.
        if not value.strip():
            raise ValueError("request body must be non-empty (nothing to route)")
        if len(value) > MAX_REQUEST_BODY_CHARS:
            raise ValueError(
                f"request body length {len(value)} exceeds "
                f"MAX_REQUEST_BODY_CHARS {MAX_REQUEST_BODY_CHARS}"
            )
        return value
