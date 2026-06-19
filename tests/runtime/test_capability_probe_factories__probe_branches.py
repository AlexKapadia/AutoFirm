"""Direct tests of the capability probe factories: degraded branches + transport reachability.

Exercises the per-factory probe closures directly (not just through the aggregate self-test),
including the OPTIONAL degraded paths that report correct-degradation and the synthetic gateway
transport's reachability response.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from autofirm.audit.candidate_b_merkle_audit_log import MerkleAuditLog
from autofirm.costledger.append_only_cost_ledger import AppendOnlyCostLedger
from autofirm.modelgateway.kill_switch_epoch import KillSwitchEpoch
from autofirm.runtime.egress_capability_factories import (
    _SyntheticHealthyTransport,
    _SyntheticResponse,
    build_audit_capability,
    build_cost_ledger_capability,
    build_gateway_capability,
    build_kill_switch_capability,
)
from autofirm.runtime.knowledge_capability_factories import build_memory_capability
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
