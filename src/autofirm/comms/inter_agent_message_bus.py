"""The inter-agent message bus core: reliable, audited, fail-closed routing (A2).

What this does
--------------
:class:`InterAgentMessageBus` routes one validated :class:`MessageEnvelope` at a
time through a fixed, auditable pipeline and returns an explainable
:class:`DeliveryReport`. The pipeline is, in order:

1. **Dedup gate** -- if the ``dedup_key`` was already committed, suppress
   (``DUPLICATE_SUPPRESSED``); the handler is NOT invoked again.
2. **Ordering gate** -- if ``causal_seq`` is strictly below the conversation's
   high-water mark, dead-letter (``ORDERING_VIOLATION``); never deliver
   out-of-order.
3. **Resolve destination** -- directed (registry) or topic fan-out. Unknown
   recipient / empty topic => dead-letter (fail-closed), never silent drop.
4. **Invoke handler(s)** under an AnyIO structured task group. If any handler
   raises, dead-letter (``HANDLER_ERROR``) and do NOT commit the dedup key, so an
   at-least-once retry can legitimately re-attempt.
5. **Commit + audit** -- on success commit the dedup key and advance ordering;
   record an append-only audit entry for EVERY outcome (delivered, suppressed, or
   dead-lettered).

Delivery guarantee (precise, no myths): **at-least-once with idempotent dedup =>
effective at-most-once per dedup key, with per-conversation FIFO ordering.** Not
exactly-once end-to-end. A handler may run twice for one logical message only if
it acts and then the process dies before the key is committed; a *committed*
delivery is suppressed on every subsequent send of that key.

Security / compliance invariants upheld
---------------------------------------
* **Fail-closed everywhere (§5.6):** unknown recipient, no subscribers, handler
  error, and out-of-order all route to the dead-letter sink with a named reason --
  no message is ever silently dropped.
* **Audit-every-decision (§3.11, A2 top priority):** every routing outcome is
  appended to the audit sink, including denials.
* **Determinism (§3.11):** timestamps come from the injected clock; the pipeline
  has no wall-clock read and no hidden ordering nondeterminism.
* **Commit-after-success:** the dedup key and ordering high-water advance ONLY
  after handlers succeed, preserving the at-least-once contract on failure.
"""

from __future__ import annotations

import anyio

from autofirm.comms.append_only_audit_sink import MessageAuditEntry, MessageAuditSink
from autofirm.comms.conversation_ordering_tracker import ConversationOrderingTracker
from autofirm.comms.dead_letter_queue import DeadLetterQueue
from autofirm.comms.delivery_outcome_types import (
    DeadLetterReason,
    DeliveryReport,
    DeliveryStatus,
)
from autofirm.comms.dynamic_agent_registry import DynamicAgentRegistry, MessageHandler
from autofirm.comms.idempotent_dedup_store import IdempotentDedupStore
from autofirm.comms.injectable_delivery_clock import DeliveryClock
from autofirm.comms.message_envelope_contract import MessageEnvelope

__all__ = ["InterAgentMessageBus"]


class InterAgentMessageBus:
    """Routes validated envelopes with at-least-once + dedup + ordering + audit.

    Single-writer per instance: ``deliver`` is awaited one envelope at a time, so
    the dedup store, ordering tracker, registry, dead-letter queue, and audit sink
    are mutated without interleaving (no internal lock needed). Concurrency lives
    INSIDE a single deliver (fan-out to topic subscribers via a task group).
    """

    def __init__(  # noqa: PLR0913 -- explicit dependency injection of the bus's
        # six collaborators (registry/audit/clock mandatory; dedup/dead/ordering
        # injectable for tests). All keyword-only; no hidden global state.
        self,
        *,
        registry: DynamicAgentRegistry,
        audit_sink: MessageAuditSink,
        clock: DeliveryClock,
        dedup_store: IdempotentDedupStore | None = None,
        dead_letters: DeadLetterQueue | None = None,
        ordering: ConversationOrderingTracker | None = None,
    ) -> None:
        """Wire the bus from its collaborators (dependency injection).

        ``registry``, ``audit_sink`` and ``clock`` are mandatory (no defaults):
        the bus refuses to exist without a destination directory, an audit trail,
        and a deterministic time source -- fail-closed configuration (§5.6).
        """
        self._registry = registry
        self._audit = audit_sink
        self._clock = clock
        self._dedup = dedup_store if dedup_store is not None else IdempotentDedupStore()
        self._dead = dead_letters if dead_letters is not None else DeadLetterQueue()
        self._ordering = ordering if ordering is not None else ConversationOrderingTracker()

    @property
    def dead_letters(self) -> DeadLetterQueue:
        """The dead-letter sink (for operator inspection / replay)."""
        return self._dead

    async def deliver(self, envelope: MessageEnvelope) -> DeliveryReport:
        """Route one validated envelope and return its explainable outcome.

        The envelope is already boundary-validated (pydantic refused a malformed
        one at construction), so this method handles only *routing* failures, all
        fail-closed to the dead-letter sink with a named reason.
        """
        # 1. Dedup gate -- a committed key means this logical message already
        # delivered; suppress without re-invoking the handler (idempotency).
        if self._dedup.already_delivered(envelope.dedup_key):
            return self._finish(envelope, DeliveryStatus.DUPLICATE_SUPPRESSED, 0, None)

        # 2. Ordering gate -- refuse a strictly-out-of-order message (fail-closed).
        if not self._ordering.accept(envelope.conversation_id, envelope.causal_seq):
            return self._dead_letter(envelope, DeadLetterReason.ORDERING_VIOLATION)

        # 3. Resolve destination + 4. invoke handler(s). Directed and topic paths
        # are handled separately; both end in either delivery or a dead-letter.
        if envelope.recipient is not None:
            return await self._deliver_directed(envelope)
        # The envelope contract guarantees exactly one of recipient/topic is set,
        # so a missing recipient here means a topic is present.
        return await self._deliver_topic(envelope)

    async def _deliver_directed(self, envelope: MessageEnvelope) -> DeliveryReport:
        """Resolve + invoke the single directed handler (1:1 delivery)."""
        handler = self._registry.resolve_directed(envelope.recipient)  # type: ignore[arg-type]
        if handler is None:
            # fail-closed: unknown recipient is dead-lettered, never dropped (§5.6).
            return self._dead_letter(envelope, DeadLetterReason.UNKNOWN_RECIPIENT)
        return await self._invoke_and_commit(envelope, (handler,))

    async def _deliver_topic(self, envelope: MessageEnvelope) -> DeliveryReport:
        """Resolve + fan out to every current topic subscriber (pub-sub)."""
        handlers = self._registry.resolve_topic(envelope.topic)  # type: ignore[arg-type]
        if not handlers:
            # fail-closed: a topic with zero subscribers is dead-lettered with a
            # distinct reason so an operator can see the message had nowhere to go.
            return self._dead_letter(envelope, DeadLetterReason.NO_TOPIC_SUBSCRIBERS)
        return await self._invoke_and_commit(envelope, handlers)

    async def _invoke_and_commit(
        self, envelope: MessageEnvelope, handlers: tuple[MessageHandler, ...]
    ) -> DeliveryReport:
        """Invoke handlers under a task group; commit dedup ONLY on full success.

        If ANY handler raises, the structured task group propagates it, we
        dead-letter the whole message (HANDLER_ERROR) and do NOT commit the dedup
        key -- so an at-least-once retry can re-attempt. Commit-after-success is
        what keeps the guarantee at-least-once rather than at-most-once-on-failure.
        """
        try:
            async with anyio.create_task_group() as task_group:
                for handler in handlers:
                    task_group.start_soon(handler, envelope)
        except BaseExceptionGroup:
            # A subscribed handler raised. Fail-closed: dead-letter the message and
            # leave the dedup key UNcommitted so a retry is permitted (§5.6).
            return self._dead_letter(envelope, DeadLetterReason.HANDLER_ERROR)
        # Success: commit the dedup key so any re-send of this key is suppressed.
        self._dedup.commit(envelope.dedup_key)
        return self._finish(envelope, DeliveryStatus.DELIVERED, len(handlers), None)

    def _dead_letter(
        self, envelope: MessageEnvelope, reason: DeadLetterReason
    ) -> DeliveryReport:
        """Append to the dead-letter sink and finish with a DEAD_LETTERED report."""
        self._dead.add(envelope, reason)
        return self._finish(envelope, DeliveryStatus.DEAD_LETTERED, 0, reason)

    def _finish(
        self,
        envelope: MessageEnvelope,
        status: DeliveryStatus,
        recipients_notified: int,
        reason: DeadLetterReason | None,
    ) -> DeliveryReport:
        """Audit the outcome (append-only) and build the explainable report.

        Called on EVERY terminal path (delivered / suppressed / dead-lettered) so
        the audit trail records every routing decision -- the A2 top priority.
        """
        destination = (
            envelope.recipient
            if envelope.recipient is not None
            else f"topic:{envelope.topic}"
        )
        self._audit.record(
            MessageAuditEntry(
                dedup_key=envelope.dedup_key,
                conversation_id=envelope.conversation_id,
                sender=envelope.sender,
                destination=destination,
                performative=envelope.performative,
                status=status,
                recipients_notified=recipients_notified,
                timestamp=self._clock.now(),  # injected clock, never wall clock
                dead_letter_reason=reason,
            )
        )
        return DeliveryReport(
            dedup_key=envelope.dedup_key,
            conversation_id=envelope.conversation_id,
            status=status,
            recipients_notified=recipients_notified,
            dead_letter_reason=reason,
        )
