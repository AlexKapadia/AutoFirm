"""Delivery outcome + dead-letter reason types for the comms plane.

What this does
--------------
Defines the closed enums and frozen result records the bus returns from a
``deliver`` call: :class:`DeliveryStatus` (what happened), :class:`DeadLetterReason`
(why a message could not be delivered/processed), and :class:`DeliveryReport`
(the per-message outcome the caller and audit trail consume). These are pure data
-- no behaviour -- so every routing decision is reportable and explainable
(CLAUDE §3.11 explain-every-decision).

Why it exists / where it sits
-----------------------------
Separating the *vocabulary of outcomes* from the bus mechanics keeps the bus file
focused and gives the audit sink + dead-letter queue a single, typed shape to
record. Every non-delivery is a *named* reason, never a silent drop (§5.6).

Security / compliance invariants upheld
---------------------------------------
* **No silent drops (§5.6):** a message that cannot be delivered always yields a
  :class:`DeliveryStatus.DEAD_LETTERED` report with an explicit
  :class:`DeadLetterReason` -- the fail-closed path is observable and audited.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict

__all__ = [
    "DeadLetterReason",
    "DeliveryReport",
    "DeliveryStatus",
]


class DeliveryStatus(StrEnum):
    """Terminal outcome of routing one envelope (deterministic, exhaustive)."""

    DELIVERED = "delivered"  # handler(s) invoked and returned without raising
    DUPLICATE_SUPPRESSED = "duplicate_suppressed"  # dedup_key already committed
    DEAD_LETTERED = "dead_lettered"  # could not deliver/process -> dead-letter sink


class DeadLetterReason(StrEnum):
    """Why a message landed in the dead-letter sink (named, never silent)."""

    UNKNOWN_RECIPIENT = "unknown_recipient"  # directed address not in registry
    NO_TOPIC_SUBSCRIBERS = "no_topic_subscribers"  # topic has zero subscribers
    HANDLER_ERROR = "handler_error"  # a subscribed handler raised
    ORDERING_VIOLATION = "ordering_violation"  # out-of-order causal_seq rejected


class DeliveryReport(BaseModel):
    """The explainable, per-message outcome of a ``deliver`` call (frozen).

    ``dead_letter_reason`` is set IFF ``status`` is ``DEAD_LETTERED`` -- this is
    the explain-every-decision record (§3.11): the report names what happened and,
    on the fail-closed path, exactly why.
    """

    model_config = ConfigDict(frozen=True)

    dedup_key: str
    conversation_id: str
    status: DeliveryStatus
    recipients_notified: int  # how many handlers were actually invoked
    dead_letter_reason: DeadLetterReason | None = None
