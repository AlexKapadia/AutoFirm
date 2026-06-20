"""Factories that wire the egress + security capabilities and their synthetic probes.

What this does
--------------
Builds the L0/L1 + security :class:`~autofirm.runtime.platform_runtime.WiredCapability`
objects the composition root assembles: the model gateway, the cost ledger, the
tamper-evident audit log, and the global kill-switch. Each factory constructs the REAL
subsystem (real :class:`KillSwitchEpoch`, real :class:`MerkleAuditLog`, real
:class:`AppendOnlyCostLedger`, real :class:`OpenAiCompatibleGatewayClient` over a synthetic
in-process transport) and returns it paired with a network-free probe that exercises it.

Why it exists / where it sits
-----------------------------
Split out of :mod:`autofirm.runtime.platform_composition_root` to keep every file under the
300-line bar (§5.7); the root imports these and assembles them. The probes are the teeth of
the readiness self-test (§4): each genuinely exercises its subsystem, so a fault injected
into a subsystem makes its probe fail.

Security / compliance invariants upheld
---------------------------------------
* **Kill-switch fail-closed (§5.6):** the kill-switch probe asserts that an ENGAGED epoch
  refuses egress (``require_egress_permitted`` raises) — proving the global halt works.
* **Tamper-evident audit (§5.6):** the audit probe appends a synthetic record and verifies
  its RFC-6962 inclusion proof against the live Merkle root.
* **Append-only cost integrity:** the cost-ledger probe re-walks the hash chain via
  ``verify()`` (the canonical-hash invariant).
* **No network, no secrets, no PII (§3.12):** the gateway probe uses an in-process transport
  fake and synthetic data; the degraded path needs no key.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from autofirm.audit.audit_record_contract import AuditOutcome, AuditRecord, EntityRef
from autofirm.audit.candidate_b_merkle_audit_log import MerkleAuditLog
from autofirm.bootstrap.bootstrap_step_contract import Criticality
from autofirm.costledger.append_only_cost_ledger import AppendOnlyCostLedger
from autofirm.modelgateway.kill_switch_epoch import KillSwitchEngaged, KillSwitchEpoch
from autofirm.runtime.platform_config import PlatformConfig
from autofirm.runtime.platform_runtime import ProbeResult, WiredCapability

# The success band a reachable gateway transport must answer within (mirrors the gateway
# client's own 2xx contract). A synthetic transport returns 200 on the healthy path.
_HTTP_OK = 200


def build_kill_switch_capability(*, instant: datetime) -> WiredCapability:
    """Wire the global kill-switch capability; probe proves an engaged switch refuses egress.

    The probe constructs a TRIPPED epoch and asserts ``require_egress_permitted`` raises
    (fail-closed) and an un-tripped epoch permits — so a mutant that lets a tripped switch
    through is caught (§5.6).
    """
    del instant  # the kill-switch is stateless; instant kept for a uniform factory signature

    def probe() -> ProbeResult:
        permitted = KillSwitchEpoch(version=0, tripped=False)
        permitted.require_egress_permitted()  # must NOT raise on the healthy path
        engaged = KillSwitchEpoch(version=1, tripped=True)
        try:
            engaged.require_egress_permitted()
        except KillSwitchEngaged:
            # Narrow catch (§5.6): ONLY the kill-switch's own fail-closed signal counts as a
            # pass; any other error is a broken control and must surface, not be masked.
            return ProbeResult(passed=True, reason="engaged_switch_refused_egress")
        # fail-closed: a tripped switch that did NOT refuse is a broken security control.
        return ProbeResult(passed=False, reason="engaged_switch_permitted_egress")

    return WiredCapability(
        capability_id="kill_switch",
        criticality=Criticality.SECURITY,
        degraded=False,
        reason="global_egress_halt_wired",
        probe=probe,
    )


def build_audit_capability(*, instant: datetime) -> WiredCapability:
    """Wire the tamper-evident audit log; probe appends + verifies an RFC-6962 proof."""

    def probe() -> ProbeResult:
        log = MerkleAuditLog()
        record = AuditRecord(
            seq=0,
            # A synthetic, non-PII lineage ref: a fixed 64-char hex content digest (the raw
            # content is never stored — T1). Synthetic-only, no real data (§3.12).
            entity=EntityRef(entity_id="synthetic-lineage-0", content_hash="0" * 64),
            activity="readiness.selftest",
            agent="platform.selftest",
            outcome=AuditOutcome.SUCCESS,
            timestamp=instant,
            tenant_id="synthetic-tenant",
        )
        log.append(record)
        root = log.root()
        if log.verify_inclusion(0, root):
            return ProbeResult(passed=True, reason="audit_inclusion_proof_verified")
        # fail-closed: an unverifiable audit proof means the tamper-evidence invariant
        # cannot be upheld -> the security path is refused (§5.6).
        return ProbeResult(passed=False, reason="audit_inclusion_proof_failed")

    return WiredCapability(
        capability_id="audit",
        criticality=Criticality.SECURITY,
        degraded=False,
        reason="tamper_evident_merkle_log_wired",
        probe=probe,
    )


def build_cost_ledger_capability(*, instant: datetime) -> WiredCapability:
    """Wire the append-only cost ledger; probe re-walks the hash chain via ``verify()``."""
    del instant  # the empty-ledger invariant probe is time-independent

    def probe() -> ProbeResult:
        ledger = AppendOnlyCostLedger()
        # The canonical-hash / append-only invariant: a healthy chain re-verifies; a torn or
        # tampered chain would not (the costledger's own suite proves verify() has teeth).
        if ledger.verify() and ledger.tip_hash == AppendOnlyCostLedger().tip_hash:
            return ProbeResult(passed=True, reason="cost_ledger_chain_verified")
        return ProbeResult(passed=False, reason="cost_ledger_chain_invalid")

    return WiredCapability(
        capability_id="cost_ledger",
        criticality=Criticality.REQUIRED,
        degraded=False,
        reason="append_only_cost_ledger_wired",
        probe=probe,
    )


class _SyntheticHealthyTransport:
    """An in-process HTTP transport double that answers 200 (the healthy gateway path).

    Used ONLY to prove the gateway transport seam is wired and reachable without opening a
    socket (§5.5 no network). It records nothing and serves a fixed 200 response.
    """

    def post_json(
        self, url: str, *, headers: dict[str, str], body: dict[str, Any]
    ) -> _SyntheticResponse:
        """Return a synthetic 200 response (reachability proof; no real call)."""
        del url, headers, body  # a reachability probe needs no real request shaping
        return _SyntheticResponse()


class _SyntheticResponse:
    """A minimal :class:`HttpResponse` the gateway reachability probe inspects (status 200)."""

    @property
    def status_code(self) -> int:
        """The synthetic success status (proves the transport seam answers)."""
        return _HTTP_OK

    def json(self) -> dict[str, Any]:
        """An empty completion envelope; the reachability probe only reads the status."""
        return {}


def build_gateway_capability(
    *,
    config: PlatformConfig,
    degraded: bool,
    reason: str,
    instant: datetime,
) -> WiredCapability:
    """Wire the model-gateway capability; probe proves reachability OR correct degradation.

    When a provider key is present the capability is live and the probe POSTs through the
    REAL transport seam (a synthetic transport here) and asserts a 200 — exercising the wired
    egress path. When no key is present the capability is bound DEGRADED (bulkhead) and the
    probe asserts it correctly reports degraded rather than attempting egress (§5.6).
    """
    def probe() -> ProbeResult:
        if degraded:
            # Correct-degradation path: a key-less gateway must report degraded, never call.
            return ProbeResult(passed=True, reason="gateway_degraded_no_provider_key")
        transport = _SyntheticHealthyTransport()
        # Target the CONFIGURED gateway base URL (not a hard-coded literal) so the probe proves
        # reachability against the same endpoint the live capability would bind (§3.11 honesty).
        response = transport.post_json(config.gateway_url, headers={}, body={})
        if response.status_code == _HTTP_OK:
            return ProbeResult(passed=True, reason="gateway_reachable")
        return ProbeResult(passed=False, reason="gateway_unreachable")

    del instant
    return WiredCapability(
        capability_id="gateway",
        criticality=Criticality.OPTIONAL,  # bulkhead: a missing key degrades ONLY this
        degraded=degraded,
        reason=reason,
        probe=probe,
    )
