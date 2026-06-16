"""Typed, validated inter-agent message envelope (FIPA-derived; A2.1).

What this does
--------------
Defines :class:`MessageEnvelope`, the single typed contract every inter-agent
message must satisfy, plus the closed :class:`Performative` intent set. The
envelope carries who sent it, who/what it is for (a directed recipient OR a
pub-sub topic -- exactly one), the conversation/correlation id, the causal
ordering sequence, the idempotent dedup key, the payload, and an injected
timestamp. Validation happens at construction (the boundary), so a malformed or
oversized message can never enter the bus.

Why it exists / where it sits
-----------------------------
Per ``docs/research/A2-agent-communication-and-flow/SYNTHESIS.md`` §3 the A2
contract is a FIPA-derived envelope {intent/performative (closed set), sender,
receiver, content, conversation-id, ...}. This is the *boundary* of the comms
plane: all message content is treated as UNTRUSTED (injection defence -- CLAUDE
§5.6), so payload size and field shapes are bounded here and nowhere downstream
has to re-validate.

Security / compliance invariants upheld
---------------------------------------
* **Validate input at the boundary, deny by default (§5.6):** every field is
  pydantic-validated; an unknown performative, an empty sender, a recipient that
  is neither a directed address nor a topic, BOTH a directed address and a topic,
  or an over-cap payload are all REFUSED at construction (fail-closed) rather than
  routed.
* **Injection defence:** the payload is an opaque mapping with a hard byte cap;
  the bus never interprets payload content, only routes it.
* **Determinism (§3.11):** the timestamp is injected by the caller (from the
  bus's clock), never read from the wall clock here, so envelopes are
  reproducible in tests and replay.
"""

from __future__ import annotations

import json
from datetime import datetime
from enum import StrEnum
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, StringConstraints, field_validator, model_validator

__all__ = [
    "MAX_PAYLOAD_BYTES",
    "MessageEnvelope",
    "Performative",
]

# Hard payload byte cap (injection / resource-exhaustion defence -- §5.6). A
# message whose serialised payload exceeds this is refused at the boundary, never
# routed, so a single oversized message can neither exhaust memory nor wedge a
# handler. Chosen generously for structured agent payloads; tune per deployment.
MAX_PAYLOAD_BYTES = 256 * 1024  # 256 KiB

# A non-empty, length-bounded identifier (agent id, role, topic, conversation id,
# dedup key). Bounding length is part of the injection defence: an unbounded id
# is a resource-exhaustion and log-poisoning vector.
_Id = Annotated[str, StringConstraints(min_length=1, max_length=512, strip_whitespace=True)]


class Performative(StrEnum):
    """Closed set of message intents (FIPA-derived; A2.1 ADOPT bounded set).

    A closed set (not free text) is what lets routing and verification reason
    about intent deterministically. An out-of-set performative is refused at the
    boundary (fail-closed) -- the synthesis REJECTs free-text-only emergent
    chatter as the dominant mode.
    """

    REQUEST = "request"  # ask the recipient to perform an action
    INFORM = "inform"  # share a fact / result
    PROPOSE = "propose"  # Contract-Net bid / offer
    ACCEPT = "accept"  # award / agree
    REJECT = "reject"  # decline
    FAILURE = "failure"  # report an action failed
    QUERY = "query"  # ask for information


class MessageEnvelope(BaseModel):
    """One typed inter-agent message (frozen once built -- append-only semantics).

    Exactly one of ``recipient`` (directed) or ``topic`` (pub-sub) is set; the
    bus routes on whichever is present. ``conversation_id`` correlates a
    multi-message exchange; ``causal_seq`` is the sender-assigned, monotonically
    increasing position within that conversation (the ordering key). ``dedup_key``
    is the stable idempotency key: two envelopes with the same key are the SAME
    logical message and the second delivery is suppressed.
    """

    model_config = ConfigDict(frozen=True)

    performative: Performative
    sender: _Id
    recipient: _Id | None = None  # directed address (agent id or role)
    topic: _Id | None = None  # pub-sub topic; mutually exclusive with recipient
    conversation_id: _Id
    causal_seq: int  # sender-assigned FIFO position within the conversation
    dedup_key: _Id  # stable idempotency key (effective at-most-once per key)
    payload: dict[str, Any]
    timestamp: datetime  # injected by the bus clock, never the wall clock here

    @field_validator("causal_seq")
    @classmethod
    def _causal_seq_non_negative(cls, value: int) -> int:
        # fail-closed: ordering positions are non-negative monotonic counters; a
        # negative position is malformed and could corrupt per-conversation order.
        if value < 0:
            raise ValueError("causal_seq must be >= 0 (monotonic per-conversation counter)")
        return value

    @model_validator(mode="after")
    def _exactly_one_destination(self) -> MessageEnvelope:
        """Fail-closed: exactly one of recipient / topic must be set (§5.6).

        Neither set => undeliverable (no destination). Both set => ambiguous
        routing. Either way we REFUSE at the boundary rather than guess a
        destination and risk mis-delivery.
        """
        has_recipient = self.recipient is not None
        has_topic = self.topic is not None
        if has_recipient == has_topic:
            # Both True (ambiguous) or both False (no destination) -> refuse.
            raise ValueError("exactly one of 'recipient' or 'topic' must be set")
        return self

    @model_validator(mode="after")
    def _payload_within_cap(self) -> MessageEnvelope:
        """Fail-closed: refuse an over-cap payload at the boundary (§5.6).

        The payload is UNTRUSTED content. We measure its canonical serialised
        size and refuse anything over ``MAX_PAYLOAD_BYTES`` so an oversized
        message cannot exhaust memory or wedge a downstream handler.
        """
        try:
            size = len(json.dumps(self.payload, separators=(",", ":")).encode("utf-8"))
        except (TypeError, ValueError) as exc:
            # A payload that is not JSON-serialisable is malformed/untrusted ->
            # refuse rather than route an unserialisable blob (fail-closed).
            raise ValueError("payload must be JSON-serialisable") from exc
        if size > MAX_PAYLOAD_BYTES:
            raise ValueError(
                f"payload size {size} exceeds MAX_PAYLOAD_BYTES {MAX_PAYLOAD_BYTES}"
            )
        return self
