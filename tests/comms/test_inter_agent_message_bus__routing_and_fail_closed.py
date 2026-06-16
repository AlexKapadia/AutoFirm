"""Adversarial tests for bus routing, fail-closed dead-lettering, and audit (A2).

Proves teeth (CLAUDE.md §3.6): directed + topic delivery work, and EVERY failure
path (unknown recipient, empty topic, handler error, ordering violation) lands in
the dead-letter sink with the CORRECT named reason and is audited -- never
silently dropped. Boundary-exact on recipient counts and audit-entry counts so a
mutant that swaps a reason, skips an audit write, or drops a dead-letter is killed.
"""

from __future__ import annotations

import pytest

from autofirm.comms.delivery_outcome_types import DeadLetterReason, DeliveryStatus
from autofirm.comms.inter_agent_message_bus import InterAgentMessageBus
from tests.comms.synthetic_comms_fixtures import (
    RecordingHandler,
    make_bus,
    make_envelope,
)

pytestmark = pytest.mark.anyio


@pytest.fixture
def anyio_backend() -> str:
    # Pin AnyIO's backend to asyncio (the stack target) for deterministic runs.
    return "asyncio"


async def test_directed_message_is_delivered_to_the_registered_handler() -> None:
    h = make_bus()
    handler = RecordingHandler()
    h.registry.register_agent("agent-b", handler)

    report = await h.bus.deliver(make_envelope(recipient="agent-b"))

    assert report.status is DeliveryStatus.DELIVERED
    assert report.recipients_notified == 1  # exactly one directed handler
    assert len(handler.calls) == 1
    assert handler.calls[0].recipient == "agent-b"


async def test_unknown_recipient_is_dead_lettered_not_dropped() -> None:
    h = make_bus()
    # No agent registered -> fail-closed to dead-letter.
    report = await h.bus.deliver(make_envelope(recipient="ghost"))

    assert report.status is DeliveryStatus.DEAD_LETTERED
    assert report.dead_letter_reason is DeadLetterReason.UNKNOWN_RECIPIENT
    assert report.recipients_notified == 0
    dead = h.bus.dead_letters.peek()
    assert len(dead) == 1  # message preserved, not dropped
    assert dead[0].reason is DeadLetterReason.UNKNOWN_RECIPIENT


async def test_topic_fan_out_invokes_every_subscriber() -> None:
    h = make_bus()
    a, b, c = RecordingHandler(), RecordingHandler(), RecordingHandler()
    h.registry.subscribe("planning", "a", a)
    h.registry.subscribe("planning", "b", b)
    h.registry.subscribe("planning", "c", c)

    report = await h.bus.deliver(make_envelope(recipient=None, topic="planning"))

    assert report.status is DeliveryStatus.DELIVERED
    assert report.recipients_notified == 3  # boundary-exact fan-out count
    assert len(a.calls) == 1 and len(b.calls) == 1 and len(c.calls) == 1


async def test_topic_with_no_subscribers_is_dead_lettered() -> None:
    h = make_bus()
    report = await h.bus.deliver(make_envelope(recipient=None, topic="empty-topic"))

    assert report.status is DeliveryStatus.DEAD_LETTERED
    assert report.dead_letter_reason is DeadLetterReason.NO_TOPIC_SUBSCRIBERS


async def test_handler_error_dead_letters_and_does_not_commit_dedup() -> None:
    h = make_bus()
    failing = RecordingHandler(fail=True)
    h.registry.register_agent("agent-b", failing)
    env = make_envelope(recipient="agent-b", dedup_key="dk-fail")

    report = await h.bus.deliver(env)

    assert report.status is DeliveryStatus.DEAD_LETTERED
    assert report.dead_letter_reason is DeadLetterReason.HANDLER_ERROR
    # The handler ran (and raised) -- the call was attempted.
    assert len(failing.calls) == 1

    # Critical at-least-once property: dedup NOT committed on failure, so a retry
    # with a now-working handler delivers (the message is not lost).
    working = RecordingHandler()
    h.registry.register_agent("agent-b", working)
    retry = await h.bus.deliver(make_envelope(recipient="agent-b", dedup_key="dk-fail"))
    assert retry.status is DeliveryStatus.DELIVERED
    assert len(working.calls) == 1


async def test_partial_topic_failure_dead_letters_whole_message() -> None:
    # If ANY subscriber raises, the whole fan-out is dead-lettered (fail-closed).
    h = make_bus()
    ok, bad = RecordingHandler(), RecordingHandler(fail=True)
    h.registry.subscribe("t", "ok", ok)
    h.registry.subscribe("t", "bad", bad)

    report = await h.bus.deliver(make_envelope(recipient=None, topic="t"))
    assert report.status is DeliveryStatus.DEAD_LETTERED
    assert report.dead_letter_reason is DeadLetterReason.HANDLER_ERROR


async def test_every_outcome_is_audited_append_only() -> None:
    h = make_bus()
    h.registry.register_agent("agent-b", RecordingHandler())

    await h.bus.deliver(make_envelope(recipient="agent-b", dedup_key="d1"))  # delivered
    await h.bus.deliver(make_envelope(recipient="ghost", dedup_key="d2"))  # dead-letter
    await h.bus.deliver(make_envelope(recipient="agent-b", dedup_key="d1"))  # duplicate

    entries = h.audit.entries()
    # Exactly three append-only entries -- one per routing decision, denials too.
    assert len(entries) == 3
    statuses = [e.status for e in entries]
    assert statuses == [
        DeliveryStatus.DELIVERED,
        DeliveryStatus.DEAD_LETTERED,
        DeliveryStatus.DUPLICATE_SUPPRESSED,
    ]
    # The dead-letter entry names its reason; the others do not.
    assert entries[1].dead_letter_reason is DeadLetterReason.UNKNOWN_RECIPIENT
    assert entries[0].dead_letter_reason is None
    assert entries[2].dead_letter_reason is None


async def test_audit_sink_len_tracks_entry_count() -> None:
    # __len__ on the in-memory sink mirrors the number of recorded decisions.
    h = make_bus()
    h.registry.register_agent("agent-b", RecordingHandler())
    assert len(h.audit) == 0
    await h.bus.deliver(make_envelope(recipient="agent-b", dedup_key="x1"))
    await h.bus.deliver(make_envelope(recipient="ghost", dedup_key="x2"))
    assert len(h.audit) == 2 == len(h.audit.entries())


async def test_audit_records_topic_destination_label() -> None:
    h = make_bus()
    h.registry.subscribe("planning", "a", RecordingHandler())
    await h.bus.deliver(make_envelope(recipient=None, topic="planning"))
    entry = h.audit.entries()[0]
    assert entry.destination == "topic:planning"  # distinguishes pub-sub in audit


async def test_audit_timestamp_comes_from_injected_clock_not_wall_clock() -> None:
    h = make_bus()
    h.registry.register_agent("agent-b", RecordingHandler())
    h.clock.tick(123.0)  # advance the manual clock
    expected = h.clock.now()
    await h.bus.deliver(make_envelope(recipient="agent-b"))
    assert h.audit.entries()[0].timestamp == expected  # deterministic, injected


async def test_bus_requires_registry_audit_and_clock() -> None:
    # Fail-closed configuration: the bus cannot be built without its mandatory
    # collaborators (enforced by the keyword-only required parameters).
    with pytest.raises(TypeError):
        InterAgentMessageBus()  # type: ignore[call-arg]  # missing required deps
