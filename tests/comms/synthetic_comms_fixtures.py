"""Synthetic fixtures + Hypothesis strategies for the comms-bus tests.

Synthetic-only (CLAUDE.md §3.12): no real agents, no network, no PII. Provides a
recording handler, an envelope factory, a fully-wired bus, and Hypothesis
strategies for property-based tests (envelopes, dedup keys, conversation streams).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from hypothesis import strategies as st

from autofirm.comms.append_only_audit_sink import InMemoryMessageAuditSink
from autofirm.comms.dynamic_agent_registry import DynamicAgentRegistry
from autofirm.comms.injectable_delivery_clock import ManualClock
from autofirm.comms.inter_agent_message_bus import InterAgentMessageBus
from autofirm.comms.message_envelope_contract import MessageEnvelope, Performative


@dataclass
class RecordingHandler:
    """An async handler that records every envelope it is invoked with.

    ``calls`` is the ordered list of delivered envelopes, so tests can assert
    exactly-once-per-key and per-conversation ordering on the *handler* side, not
    just on the bus's report.
    """

    calls: list[MessageEnvelope] = field(default_factory=list)
    fail: bool = False  # if True, the handler raises (drives the HANDLER_ERROR path)

    async def __call__(self, envelope: MessageEnvelope) -> None:
        self.calls.append(envelope)
        if self.fail:
            raise RuntimeError("synthetic handler failure")


def make_envelope(  # noqa: PLR0913 -- a test factory mirroring the envelope's
    # full field set so any field can be perturbed independently in a test.
    *,
    performative: Performative = Performative.INFORM,
    sender: str = "agent-a",
    recipient: str | None = "agent-b",
    topic: str | None = None,
    conversation_id: str = "conv-1",
    causal_seq: int = 0,
    dedup_key: str = "dk-1",
    payload: dict | None = None,
) -> MessageEnvelope:
    """Build a valid envelope with sensible synthetic defaults."""
    return MessageEnvelope(
        performative=performative,
        sender=sender,
        recipient=recipient,
        topic=topic,
        conversation_id=conversation_id,
        causal_seq=causal_seq,
        dedup_key=dedup_key,
        payload=payload if payload is not None else {"k": "v"},
        # Fixed timestamp -- the bus re-stamps audit time from its own clock.
        timestamp=ManualClock().now(),
    )


@dataclass
class BusHarness:
    """A fully-wired bus plus its collaborators, for assertion-rich tests."""

    bus: InterAgentMessageBus
    registry: DynamicAgentRegistry
    audit: InMemoryMessageAuditSink
    clock: ManualClock


def make_bus() -> BusHarness:
    """Wire a deterministic bus with an in-memory registry + audit + manual clock."""
    registry = DynamicAgentRegistry()
    audit = InMemoryMessageAuditSink()
    clock = ManualClock()
    bus = InterAgentMessageBus(registry=registry, audit_sink=audit, clock=clock)
    return BusHarness(bus=bus, registry=registry, audit=audit, clock=clock)


# ---------------------------- Hypothesis strategies ------------------------- #

# Bounded, non-empty, printable identifiers (match the _Id constraint shape).
ids = st.text(
    alphabet=st.characters(min_codepoint=33, max_codepoint=126),
    min_size=1,
    max_size=24,
)
# Small JSON-serialisable payloads.
small_payloads = st.dictionaries(
    keys=st.text(min_size=1, max_size=8),
    values=st.one_of(st.integers(-1000, 1000), st.text(max_size=16), st.booleans()),
    max_size=4,
)


@st.composite
def directed_envelopes(draw: st.DrawFn) -> MessageEnvelope:
    """Strategy producing valid directed (recipient) envelopes."""
    return make_envelope(
        sender=draw(ids),
        recipient=draw(ids),
        conversation_id=draw(ids),
        causal_seq=draw(st.integers(min_value=0, max_value=10_000)),
        dedup_key=draw(ids),
        payload=draw(small_payloads),
    )
