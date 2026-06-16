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
