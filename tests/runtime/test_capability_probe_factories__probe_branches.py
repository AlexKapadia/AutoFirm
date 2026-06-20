"""Direct tests of the capability probe factories: degraded branches + transport reachability.

Exercises the per-factory probe closures directly (not just through the aggregate self-test),
including the OPTIONAL degraded paths that report correct-degradation and the synthetic gateway
transport's reachability response.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from autofirm.audit.candidate_b_merkle_audit_log import MerkleAuditLog
from autofirm.capabilities.capability_growth_log import CapabilityGrowthLog
from autofirm.comms.append_only_audit_sink import InMemoryMessageAuditSink
from autofirm.comms.inter_agent_message_bus import InterAgentMessageBus
from autofirm.costledger.append_only_cost_ledger import AppendOnlyCostLedger
from autofirm.frontdoor.front_desk_request_router import FrontDeskRequestRouter
from autofirm.frontdoor.role_capability_index import RoleCapabilityIndex
from autofirm.memory.agent_memory_layer import AgentMemoryLayer
from autofirm.memory.memory_record_contract import MemoryKind
from autofirm.modelgateway.kill_switch_epoch import KillSwitchEpoch
from autofirm.runtime.egress_capability_factories import (
    _SyntheticHealthyTransport,
    _SyntheticResponse,
    build_audit_capability,
    build_cost_ledger_capability,
    build_gateway_capability,
    build_kill_switch_capability,
)
from autofirm.runtime.knowledge_capability_factories import (
    build_capability_registry_capability,
    build_comms_capability,
    build_memory_capability,
    build_org_frontdoor_capability,
)
from autofirm.runtime.platform_config import PlatformConfig

_NOW = datetime(2025, 1, 1, tzinfo=UTC)
_PRESENT = PlatformConfig(present_providers=frozenset({"anthropic"}))


def test_gateway_capability__degraded_probe_reports_correct_degradation() -> None:
    """A degraded gateway probe passes by reporting correct degradation (never attempts egress)."""
    cap = build_gateway_capability(
        config=PlatformConfig(present_providers=frozenset()),
        degraded=True,
        reason="key_absent",
        instant=_NOW,
    )
    result = cap.probe()
    assert result.passed
    assert result.reason == "gateway_degraded_no_provider_key"


def test_gateway_capability__live_probe_reaches_synthetic_transport() -> None:
    """A live (non-degraded) gateway probe POSTs through the transport seam and sees a 200."""
    cap = build_gateway_capability(
        config=PlatformConfig(present_providers=frozenset({"anthropic"})),
        degraded=False,
        reason="key_present",
        instant=_NOW,
    )
    result = cap.probe()
    assert result.passed
    assert result.reason == "gateway_reachable"


def test_synthetic_transport__answers_200_with_json_body() -> None:
    """The synthetic transport returns a 200 response exposing an (empty) JSON body."""
    response = _SyntheticHealthyTransport().post_json("x://y", headers={}, body={})
    assert response.status_code == 200
    assert response.json() == {}


def test_memory_capability__degraded_when_embedding_backend_disabled() -> None:
    """With the embedding backend disabled, the memory probe reports correct degradation."""
    cap = build_memory_capability(
        config=PlatformConfig(present_providers=frozenset(), embedding_enabled=False),
        instant=_NOW,
    )
    result = cap.probe()
    assert result.passed
    assert result.reason == "memory_degraded_no_embedding_backend"
    assert cap.degraded


def test_kill_switch_capability__healthy_probe_confirms_engaged_switch_refuses() -> None:
    """The kill-switch probe confirms an engaged epoch refuses egress (security control live)."""
    result = build_kill_switch_capability(instant=_NOW).probe()
    assert result.passed
    assert result.reason == "engaged_switch_refused_egress"


# ---------------------------------------------------------------------------
# Mutation-hardening (CLAUDE.md §3.6): exercise every probe's FAILURE branch
# (via white-box monkeypatching of the verified collaborator), pin every exact
# reason/capability string, and capture the synthetic (no-PII §3.12) probe data.
# ---------------------------------------------------------------------------


def test_kill_switch_capability__reason_is_exact() -> None:
    """The kill-switch capability's audited reason is pinned exactly (kills the string mutant)."""
    assert build_kill_switch_capability(instant=_NOW).reason == "global_egress_halt_wired"


def test_kill_switch_probe__exercises_an_untripped_then_a_tripped_epoch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The probe must check BOTH an untripped (v0) and a tripped (v1) epoch (kills version mutants).

    Capturing the epoch versions the probe checks proves it exercises the permit path AND the
    refuse path with distinct epochs — a mutant altering either constructed version is caught.
    """
    seen: list[int] = []
    original = KillSwitchEpoch.require_egress_permitted

    def _spy(self: KillSwitchEpoch) -> None:
        seen.append(self.version)
        original(self)

    monkeypatch.setattr(KillSwitchEpoch, "require_egress_permitted", _spy)
    build_kill_switch_capability(instant=_NOW).probe()
    assert seen == [0, 1]  # untripped epoch v0 (permits), then tripped epoch v1 (refuses)


def test_kill_switch_probe__failure_branch_when_tripped_switch_permits(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """If a tripped switch fails to refuse, the probe reports the broken control (failure branch).

    Forcing ``require_egress_permitted`` to never raise drives the defensive fail-closed branch:
    a tripped switch that permits egress is a broken SECURITY control and must fail the probe.
    """
    monkeypatch.setattr(KillSwitchEpoch, "require_egress_permitted", lambda self: None)
    result = build_kill_switch_capability(instant=_NOW).probe()
    assert not result.passed
    assert result.reason == "engaged_switch_permitted_egress"


def test_audit_probe__appends_a_synthetic_non_pii_record(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The audit probe records ONLY synthetic, non-PII fields (kills the field mutants; §3.12)."""
    captured: dict[str, object] = {}
    original = MerkleAuditLog.append

    def _spy(self: MerkleAuditLog, record: object) -> object:
        captured["record"] = record
        return original(self, record)  # type: ignore[arg-type]

    monkeypatch.setattr(MerkleAuditLog, "append", _spy)
    build_audit_capability(instant=_NOW).probe()
    record = captured["record"]
    assert record.entity.entity_id == "synthetic-lineage-0"  # type: ignore[attr-defined]
    assert record.entity.content_hash == "0" * 64  # type: ignore[attr-defined]
    assert record.activity == "readiness.selftest"  # type: ignore[attr-defined]
    assert record.agent == "platform.selftest"  # type: ignore[attr-defined]
    assert record.tenant_id == "synthetic-tenant"  # type: ignore[attr-defined]


def test_audit_probe__success_reason_is_exact() -> None:
    """A verified inclusion proof yields the exact success reason (kills the string mutant)."""
    result = build_audit_capability(instant=_NOW).probe()
    assert result.passed
    assert result.reason == "audit_inclusion_proof_verified"


def test_audit_probe__failure_branch_when_inclusion_proof_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An unverifiable inclusion proof fails the probe fail-closed (drives the failure branch)."""
    monkeypatch.setattr(MerkleAuditLog, "verify_inclusion", lambda self, seq, root: False)
    result = build_audit_capability(instant=_NOW).probe()
    assert not result.passed
    assert result.reason == "audit_inclusion_proof_failed"


def test_audit_capability__reason_is_exact() -> None:
    """The audit capability's audited reason is pinned exactly (kills the string mutant)."""
    assert build_audit_capability(instant=_NOW).reason == "tamper_evident_merkle_log_wired"


def test_cost_ledger_probe__success_reason_and_capability_reason_are_exact() -> None:
    """A verified chain yields the exact probe + capability reasons (kills the string mutants)."""
    cap = build_cost_ledger_capability(instant=_NOW)
    assert cap.reason == "append_only_cost_ledger_wired"
    result = cap.probe()
    assert result.passed
    assert result.reason == "cost_ledger_chain_verified"


def test_cost_ledger_probe__failure_branch_when_chain_does_not_verify(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A chain that fails ``verify()`` fails the probe (drives the AND-guarded failure branch).

    Forcing ``verify()`` False must fail the probe regardless of the tip-hash equality — so a
    mutant relaxing the ``and`` to ``or`` (which would pass on the tip match alone) is killed.
    """
    monkeypatch.setattr(AppendOnlyCostLedger, "verify", lambda self: False)
    result = build_cost_ledger_capability(instant=_NOW).probe()
    assert not result.passed
    assert result.reason == "cost_ledger_chain_invalid"


def test_gateway_probe__unreachable_branch_when_transport_answers_non_200(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A non-200 transport answer fails the live gateway probe (drives the failure branch)."""
    monkeypatch.setattr(_SyntheticResponse, "status_code", property(lambda self: 503))
    cap = build_gateway_capability(
        config=_PRESENT, degraded=False, reason="key_present", instant=_NOW
    )
    result = cap.probe()
    assert not result.passed
    assert result.reason == "gateway_unreachable"


def test_gateway_probe__live_probe_targets_the_configured_gateway_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The live probe POSTs to the CONFIGURED gateway URL (kills a hard-coded-URL regression)."""
    seen: dict[str, str] = {}
    original = _SyntheticHealthyTransport.post_json

    def _spy(self: _SyntheticHealthyTransport, url: str, **kwargs: object) -> object:
        seen["url"] = url
        return original(self, url, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(_SyntheticHealthyTransport, "post_json", _spy)
    config = PlatformConfig(
        present_providers=frozenset({"anthropic"}), gateway_url="http://probe-target:9"
    )
    build_gateway_capability(
        config=config, degraded=False, reason="key_present", instant=_NOW
    ).probe()
    assert seen["url"] == "http://probe-target:9"


# ===========================================================================
# Knowledge-layer probes (memory / comms / registry / org front-door).
# Mutation-hardening (§3.6): capture the synthetic (no-PII §3.12) fixture each
# probe drives, pin every exact reason, and force every failure/condition branch.
# ===========================================================================


def test_memory_probe__stores_and_recalls_the_exact_synthetic_fixture(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The memory probe stores + recalls EXACT synthetic data (kills the fixture mutants; §3.12)."""
    remembered: dict[str, object] = {}
    recalled: dict[str, object] = {}
    orig_remember = AgentMemoryLayer.remember
    orig_recall = AgentMemoryLayer.recall

    def _spy_remember(self: AgentMemoryLayer, **kw: object) -> object:
        remembered.update(kw)
        return orig_remember(self, **kw)  # type: ignore[arg-type]

    def _spy_recall(self: AgentMemoryLayer, **kw: object) -> object:
        recalled.update(kw)
        return orig_recall(self, **kw)  # type: ignore[arg-type]

    monkeypatch.setattr(AgentMemoryLayer, "remember", _spy_remember)
    monkeypatch.setattr(AgentMemoryLayer, "recall", _spy_recall)
    build_memory_capability(config=_PRESENT, instant=_NOW).probe()
    assert remembered == {
        "written_by": "selftest",
        "owner": "selftest",
        "content": "alpha beta gamma",
        "kind": MemoryKind.SEMANTIC,
    }
    assert recalled == {
        "reader": "selftest",
        "owner": "selftest",
        "query": "alpha",
        "limit": 3,
    }


def test_memory_probe__success_reason_is_exact() -> None:
    """A successful store+recall round-trip yields the exact reason (kills the string mutant)."""
    result = build_memory_capability(config=_PRESENT, instant=_NOW).probe()
    assert result.passed
    assert result.reason == "memory_store_recall_round_trip"


def test_memory_probe__failure_branch_when_recall_returns_nothing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A stored record that does not recall fails the probe (drives the empty-result branch)."""
    monkeypatch.setattr(AgentMemoryLayer, "recall", lambda self, **kw: [])
    result = build_memory_capability(config=_PRESENT, instant=_NOW).probe()
    assert not result.passed
    assert result.reason == "memory_recall_returned_nothing"


def test_memory_capability__reason_is_exact_for_wired_and_degraded() -> None:
    """The memory capability's reason names the wired/degraded state exactly (kills the ternary)."""
    wired = build_memory_capability(config=_PRESENT, instant=_NOW)
    assert not wired.degraded
    assert wired.reason == "agent_memory_layer_wired"
    degraded = build_memory_capability(
        config=PlatformConfig(present_providers=frozenset(), embedding_enabled=False),
        instant=_NOW,
    )
    assert degraded.degraded
    assert degraded.reason == "embedding_backend_absent"


def test_comms_probe__delivers_the_exact_synthetic_envelope(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The comms probe routes an EXACT synthetic envelope (kills the envelope-field mutants)."""
    captured: dict[str, object] = {}
    orig = InterAgentMessageBus.deliver

    async def _spy(self: InterAgentMessageBus, envelope: object) -> object:
        captured["envelope"] = envelope
        return await orig(self, envelope)  # type: ignore[arg-type]

    monkeypatch.setattr(InterAgentMessageBus, "deliver", _spy)
    build_comms_capability(instant=_NOW).probe()
    envelope = captured["envelope"]
    assert envelope.sender == "selftest.sender"  # type: ignore[attr-defined]
    assert envelope.recipient == "selftest.recipient"  # type: ignore[attr-defined]
    assert envelope.conversation_id == "selftest-conversation"  # type: ignore[attr-defined]
    assert envelope.causal_seq == 0  # type: ignore[attr-defined]
    assert envelope.dedup_key == "selftest-dedup-0"  # type: ignore[attr-defined]
    assert envelope.payload == {"probe": "loopback"}  # type: ignore[attr-defined]


def test_comms_probe__success_reason_is_exact() -> None:
    """A delivered + audited loopback yields the exact reason (kills the string mutant)."""
    result = build_comms_capability(instant=_NOW).probe()
    assert result.passed
    assert result.reason == "comms_loopback_delivered_and_audited"


def test_comms_probe__failure_branch_when_delivery_is_not_audited(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A delivery that is not audited fails the probe (drives the audited==1 conjunct).

    Forcing the audit sink to report ZERO entries must fail the probe even though the message
    was delivered — so a mutant dropping the ``len(audit.entries()) == 1`` conjunct is killed.
    """
    monkeypatch.setattr(InMemoryMessageAuditSink, "entries", lambda self: [])
    result = build_comms_capability(instant=_NOW).probe()
    assert not result.passed
    assert result.reason == "comms_loopback_not_delivered"


def test_comms_capability__reason_is_exact() -> None:
    """The comms capability's audited reason is pinned exactly (kills the string mutant)."""
    assert build_comms_capability(instant=_NOW).reason == "inter_agent_message_bus_wired"


def test_registry_probe__seals_the_exact_synthetic_descriptor(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The registry probe seals an EXACT synthetic capability descriptor (kills field mutants)."""
    captured: dict[str, object] = {}
    orig = CapabilityGrowthLog.seal

    def _spy(self: CapabilityGrowthLog, **kw: object) -> object:
        captured.update(kw)
        return orig(self, **kw)  # type: ignore[arg-type]

    monkeypatch.setattr(CapabilityGrowthLog, "seal", _spy)
    build_capability_registry_capability(instant=_NOW).probe()
    assert captured["kind"] == "CAPABILITY_ADDED"
    assert captured["triggered_by"] == "role-root"
    assert captured["org_event_ref"] == 0
    assert captured["rationale"] == "founding"
    descriptor = captured["descriptor"]
    assert descriptor.capability_id == "selftest-capability"  # type: ignore[attr-defined]
    assert descriptor.name == "readiness self-test capability"  # type: ignore[attr-defined]
    assert descriptor.keywords == frozenset({"selftest"})  # type: ignore[attr-defined]
    assert descriptor.owning_role_id == "role-selftest"  # type: ignore[attr-defined]
    assert descriptor.required_clearance == "public"  # type: ignore[attr-defined]
    assert descriptor.provenance.org_event_seq == 0  # type: ignore[attr-defined]
    assert (
        descriptor.provenance.rationale == "founding self-test capability"  # type: ignore[attr-defined]
    )


def test_registry_probe__success_reason_is_exact() -> None:
    """A non-empty registry yields the exact reason (kills the string mutant)."""
    result = build_capability_registry_capability(instant=_NOW).probe()
    assert result.passed
    assert result.reason == "capability_registry_enumerated"


def test_registry_probe__failure_branch_when_registry_is_empty(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An empty registry fails the probe (drives the ``len(...) > 0`` boundary failure branch).

    Forcing ``descriptors()`` empty must fail the probe — so a mutant relaxing ``> 0`` to
    ``>= 0`` (which would pass on an empty registry) is killed.
    """
    from autofirm.capabilities.live_capability_registry import LiveCapabilityRegistry

    monkeypatch.setattr(LiveCapabilityRegistry, "descriptors", lambda self: ())
    result = build_capability_registry_capability(instant=_NOW).probe()
    assert not result.passed
    assert result.reason == "capability_registry_empty"


def test_registry_capability__reason_is_exact() -> None:
    """The registry capability's audited reason is pinned exactly (kills the string mutant)."""
    cap = build_capability_registry_capability(instant=_NOW)
    assert cap.reason == "live_capability_registry_wired"


def test_frontdoor_probe__routes_the_exact_synthetic_roles_and_request(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The front-door probe indexes EXACT synthetic roles and routes an EXACT request (§3.12)."""
    roles_seen: dict[str, object] = {}
    request_seen: dict[str, object] = {}
    orig_init = RoleCapabilityIndex.__init__
    orig_route = FrontDeskRequestRouter.route

    def _spy_init(self: RoleCapabilityIndex, capabilities: object) -> None:
        roles_seen["roles"] = capabilities
        orig_init(self, capabilities)  # type: ignore[arg-type]

    def _spy_route(self: FrontDeskRequestRouter, request: object) -> object:
        request_seen["request"] = request
        return orig_route(self, request)  # type: ignore[arg-type]

    monkeypatch.setattr(RoleCapabilityIndex, "__init__", _spy_init)
    monkeypatch.setattr(FrontDeskRequestRouter, "route", _spy_route)
    build_org_frontdoor_capability(instant=_NOW).probe()

    roles = {r.role_id: r for r in roles_seen["roles"]}  # type: ignore[attr-defined]
    sales = roles["role-sales"]
    triage = roles["role-triage"]
    assert sales.title == "Sales"
    assert sales.keywords == frozenset({"pricing", "sales"})
    assert sales.required_clearance == "public"
    assert not sales.is_triage
    assert triage.title == "Triage"
    assert triage.keywords == frozenset({"triage"})
    assert triage.required_clearance == "public"
    assert triage.is_triage

    request = request_seen["request"]
    assert request.correlation_id == "selftest-correlation"  # type: ignore[attr-defined]
    assert request.requester.requester_id == "selftest-owner"  # type: ignore[attr-defined]
    assert request.requester.display_name == "Self Test Owner"  # type: ignore[attr-defined]
    assert request.requester.clearances == frozenset({"public"})  # type: ignore[attr-defined]
    assert request.body == "a question about pricing"  # type: ignore[attr-defined]


def test_frontdoor_probe__success_reason_is_exact() -> None:
    """Routing to the capable role yields the exact reason (kills the string mutant)."""
    result = build_org_frontdoor_capability(instant=_NOW).probe()
    assert result.passed
    assert result.reason == "front_door_routed_to_capable_role"


def test_frontdoor_probe__failure_branch_when_routed_but_triaged(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A triaged routing fails the probe even if the role id matches (drives the AND conjunct).

    A decision that picks ``role-sales`` BUT is triaged must fail (the probe demands a capable,
    non-triaged route) — so a mutant relaxing the ``and not is_triaged`` to ``or`` is killed.
    """

    class _TriagedDecision:
        chosen_role_id = "role-sales"
        is_triaged = True

    monkeypatch.setattr(FrontDeskRequestRouter, "route", lambda self, request: _TriagedDecision())
    result = build_org_frontdoor_capability(instant=_NOW).probe()
    assert not result.passed
    assert result.reason == "front_door_failed_to_route"


def test_frontdoor_capability__reason_is_exact() -> None:
    """The front-door capability's audited reason is pinned exactly (kills the string mutant)."""
    assert build_org_frontdoor_capability(instant=_NOW).reason == "org_front_door_routing_wired"
