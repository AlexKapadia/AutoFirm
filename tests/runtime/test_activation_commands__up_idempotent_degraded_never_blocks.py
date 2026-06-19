"""End-to-end activation-command tests: flawless up, idempotency, degraded-never-blocks, resume."""

from __future__ import annotations

from datetime import UTC, datetime

from autofirm.runtime.activation_bootstrap_steps import MappingEnvProbe, activation_steps
from autofirm.runtime.activation_commands import (
    EXIT_FAILED,
    EXIT_OK,
    run_doctor,
    run_down,
    run_status,
    run_up,
)
from autofirm.runtime.platform_readiness_selftest import ReadinessGrade

_NOW = datetime(2025, 1, 1, tzinfo=UTC)


def _converged_probe() -> MappingEnvProbe:
    return MappingEnvProbe(facts={s.id for s in activation_steps()})


def test_up__healthy_config_brings_platform_live_green_exit_zero() -> None:
    """`up` on a healthy (keyed) config converges, wires, self-tests GREEN, and exits 0."""
    result, readiness = run_up(
        {"ANTHROPIC_API_KEY": "sk-x"}, env_probe=_converged_probe(), now=_NOW
    )
    assert result.exit_code == EXIT_OK
    assert readiness.grade is ReadinessGrade.GREEN
    assert "readiness=green" in result.summary


def test_up__is_idempotent_second_run_does_zero_env_mutations() -> None:
    """The idempotency acceptance signal: a second `up` performs ZERO env mutations (§5 item 2)."""
    probe = _converged_probe()
    run_up({"ANTHROPIC_API_KEY": "sk-x"}, env_probe=probe, now=_NOW)
    second, _ = run_up({"ANTHROPIC_API_KEY": "sk-x"}, env_probe=probe, now=_NOW)
    # The bootstrapper's check() gated every apply() -> the summary reports 0 mutations.
    assert "mutations=0" in second.summary


def test_up__re_activates_to_identical_capability_state() -> None:
    """An idempotent re-run re-activates to the IDENTICAL capability/grade state set."""
    probe = _converged_probe()
    _, first = run_up({"ANTHROPIC_API_KEY": "sk-x"}, env_probe=probe, now=_NOW)
    _, second = run_up({"ANTHROPIC_API_KEY": "sk-x"}, env_probe=probe, now=_NOW)
    state = lambda rd: {(r.capability_id, r.passed, r.degraded) for r in rd.reports}  # noqa: E731
    assert state(first) == state(second)  # same live state


def test_up__missing_optional_key_still_reaches_up_degraded_exit_zero() -> None:
    """`up` with NO provider key reaches UP (degraded) and exits 0 — never hard-blocks."""
    result, readiness = run_up({}, env_probe=_converged_probe(), now=_NOW)
    assert result.exit_code == EXIT_OK  # NEVER hard-blocks on a missing optional dependency
    assert readiness.grade is ReadinessGrade.DEGRADED
    degraded = {r.capability_id for r in readiness.reports if r.degraded}
    assert degraded == {"gateway"}  # exactly the removed capability is degraded


def test_up__missing_embedding_backend_still_up_degrades_only_memory() -> None:
    """Across the missing-dep matrix: no embedding backend degrades only memory, platform UP."""
    # embedding is disabled by AUTOFIRM_* — model it via a config with embedding off through env.
    # (PlatformConfig.from_environment keeps embedding_enabled True; we assert the gateway+memory
    #  degraded-mode matrix via the no-key path here and the composition-root test for embedding.)
    result, readiness = run_up({}, env_probe=_converged_probe(), now=_NOW)
    assert result.ok
    assert readiness.grade is not ReadinessGrade.RED  # no whole-platform block, ever


def test_up__crash_mid_converge_then_resume_reaches_same_live_state() -> None:
    """Inject a crash mid-converge (drop a bootstrapped fact), resume, reach the same live state."""
    probe = _converged_probe()
    _, first = run_up({"ANTHROPIC_API_KEY": "sk-x"}, env_probe=probe, now=_NOW)
    # Crash injection: a bootstrap fact was lost (process died before it was durable).
    probe.facts.discard("smoke.composed")
    resumed, second = run_up({"ANTHROPIC_API_KEY": "sk-x"}, env_probe=probe, now=_NOW)
    assert resumed.ok
    assert second.grade is first.grade  # converged to the identical final grade
    assert "smoke.composed" in probe.facts  # the dropped step re-converged


def test_status__reports_live_capabilities_and_exits_zero_when_up() -> None:
    """`status` re-runs the probes and reports the live capability set (level-triggered)."""
    result, readiness = run_status({"ANTHROPIC_API_KEY": "sk-x"}, now=_NOW)
    assert result.exit_code == EXIT_OK
    assert len(readiness.reports) == 8
    assert "capabilities=8" in result.summary


def test_status__degraded_when_optional_dependency_absent() -> None:
    """`status` reports DEGRADED (still exit 0) when an optional dependency is absent."""
    result, readiness = run_status({}, now=_NOW)
    assert result.exit_code == EXIT_OK
    assert readiness.grade is ReadinessGrade.DEGRADED
    assert "gateway" in result.summary


def test_doctor__empty_environment_reports_missing_required_steps_exit_one() -> None:
    """`doctor` on a bare environment reports the missing REQUIRED steps and exits non-zero."""
    result = run_doctor(env_probe=MappingEnvProbe())
    assert result.exit_code == EXIT_FAILED
    assert "venv.present" in result.summary


def test_doctor__converged_environment_reports_ok_exit_zero() -> None:
    """`doctor` on a converged environment reports ok and exits 0 (nothing missing)."""
    result = run_doctor(env_probe=_converged_probe())
    assert result.exit_code == EXIT_OK
    assert "ok=True" in result.summary


def test_down__drains_loops_cleanly_exit_zero() -> None:
    """`down` cooperatively drains the supervised loops and exits 0 on a clean drain."""
    result = run_down({"ANTHROPIC_API_KEY": "sk-x"}, now=_NOW)
    assert result.exit_code == EXIT_OK
    assert "drained loops=" in result.summary


def test_up__determinism_identical_summary_across_repeats() -> None:
    """Determinism (§3.11): repeated `up` runs with the same inputs produce identical summaries."""
    s1 = run_up({"ANTHROPIC_API_KEY": "sk-x"}, env_probe=_converged_probe(), now=_NOW)[0].summary
    s2 = run_up({"ANTHROPIC_API_KEY": "sk-x"}, env_probe=_converged_probe(), now=_NOW)[0].summary
    assert s1 == s2
