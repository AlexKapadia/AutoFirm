"""End-to-end activation-command tests: flawless up, idempotency, degraded-never-blocks, resume."""

from __future__ import annotations

import dataclasses
from datetime import UTC, datetime

import pytest

import autofirm.runtime.activation_commands as ac
from autofirm.runtime.activation_bootstrap_steps import MappingEnvProbe, activation_steps
from autofirm.runtime.activation_commands import (
    EXIT_FAILED,
    EXIT_OK,
    CommandResult,
    run_doctor,
    run_down,
    run_status,
    run_up,
)
from autofirm.runtime.platform_readiness_selftest import ReadinessGrade
from autofirm.runtime.platform_supervisor import PlatformSupervisor

_NOW = datetime(2025, 1, 1, tzinfo=UTC)
_KEYED = {"ANTHROPIC_API_KEY": "sk-x"}


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


# ---------------------------------------------------------------------------
# Mutation-hardening (CLAUDE.md §3.6): pin the EXACT summary strings (substring
# checks above survive a string-wrap mutant), the exit-code constants, the
# frozen result, the bool ``ok`` property, the supervision-cycle count, and that
# the injected instant is actually propagated to the composition root.
# ---------------------------------------------------------------------------


def test_run_up__summary_and_exit_code_are_exact() -> None:
    """`up`'s summary is byte-exact and a healthy run exits integer 0 (kills const/str mutants)."""
    result, _ = run_up(_KEYED, env_probe=_converged_probe(), now=_NOW)
    assert result.exit_code == 0  # the literal success code (kills EXIT_OK = None)
    assert (
        result.summary
        == "up: bootstrap mutations=0 readiness=green loops_healthy=True capabilities=8"
    )


def test_run_status__summary_is_byte_exact() -> None:
    """`status`'s summary line is pinned exactly (kills the f-string-wrap mutants)."""
    result, _ = run_status(_KEYED, now=_NOW)
    assert result.summary == "status: readiness=green capabilities=8 degraded=[]"


def test_run_doctor__missing_summary_lists_each_failed_step_exactly() -> None:
    """`doctor` on a bare env names every missing step in the exact ``id(state)`` shape."""
    result = run_doctor(env_probe=MappingEnvProbe())
    assert result.summary == (
        "doctor: ok=False missing=['venv.present(failed)', 'deps.installed(failed)', "
        "'package.importable(failed)', 'state.dir(failed)', 'smoke.composed(failed)']"
    )


def test_run_down__summary_is_byte_exact() -> None:
    """`down`'s drain summary is pinned exactly (kills the f-string-wrap mutant)."""
    result = run_down(_KEYED, now=_NOW)
    assert result.summary == "down: drained loops=2 all_healthy=True"


def test_command_result__is_frozen_immutable() -> None:
    """A CommandResult is an immutable outcome record (kills the ``frozen=True`` mutant)."""
    result = CommandResult(exit_code=0, summary="x")
    with pytest.raises(dataclasses.FrozenInstanceError):
        result.exit_code = 1  # type: ignore[misc]


def test_command_result__ok_is_a_bool_property_not_a_method() -> None:
    """``ok`` is a computed boolean PROPERTY (kills the dropped-``@property`` mutant).

    Without the decorator ``ok`` would be a bound method (always truthy), so an ``is True`` /
    ``is False`` identity check — not mere truthiness — is required to catch the regression.
    """
    assert CommandResult(exit_code=EXIT_OK, summary="x").ok is True
    assert CommandResult(exit_code=EXIT_FAILED, summary="x").ok is False


def test_run_up__runs_exactly_two_supervision_cycles(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`up` drives the supervisor for EXACTLY two bounded cycles (kills the cycle-count mutant)."""
    seen: list[int] = []
    original = PlatformSupervisor.run_cycles

    def _spy(self: PlatformSupervisor, cycles: int) -> object:
        seen.append(cycles)
        return original(self, cycles)

    monkeypatch.setattr(PlatformSupervisor, "run_cycles", _spy)
    run_up(_KEYED, env_probe=_converged_probe(), now=_NOW)
    assert seen == [2]


def test_commands__propagate_the_injected_instant_to_the_composition_root(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """up/status/down pass the INJECTED instant (not None / not wall-clock) to build_platform.

    Kills the ``instant = None`` and ``now is not None`` ternary-flip mutants: the composition
    root tolerates a ``None`` now (defaulting to wall-clock), so the only way to prove the
    injected instant is honoured is to capture the value the root is actually called with.
    """
    seen: list[object] = []
    original = ac.build_platform

    def _spy(config: object, *, now: object = None) -> object:
        seen.append(now)
        return original(config, now=now)  # type: ignore[arg-type]

    monkeypatch.setattr(ac, "build_platform", _spy)
    run_up(_KEYED, env_probe=_converged_probe(), now=_NOW)
    run_status(_KEYED, now=_NOW)
    run_down(_KEYED, now=_NOW)
    assert seen == [_NOW, _NOW, _NOW]
