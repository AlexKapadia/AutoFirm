"""Teeth tests for the composition root: every subsystem wired, degraded-binding, mis-wire fails.

Proves the root makes the system COHESIVE (every advertised capability is present + probed)
and that a deliberately mis-wired graph FAILS — the build-time cohesion validation is not a
tautology. Also asserts degraded-binding per capability across the missing-dependency matrix
never produces a whole-platform block.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from autofirm.bootstrap.bootstrap_step_contract import Criticality
from autofirm.runtime.platform_composition_root import (
    EXPECTED_CAPABILITY_IDS,
    _validate_cohesion,
    build_platform,
)
from autofirm.runtime.platform_config import PlatformConfig
from autofirm.runtime.platform_runtime import Platform, ProbeResult, WiredCapability

_NOW = datetime(2025, 1, 1, tzinfo=UTC)


def _healthy_config() -> PlatformConfig:
    return PlatformConfig(present_providers=frozenset({"anthropic"}), embedding_enabled=True)


def test_build_platform__wires_every_expected_capability() -> None:
    """The cohesion property: the built platform advertises EVERY expected subsystem."""
    platform = build_platform(_healthy_config(), now=_NOW)
    assert platform.capability_ids() == EXPECTED_CAPABILITY_IDS
    # Each capability carries a probe closure (the cohesion ledger is fully wired, not stubbed).
    assert all(callable(cap.probe) for cap in platform.capabilities)


def test_build_platform__every_probe_actually_passes_on_a_healthy_config() -> None:
    """A healthy config wires subsystems whose probes all pass (end-to-end serving proof)."""
    platform = build_platform(_healthy_config(), now=_NOW)
    assert all(cap.probe().passed for cap in platform.capabilities)


def test_build_platform__declares_supervised_loops_and_a_config_fingerprint() -> None:
    """The platform declares its loop inventory and a deterministic, secret-free fingerprint."""
    platform = build_platform(_healthy_config(), now=_NOW)
    assert len(platform.loops) >= 1
    assert "providers=anthropic" in platform.config_fingerprint


def test_build_platform__fingerprint_is_deterministic_and_excludes_secrets() -> None:
    """The same config yields an identical fingerprint; no secret value appears in it."""
    fp1 = build_platform(_healthy_config(), now=_NOW).config_fingerprint
    fp2 = build_platform(_healthy_config(), now=_NOW).config_fingerprint
    assert fp1 == fp2
    assert "sk-" not in fp1  # presence flags only — never a key value


def test_build_platform__missing_provider_key_binds_gateway_degraded_platform_still_up() -> None:
    """No provider key => the gateway binds DEGRADED (bulkhead) but the platform STILL builds."""
    platform = build_platform(PlatformConfig(present_providers=frozenset()), now=_NOW)
    gateway = platform.capability("gateway")
    assert gateway.degraded  # degraded, not absent
    assert gateway.criticality is Criticality.OPTIONAL
    # The whole platform still came up with all 8 capabilities (never a whole-platform block).
    assert platform.capability_ids() == EXPECTED_CAPABILITY_IDS


def test_build_platform__missing_embedding_backend_degrades_only_memory() -> None:
    """Disabling the embedding backend degrades ONLY memory — every other capability is fine."""
    platform = build_platform(
        PlatformConfig(present_providers=frozenset({"anthropic"}), embedding_enabled=False),
        now=_NOW,
    )
    assert platform.capability("memory").degraded
    non_memory = [c for c in platform.capabilities if c.capability_id != "memory"]
    assert not any(c.degraded for c in non_memory)  # bulkhead: the rest are unaffected


def test_validate_cohesion__a_mis_wired_graph_with_a_dropped_capability_fails() -> None:
    """A platform missing a wired capability FAILS the cohesion validation (teeth, not tautology).

    This is acceptance item §5.5: a deliberately mis-wired graph (here, the cost-ledger
    subsystem dropped from the wiring) must be REJECTED — proving the validation has teeth.
    """
    full = build_platform(_healthy_config(), now=_NOW)
    crippled = Platform(
        capabilities=tuple(c for c in full.capabilities if c.capability_id != "cost_ledger"),
        loops=full.loops,
    )
    with pytest.raises(ValueError, match="missing wired capabilities"):
        _validate_cohesion(crippled)


def test_validate_cohesion__a_fully_wired_graph_passes() -> None:
    """The positive control: a fully-wired graph passes the cohesion validation cleanly."""
    _validate_cohesion(build_platform(_healthy_config(), now=_NOW))  # must not raise


def test_capability__unknown_id_fails_loud() -> None:
    """Asking for an unadvertised capability fails loud (never a silent default)."""
    platform = build_platform(_healthy_config(), now=_NOW)
    with pytest.raises(KeyError, match="no wired capability"):
        platform.capability("does-not-exist")


def test_build_platform__degraded_gateway_capability_advertises_a_reason() -> None:
    """A degraded capability is explicit: it carries a non-empty reason (never silently off)."""
    platform = build_platform(PlatformConfig(present_providers=frozenset()), now=_NOW)
    assert platform.capability("gateway").reason


def test_wired_capability__is_a_plain_value_carrying_its_probe() -> None:
    """Sanity: WiredCapability stores its probe result faithfully (probe closure round-trips)."""
    cap = WiredCapability(
        capability_id="x",
        criticality=Criticality.REQUIRED,
        degraded=False,
        reason="r",
        probe=lambda: ProbeResult(passed=True, reason="ok"),
    )
    assert cap.probe().passed


def test_build_platform__fingerprint_is_the_exact_secret_free_string() -> None:
    """The config fingerprint is pinned exactly (kills fingerprint-format mutants).

    Same-live-state assertions rely on this string being a deterministic function of the
    presence flags + non-secret paths, so its exact shape is asserted.
    """
    platform = build_platform(
        PlatformConfig(
            present_providers=frozenset({"anthropic"}),
            gateway_url="http://gw:1",
            embedding_enabled=True,
        ),
        now=_NOW,
    )
    assert platform.config_fingerprint == "providers=anthropic|gateway=http://gw:1|emb=True"


def test_build_platform__fingerprint_joins_multiple_providers_with_a_comma() -> None:
    """Multiple providers are comma-joined in sorted order (kills separator/sort mutants)."""
    platform = build_platform(
        PlatformConfig(
            present_providers=frozenset({"openai", "anthropic"}),
            gateway_url="http://gw:1",
            embedding_enabled=True,
        ),
        now=_NOW,
    )
    # Sorted + comma-joined: 'anthropic,openai' (not 'openai,anthropic', not a different sep).
    assert platform.config_fingerprint == "providers=anthropic,openai|gateway=http://gw:1|emb=True"


def test_build_platform__supervised_loop_names_are_exact() -> None:
    """The supervised loop inventory carries its exact, self-documenting names (kills mutants)."""
    platform = build_platform(_healthy_config(), now=_NOW)
    names = {loop.name for loop in platform.loops}
    assert names == {"capability.reprobe", "comms.drain"}


def test_build_platform__defaults_now_when_unset_still_wires_full_graph() -> None:
    """`now=None` resolves a wall-clock instant at the edge and still wires the full graph.

    Exercises the now-injection default branch (kills the ``now is not None`` mutant) without
    asserting on the (non-deterministic) wall-clock value itself.
    """
    platform = build_platform(_healthy_config())  # now omitted -> defaults at the edge
    assert platform.capability_ids() == EXPECTED_CAPABILITY_IDS


def test_validate_cohesion__error_names_the_missing_capability_ids() -> None:
    """The cohesion failure message names exactly the missing capability ids (kills msg mutants)."""
    full = build_platform(_healthy_config(), now=_NOW)
    crippled = Platform(
        capabilities=tuple(c for c in full.capabilities if c.capability_id != "audit"),
        loops=full.loops,
    )
    with pytest.raises(ValueError) as excinfo:
        _validate_cohesion(crippled)
    # Assert the EXACT message (anchored) so a mutant wrapping the string in sentinels is killed.
    assert str(excinfo.value) == "composition root is missing wired capabilities: ['audit']"


def test_build_platform__gateway_degraded_reason_names_the_provider_dependency() -> None:
    """The gateway degraded reason names the provider dependency AND the policy outcome exactly.

    Pins the audit-linkage format ``<dependency>:<policy-reason>`` (§3.11) so a mutant that
    drops/wraps the ``provider:anthropic`` dependency label or the ``:`` separator is killed.
    """
    platform = build_platform(PlatformConfig(present_providers=frozenset()), now=_NOW)
    assert (
        platform.capability("gateway").reason
        == "provider:anthropic:optional_dependency_absent_capability_degraded"
    )


def test_build_platform__gateway_present_reason_names_the_provider_dependency() -> None:
    """When the provider key is present the reason still names the dependency (present branch)."""
    platform = build_platform(_healthy_config(), now=_NOW)
    assert platform.capability("gateway").reason == "provider:anthropic:dependency_present"


def test_build_platform__defaults_now_propagates_a_real_instant_to_every_probe() -> None:
    """`now=None` must resolve a REAL instant so every probe still passes (kills the ternary flip).

    A mutant flipping ``now is not None`` to ``now is None`` would feed ``instant=None`` into the
    factories on the default-now path, making the audit probe raise on a ``None`` timestamp. So
    we assert every probe passes when ``now`` is omitted.
    """
    platform = build_platform(_healthy_config())  # now omitted -> resolved at the edge
    assert all(cap.probe().passed for cap in platform.capabilities)
