"""Synthetic, deterministic builders for the front-door test suite.

What this provides
------------------
Side-effect-free factories for a realistic multi-capability :class:`OrgState`, a built
:class:`RoleCapabilityIndex` with a triage fallback, valid :class:`HumanRequest` /
:class:`RequesterIdentity` instances, a deterministic clock + id-generator, and a fully
wired :class:`FrontDoorRequestDispatcher` with an in-memory comms bus whose handlers
record what they received. No network, no real I/O, no real PII — synthetic only
(CLAUDE.md §5.5 / §3.12).

Builders produce *valid* artifacts by default; tests construct adversarial / invalid
variants inline so the failure each test targets is explicit and local.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime

from autofirm.comms.append_only_audit_sink import InMemoryMessageAuditSink
from autofirm.comms.dynamic_agent_registry import DynamicAgentRegistry
from autofirm.comms.injectable_delivery_clock import ManualClock
from autofirm.comms.inter_agent_message_bus import InterAgentMessageBus
from autofirm.comms.message_envelope_contract import MessageEnvelope
from autofirm.frontdoor.front_desk_request_router import FrontDeskRequestRouter
from autofirm.frontdoor.front_door_provenance_trail import InMemoryFrontDoorProvenanceTrail
from autofirm.frontdoor.front_door_request_dispatcher import FrontDoorRequestDispatcher
from autofirm.frontdoor.human_request_contract import (
    HumanRequest,
    RequestChannel,
    RequesterIdentity,
)
from autofirm.frontdoor.request_intent_classifier import KeywordIntentClassifier
from autofirm.frontdoor.role_capability_index import (
    PUBLIC_CLEARANCE,
    RoleCapabilityIndex,
)
from autofirm.org.org_identifiers import (
    ArtifactId,
    FrozenClock,
    RoleId,
    SequentialIdGenerator,
)
from autofirm.org.org_lifecycle_engine import DynamicOrg
from autofirm.org.org_state import OrgState
from autofirm.org.role_charter_contract import ROOT_AUTHOR, RoleCharter

EPOCH = datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC)

# A small, realistic org: a CEO root (the triage fallback), plus three capable roles with
# DISTINCT, non-overlapping capability vocabularies so a test can assert a request lands
# on exactly the intended role.
TRIAGE_ROLE = "ceo"
BILLING_ROLE = "billing-lead"
SUPPORT_ROLE = "support-lead"
SECURITY_ROLE = "security-lead"


def _charter(
    role_id: str,
    responsibilities: tuple[str, ...],
    *,
    manager_id: str | None,
    authored_by: str,
    artifacts: frozenset[str] = frozenset(),
) -> RoleCharter:
    """Build one valid charter with the given capability responsibilities."""
    return RoleCharter(
        role_id=RoleId(role_id),
        title=role_id.replace("-", " ").title(),
        responsibilities=responsibilities,
        ownership_scope=f"{role_id}-scope",
        success_signal=f"{role_id}-kpi",
        owned_artifacts=frozenset(ArtifactId(a) for a in artifacts),
        manager_id=RoleId(manager_id) if manager_id is not None else None,
        authored_by=RoleId(authored_by),
    )


def realistic_org_state() -> OrgState:
    """A founded org with a triage root + three capable, distinct-vocabulary roles."""
    org = DynamicOrg.found(
        _charter(
            TRIAGE_ROLE,
            ("triage anything and escalate", "run the company"),
            manager_id=None,
            authored_by=str(ROOT_AUTHOR),
        ),
        FrozenClock(EPOCH, step_seconds=1.0),
        SequentialIdGenerator(),
    )
    org = org.hire(
        _charter(
            BILLING_ROLE,
            ("handle invoice billing refund payment disputes",),
            manager_id=TRIAGE_ROLE,
            authored_by=TRIAGE_ROLE,
        )
    )
    org = org.hire(
        _charter(
            SUPPORT_ROLE,
            ("resolve onboarding tutorial guidance questions",),
            manager_id=TRIAGE_ROLE,
            authored_by=TRIAGE_ROLE,
        )
    )
    org = org.hire(
        _charter(
            SECURITY_ROLE,
            ("investigate breach vulnerability incident reports",),
            manager_id=TRIAGE_ROLE,
            authored_by=TRIAGE_ROLE,
        )
    )
    return org.state


def default_clearances() -> Mapping[RoleId, str]:
    """A clearance map: billing+support are public; security needs an explicit grant."""
    return {
        RoleId(TRIAGE_ROLE): PUBLIC_CLEARANCE,
        RoleId(BILLING_ROLE): PUBLIC_CLEARANCE,
        RoleId(SUPPORT_ROLE): PUBLIC_CLEARANCE,
        RoleId(SECURITY_ROLE): "security-cleared",
    }


def capability_index(
    state: OrgState | None = None,
    clearances: Mapping[RoleId, str] | None = None,
) -> RoleCapabilityIndex:
    """Build the capability index from the realistic org (CEO == triage fallback)."""
    return RoleCapabilityIndex.from_org_state(
        state if state is not None else realistic_org_state(),
        triage_role_id=RoleId(TRIAGE_ROLE),
        required_clearances=clearances if clearances is not None else default_clearances(),
    )


def requester(
    requester_id: str = "owner-acme",
    clearances: frozenset[str] = frozenset(),
) -> RequesterIdentity:
    """Build a valid requester identity (no clearances == unprivileged public)."""
    return RequesterIdentity(
        requester_id=requester_id,
        display_name=requester_id.replace("-", " ").title(),
        clearances=clearances,
    )


def human_request(
    body: str,
    *,
    correlation_id: str = "corr-1",
    who: RequesterIdentity | None = None,
    channel: RequestChannel = RequestChannel.API,
) -> HumanRequest:
    """Build a valid human request with a fixed received-at for determinism."""
    return HumanRequest(
        correlation_id=correlation_id,
        requester=who if who is not None else requester(),
        channel=channel,
        body=body,
        received_at=EPOCH,
    )


def router(index: RoleCapabilityIndex | None = None) -> FrontDeskRequestRouter:
    """Build a router over the capability index with the deterministic keyword classifier."""
    return FrontDeskRequestRouter(
        capability_index=index if index is not None else capability_index(),
        classifier=KeywordIntentClassifier(),
        clock=FrozenClock(EPOCH, step_seconds=1.0),
    )


class RecordingHandlers:
    """A bus + registry where every role handler records the envelopes it received.

    Lets a dispatcher test assert WHICH role actually received the delivered request
    (the routing target reached the right handler over the real bus).
    """

    def __init__(self, role_ids: tuple[str, ...]) -> None:
        """Register a recording handler for each role id on a fresh in-memory bus."""
        self.received: dict[str, list[MessageEnvelope]] = {rid: [] for rid in role_ids}
        registry = DynamicAgentRegistry()
        for rid in role_ids:
            registry.register_agent(rid, self._make_handler(rid))
        self.audit = InMemoryMessageAuditSink()
        self.bus = InterAgentMessageBus(
            registry=registry, audit_sink=self.audit, clock=ManualClock()
        )

    def _make_handler(self, role_id: str):  # type: ignore[no-untyped-def]
        async def handler(envelope: MessageEnvelope) -> None:
            self.received[role_id].append(envelope)

        return handler


def dispatcher_with_recording_handlers(
    *,
    register_roles: tuple[str, ...] = (
        TRIAGE_ROLE,
        BILLING_ROLE,
        SUPPORT_ROLE,
        SECURITY_ROLE,
    ),
    index: RoleCapabilityIndex | None = None,
) -> tuple[FrontDoorRequestDispatcher, RecordingHandlers, InMemoryFrontDoorProvenanceTrail]:
    """A fully wired dispatcher + the recording handlers + the provenance trail.

    ``register_roles`` controls which roles have a live bus handler — omit a role to
    simulate a routing-correct-but-undeliverable target (the bus dead-letters it).
    """
    handlers = RecordingHandlers(register_roles)
    trail = InMemoryFrontDoorProvenanceTrail()
    dispatcher = FrontDoorRequestDispatcher(
        router=router(index),
        message_bus=handlers.bus,
        provenance_trail=trail,
        clock=FrozenClock(EPOCH, step_seconds=1.0),
        id_generator=SequentialIdGenerator(),
    )
    return dispatcher, handlers, trail
