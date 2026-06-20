"""Factories that wire the knowledge, comms, registry, and org/front-door capabilities.

What this does
--------------
Builds the L2-L5 :class:`~autofirm.runtime.platform_runtime.WiredCapability` objects: the
agent memory layer, the inter-agent comms bus (loopback), the live capability registry, and
the org + human front-door routing path. Each factory constructs the REAL subsystem with its
real (deterministic) collaborators and pairs it with a synthetic, network-free probe that
proves it serves end-to-end.

Why it exists / where it sits
-----------------------------
Split out of :mod:`autofirm.runtime.platform_composition_root` to honour the 300-line bar
(§5.7); the root imports and assembles these. The probes are the teeth of the readiness
self-test (§4) — each exercises the wired subsystem with a synthetic round-trip.

Security / compliance invariants upheld
---------------------------------------
* **Loopback is real (comms):** the comms probe routes a synthetic envelope through the REAL
  bus, asserts a handler fired and the message was audited — not merely that a bus object
  exists.
* **Memory store+recall round-trip:** the memory probe stores then recalls a synthetic
  record and asserts it ranks back, proving the embed+retrieve path.
* **Registry is the cohesion ledger:** the registry probe builds a real registry from a
  growth log and asserts it enumerates a live capability (count > 0).
* **Least-privilege routing:** the org/front-door probe routes a synthetic, public-clearance
  request to a real capable role via the real router (clearance gate active).
* **No network, no PII (§3.12):** every collaborator is the in-package deterministic fake.
"""

from __future__ import annotations

from datetime import datetime
from typing import cast

import anyio

from autofirm.bootstrap.bootstrap_step_contract import Criticality
from autofirm.capabilities.capability_descriptor import (
    CapabilityDescriptor,
    CapabilityId,
    CapabilityProvenance,
)
from autofirm.capabilities.capability_growth_log import CapabilityGrowthLog
from autofirm.capabilities.live_capability_registry import LiveCapabilityRegistry
from autofirm.comms.append_only_audit_sink import InMemoryMessageAuditSink
from autofirm.comms.dynamic_agent_registry import DynamicAgentRegistry
from autofirm.comms.injectable_delivery_clock import ManualClock
from autofirm.comms.inter_agent_message_bus import InterAgentMessageBus
from autofirm.comms.message_envelope_contract import MessageEnvelope, Performative
from autofirm.frontdoor.front_desk_request_router import FrontDeskRequestRouter
from autofirm.frontdoor.human_request_contract import (
    HumanRequest,
    RequestChannel,
    RequesterIdentity,
)
from autofirm.frontdoor.request_intent_classifier import KeywordIntentClassifier
from autofirm.frontdoor.role_capability_index import RoleCapability, RoleCapabilityIndex
from autofirm.memory.agent_memory_layer import AgentMemoryLayer
from autofirm.memory.memory_identifiers import FrozenMemoryClock, SequentialMemoryIdGenerator
from autofirm.memory.memory_record_contract import MemoryKind
from autofirm.memory.semantic_embedding_backend import (
    DeterministicHashingEmbedder,
    EmbeddingBackend,
)
from autofirm.org.org_identifiers import FrozenClock, RoleId
from autofirm.runtime.platform_config import PlatformConfig
from autofirm.runtime.platform_runtime import ProbeResult, WiredCapability


def build_memory_capability(*, config: PlatformConfig, instant: datetime) -> WiredCapability:
    """Wire the agent memory layer; probe stores then recalls a synthetic record.

    When ``embedding_enabled`` is False the capability is OPTIONAL-degraded (the backend is
    absent), and the probe reports degraded rather than attempting recall (bulkhead §5.6).
    """
    degraded = not config.embedding_enabled

    def probe() -> ProbeResult:
        if degraded:
            return ProbeResult(passed=True, reason="memory_degraded_no_embedding_backend")
        # The deterministic in-package embedder exposes ``dimension`` as a property while the
        # EmbeddingBackend protocol declares it as a zero-arg method; the two are interchangeable
        # at runtime (a property read == a method call here), so we cast to the protocol to wire
        # the real subsystem without relaxing --strict typing elsewhere.
        embedder = cast(EmbeddingBackend, DeterministicHashingEmbedder())
        memory = AgentMemoryLayer(
            clock=FrozenMemoryClock(instant),
            id_generator=SequentialMemoryIdGenerator(),
            embedder=embedder,
        )
        memory.remember(
            written_by="selftest",
            owner="selftest",
            content="alpha beta gamma",
            kind=MemoryKind.SEMANTIC,
        )
        results = memory.recall(reader="selftest", owner="selftest", query="alpha", limit=3)
        if results:
            return ProbeResult(passed=True, reason="memory_store_recall_round_trip")
        # fail (degrade-graded): a stored record that does not recall is a broken retrieval.
        return ProbeResult(passed=False, reason="memory_recall_returned_nothing")

    return WiredCapability(
        capability_id="memory",
        criticality=Criticality.OPTIONAL,  # bulkhead: a missing backend degrades ONLY memory
        degraded=degraded,
        reason="agent_memory_layer_wired" if not degraded else "embedding_backend_absent",
        probe=probe,
    )


def build_comms_capability(*, instant: datetime) -> WiredCapability:
    """Wire the inter-agent comms bus; probe routes a synthetic envelope through it (loopback)."""

    def probe() -> ProbeResult:
        delivered: list[MessageEnvelope] = []

        async def _handler(envelope: MessageEnvelope) -> None:
            delivered.append(envelope)

        registry = DynamicAgentRegistry()
        registry.register_agent("selftest.recipient", _handler)
        audit = InMemoryMessageAuditSink()
        bus = InterAgentMessageBus(registry=registry, audit_sink=audit, clock=ManualClock())
        envelope = MessageEnvelope(
            performative=Performative.INFORM,
            sender="selftest.sender",
            recipient="selftest.recipient",
            conversation_id="selftest-conversation",
            causal_seq=0,
            dedup_key="selftest-dedup-0",
            payload={"probe": "loopback"},
            timestamp=instant,
        )
        report = anyio.run(bus.deliver, envelope)
        # Teeth: the message must have been DELIVERED, the handler must have fired, and the
        # delivery must have been audited — a bus that drops or fails to audit fails here.
        if (
            report.recipients_notified == 1
            and len(delivered) == 1
            and len(audit.entries()) == 1
        ):
            return ProbeResult(passed=True, reason="comms_loopback_delivered_and_audited")
        return ProbeResult(passed=False, reason="comms_loopback_not_delivered")

    return WiredCapability(
        capability_id="comms",
        criticality=Criticality.REQUIRED,
        degraded=False,
        reason="inter_agent_message_bus_wired",
        probe=probe,
    )


def build_capability_registry_capability(*, instant: datetime) -> WiredCapability:
    """Wire the live capability registry; probe builds it from a growth log and enumerates it."""

    def probe() -> ProbeResult:
        descriptor = CapabilityDescriptor(
            capability_id=CapabilityId("selftest-capability"),
            name="readiness self-test capability",
            keywords=frozenset({"selftest"}),
            owning_role_id=RoleId("role-selftest"),
            required_clearance="public",
            provenance=CapabilityProvenance(
                kind="hire", org_event_seq=0, rationale="founding self-test capability"
            ),
            maturity="active",
        )
        log = CapabilityGrowthLog()
        event = log.seal(
            kind="CAPABILITY_ADDED",
            descriptor=descriptor,
            triggered_by=RoleId("role-root"),
            org_event_ref=0,
            rationale="founding",
            occurred_at=instant,
        )
        registry = LiveCapabilityRegistry.from_growth_log(log.append(event))
        # The registry is the cohesion ledger: it must enumerate the live capability.
        if len(registry.descriptors()) > 0:
            return ProbeResult(passed=True, reason="capability_registry_enumerated")
        return ProbeResult(passed=False, reason="capability_registry_empty")

    return WiredCapability(
        capability_id="capability_registry",
        criticality=Criticality.REQUIRED,
        degraded=False,
        reason="live_capability_registry_wired",
        probe=probe,
    )


def build_org_frontdoor_capability(*, instant: datetime) -> WiredCapability:
    """Wire the org + human front door; probe routes a synthetic request to a real role.

    Exercises the REAL router, capability index, and intent classifier: a public-clearance
    request about "pricing" must route to the capable sales role (not triage), proving the
    end-to-end human->role path with the clearance gate active (§5.6).
    """

    def probe() -> ProbeResult:
        index = RoleCapabilityIndex(
            (
                RoleCapability(
                    role_id=RoleId("role-sales"),
                    title="Sales",
                    keywords=frozenset({"pricing", "sales"}),
                    required_clearance="public",
                    is_triage=False,
                ),
                RoleCapability(
                    role_id=RoleId("role-triage"),
                    title="Triage",
                    keywords=frozenset({"triage"}),
                    required_clearance="public",
                    is_triage=True,
                ),
            )
        )
        router = FrontDeskRequestRouter(
            capability_index=index,
            classifier=KeywordIntentClassifier(),
            clock=FrozenClock(instant),
        )
        request = HumanRequest(
            correlation_id="selftest-correlation",
            requester=RequesterIdentity(
                requester_id="selftest-owner",
                display_name="Self Test Owner",
                clearances=frozenset({"public"}),
            ),
            channel=RequestChannel.API,
            body="a question about pricing",
            received_at=instant,
        )
        decision = router.route(request)
        # Teeth: the request must route to the CAPABLE role, not fall back to triage.
        if decision.chosen_role_id == "role-sales" and not decision.is_triaged:
            return ProbeResult(passed=True, reason="front_door_routed_to_capable_role")
        return ProbeResult(passed=False, reason="front_door_failed_to_route")

    return WiredCapability(
        capability_id="org_frontdoor",
        criticality=Criticality.REQUIRED,
        degraded=False,
        reason="org_front_door_routing_wired",
        probe=probe,
    )
