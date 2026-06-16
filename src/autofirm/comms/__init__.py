"""Reliable, audited inter-agent message bus (A2; comms plane).

The whole org's effectiveness depends on reliable, audited inter-team comms
(AutoFirm memory: comms is one of the MOST important subsystems). This package
implements the A2-SYNTHESIS contract: a typed, intent-bearing message envelope
routed over a dynamic topology (agents/teams added/removed at runtime), with
at-least-once delivery, idempotent dedup, per-conversation ordering, fail-closed
routing to a dead-letter sink, and an append-only audit trail of every routed
message.

Delivery guarantee (stated precisely, no myths): **at-least-once with idempotent
dedup => effective at-most-once *per dedup key*, and per-conversation FIFO
ordering**. A handler may be invoked more than once for the same logical message
ONLY if it crashes after acting but before the dedup key is committed; the dedup
store makes a *committed* delivery exactly once. This is NOT exactly-once
end-to-end (an unattainable distributed myth) -- it is at-least-once + dedup.
"""

from __future__ import annotations

from autofirm.comms.append_only_audit_sink import (
    InMemoryMessageAuditSink,
    MessageAuditEntry,
    MessageAuditSink,
)
from autofirm.comms.conversation_ordering_tracker import ConversationOrderingTracker
from autofirm.comms.dead_letter_queue import DeadLetter, DeadLetterQueue
from autofirm.comms.delivery_outcome_types import (
    DeadLetterReason,
    DeliveryReport,
    DeliveryStatus,
)
from autofirm.comms.dynamic_agent_registry import DynamicAgentRegistry, MessageHandler
from autofirm.comms.idempotent_dedup_store import IdempotentDedupStore
from autofirm.comms.injectable_delivery_clock import (
    DeliveryClock,
    ManualClock,
    SystemClock,
)
from autofirm.comms.inter_agent_message_bus import InterAgentMessageBus
from autofirm.comms.message_envelope_contract import (
    MAX_PAYLOAD_BYTES,
    MessageEnvelope,
    Performative,
)

__all__ = [
    "MAX_PAYLOAD_BYTES",
    "ConversationOrderingTracker",
    "DeadLetter",
    "DeadLetterQueue",
    "DeadLetterReason",
    "DeliveryClock",
    "DeliveryReport",
    "DeliveryStatus",
    "DynamicAgentRegistry",
    "IdempotentDedupStore",
    "InMemoryMessageAuditSink",
    "InterAgentMessageBus",
    "ManualClock",
    "MessageAuditEntry",
    "MessageAuditSink",
    "MessageEnvelope",
    "MessageHandler",
    "Performative",
    "SystemClock",
]
