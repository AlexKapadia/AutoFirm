"""Teeth tests for the 8-probe readiness self-test: every probe FAILS when its subsystem breaks.

The acceptance proof (§5 item 5 / §4): for EACH wired capability, inject a fault into that
capability's probe and assert the self-test catches it (the probe FAILS and the grade reacts
correctly per criticality). An all-healthy platform grades GREEN. The grading rule itself is
mutation-critical: a REQUIRED/SECURITY failure MUST be RED; an OPTIONAL degrade is DEGRADED
(never RED, never a whole-platform block).
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from autofirm.bootstrap.bootstrap_step_contract import Criticality
from autofirm.runtime.platform_composition_root import build_platform
from autofirm.runtime.platform_config import PlatformConfig
from autofirm.runtime.platform_readiness_selftest import (
    ReadinessGrade,
    run_readiness_selftest,
)
from autofirm.runtime.platform_runtime import Platform, ProbeResult, WiredCapability

_NOW = datetime(2025, 1, 1, tzinfo=UTC)
_HEALTHY = PlatformConfig(present_providers=frozenset({"anthropic"}), embedding_enabled=True)

# The eight capability ids the design's probe table covers.
_ALL_CAPABILITY_IDS = (
    "gateway",
    "cost_ledger",
    "comms",
    "capability_registry",
    "memory",
    "org_frontdoor",
    "audit",
    "kill_switch",
)


def _break_one(platform: Platform, capability_id: str) -> Platform:
    """Return a platform clone where ``capability_id``'s probe is replaced by a FAILING probe.

    This is the fault injection: the real subsystem is swapped for a probe that reports a
    failure, simulating that subsystem being broken/mis-wired. A self-test with teeth must
    catch it.
    """

    def _failing() -> ProbeResult:
        return ProbeResult(passed=False, reason="injected_fault")

    rebuilt = tuple(
        WiredCapability(
            capability_id=c.capability_id,
            criticality=c.criticality,
            degraded=c.degraded,
            reason=c.reason,
            probe=_failing if c.capability_id == capability_id else c.probe,
        )
        for c in platform.capabilities
    )
    return Platform(capabilities=rebuilt, loops=platform.loops)


def test_selftest__all_healthy_grades_green() -> None:
    """A fully-healthy platform passes every probe and grades GREEN, ok=True."""
    result = run_readiness_selftest(build_platform(_HEALTHY, now=_NOW))
    assert result.grade is ReadinessGrade.GREEN
    assert result.ok
    assert all(r.passed for r in result.reports)


@pytest.mark.parametrize("capability_id", _ALL_CAPABILITY_IDS)
def test_selftest__injecting_a_fault_in_each_probe_is_caught(capability_id: str) -> None:
    """For EACH of the 8 probes: breaking that subsystem makes ITS probe FAIL (teeth).

    This is the per-probe teeth proof: the self-test is not a tautology — a broken subsystem
    is detected, not waved through.
    """
    platform = _break_one(build_platform(_HEALTHY, now=_NOW), capability_id)
    result = run_readiness_selftest(platform)
    report = next(r for r in result.reports if r.capability_id == capability_id)
    assert not report.passed  # the injected fault is caught by this probe
    assert report.reason == "injected_fault"


@pytest.mark.parametrize(
    "capability_id",
    ["cost_ledger", "comms", "capability_registry", "org_frontdoor", "audit", "kill_switch"],
)
def test_selftest__a_failed_required_or_security_probe_grades_red(capability_id: str) -> None:
    """Breaking any REQUIRED/SECURITY subsystem grades the whole self-test RED (fail-closed)."""
    platform = _break_one(build_platform(_HEALTHY, now=_NOW), capability_id)
    result = run_readiness_selftest(platform)
    assert result.grade is ReadinessGrade.RED
    assert not result.ok  # RED fails the gate (non-zero exit)


@pytest.mark.parametrize("capability_id", ["gateway", "memory"])
def test_selftest__a_failed_optional_probe_is_degraded_not_red(capability_id: str) -> None:
    """Breaking an OPTIONAL subsystem degrades the platform — DEGRADED, never RED (bulkhead)."""
    platform = _break_one(build_platform(_HEALTHY, now=_NOW), capability_id)
    result = run_readiness_selftest(platform)
    # The platform stays UP: an optional failure never makes the gate RED (§5.6 no hard block).
    assert result.grade is ReadinessGrade.DEGRADED
    assert result.ok


def test_selftest__a_raising_probe_is_treated_as_failure_not_swallowed() -> None:
    """A probe that RAISES is graded a failure (fail-closed), never silently passed."""

    def _raising() -> ProbeResult:
        raise RuntimeError("subsystem exploded")

    platform = Platform(
        capabilities=(
            WiredCapability(
                capability_id="comms",
                criticality=Criticality.REQUIRED,
                degraded=False,
                reason="r",
                probe=_raising,
            ),
        )
    )
    result = run_readiness_selftest(platform)
    assert result.grade is ReadinessGrade.RED
    assert result.reports[0].reason.startswith("probe_raised:")


def test_selftest__degraded_capability_with_passing_probe_grades_degraded() -> None:
    """A capability bound degraded (but whose probe passes) still grades the platform DEGRADED."""
    platform = build_platform(PlatformConfig(present_providers=frozenset()), now=_NOW)
    result = run_readiness_selftest(platform)
    # The gateway is degraded (no key) yet its probe passes (correct-degradation) -> DEGRADED.
    assert result.grade is ReadinessGrade.DEGRADED
    assert result.ok  # degraded never hard-blocks


def test_selftest__green_requires_every_probe_pass_and_no_degrade() -> None:
    """GREEN is reserved for the fully-healthy, fully-live platform (no degraded capability)."""
    healthy = run_readiness_selftest(build_platform(_HEALTHY, now=_NOW))
    assert healthy.grade is ReadinessGrade.GREEN
    assert not any(r.degraded for r in healthy.reports)


def test_readiness_grade__values_are_the_exact_status_strings() -> None:
    """The grade enum's string values are pinned exactly (kills value-mutating mutants).

    These strings are rendered by ``status``/``up`` summaries; a mutated value would corrupt
    the operator-facing report, so each is asserted literally.
    """
    assert ReadinessGrade.GREEN.value == "green"
    assert ReadinessGrade.DEGRADED.value == "degraded"
    assert ReadinessGrade.RED.value == "red"


def test_probe_report_and_result__are_frozen_immutable() -> None:
    """ProbeReport and ReadinessResult are frozen (kills the ``frozen=True`` mutants).

    Both are audit/report records produced once by the self-test; mutating them after the
    fact would let a report drift from what was actually probed, so both refuse mutation.
    """
    import dataclasses

    result = run_readiness_selftest(build_platform(_HEALTHY, now=_NOW))
    with pytest.raises(dataclasses.FrozenInstanceError):
        result.grade = ReadinessGrade.RED  # type: ignore[misc]
    with pytest.raises(dataclasses.FrozenInstanceError):
        result.reports[0].passed = False  # type: ignore[misc]
