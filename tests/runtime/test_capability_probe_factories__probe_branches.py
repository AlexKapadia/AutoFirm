"""Direct tests of the capability probe factories: degraded branches + transport reachability.

Exercises the per-factory probe closures directly (not just through the aggregate self-test),
including the OPTIONAL degraded paths that report correct-degradation and the synthetic gateway
transport's reachability response.
"""

from __future__ import annotations

from datetime import UTC, datetime

from autofirm.runtime.egress_capability_factories import (
    _SyntheticHealthyTransport,
    build_gateway_capability,
    build_kill_switch_capability,
)
from autofirm.runtime.knowledge_capability_factories import build_memory_capability
from autofirm.runtime.platform_config import PlatformConfig

_NOW = datetime(2025, 1, 1, tzinfo=UTC)


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
