"""Adversarial tests for the idempotent bootstrapper: no-op re-run, crash-resume, DAG order.

Proves the B3 idempotency contract has teeth: ``check()`` gates ``apply()`` (a re-run mutates
nothing), a crash mid-converge resumes to the same state, the topological order is stable and
fail-closed on a bad DAG, and an unconvergeable required step resolves FAILED while an
optional one degrades.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pytest

from autofirm.bootstrap.bootstrap_step_contract import Criticality, EnvProbe, StepState
from autofirm.bootstrap.idempotent_environment_bootstrapper import (
    IdempotentEnvironmentBootstrapper,
)


@dataclass
class _Probe:
    """A deterministic in-memory env probe recording facts and counting record() calls."""

    facts: set[str] = field(default_factory=set)
    record_calls: int = 0

    def has(self, key: str) -> bool:
        return key in self.facts

    def record(self, key: str) -> None:
        self.record_calls += 1
        self.facts.add(key)


@dataclass(frozen=True)
class _FactStep:
    """A re-entrant fact-converging step (check() True iff fact present; apply() records it)."""

    fact: str
    requires_facts: tuple[str, ...] = ()
    step_criticality: Criticality = Criticality.REQUIRED

    @property
    def id(self) -> str:
        return self.fact

    @property
    def requires(self) -> tuple[str, ...]:
        return self.requires_facts

    @property
    def criticality(self) -> Criticality:
        return self.step_criticality

    def check(self, env: EnvProbe) -> bool:
        return env.has(self.fact)

    def apply(self, env: EnvProbe) -> None:
        env.record(self.fact)


@dataclass(frozen=True)
class _StuckStep:
    """A step whose apply() does NOT converge (check() stays False) — models a hard failure."""

    fact: str
    step_criticality: Criticality

    @property
    def id(self) -> str:
        return self.fact

    @property
    def requires(self) -> tuple[str, ...]:
        return ()

    @property
    def criticality(self) -> Criticality:
        return self.step_criticality

    def check(self, env: EnvProbe) -> bool:
        return False  # never satisfied — apply() cannot make check() true

    def apply(self, env: EnvProbe) -> None:
        env.record(self.fact + ".attempted")  # records an attempt but never converges


def _steps() -> tuple[_FactStep, ...]:
    return (
        _FactStep("c", ("b",)),
        _FactStep("a"),
        _FactStep("b", ("a",)),
    )


def test_converge__from_empty_applies_every_step_in_dependency_order() -> None:
    """A first run on an empty env applies every step and counts the mutations."""
    probe = _Probe()
    result = IdempotentEnvironmentBootstrapper(_steps()).converge(probe)
    assert result.mutations == 3
    assert {o.state for o in result.outcomes} == {StepState.APPLIED}
    assert result.converged


def test_converge__rerun_on_converged_env_is_an_asserted_no_op() -> None:
    """The idempotency acceptance signal: a second converge performs ZERO mutations (B3 §3.2)."""
    probe = _Probe()
    bootstrapper = IdempotentEnvironmentBootstrapper(_steps())
    bootstrapper.converge(probe)
    record_calls_after_first = probe.record_calls
    second = bootstrapper.converge(probe)
    # check() gated apply() to a no-op: no new record() calls, mutation counter == 0.
    assert second.mutations == 0
    assert probe.record_calls == record_calls_after_first
    assert {o.state for o in second.outcomes} == {StepState.SATISFIED}


def test_converge__crash_mid_converge_resumes_to_identical_state() -> None:
    """Injecting a crash after some steps applied, then re-running, converges to the same set.

    Simulates a crash by running the loop, dropping the in-flight facts of the LAST step, and
    re-running: the resume re-runs check() in order and converges the missing step only.
    """
    probe = _Probe()
    bootstrapper = IdempotentEnvironmentBootstrapper(_steps())
    bootstrapper.converge(probe)
    full_state = set(probe.facts)
    # Crash injection: the durable env lost the last-applied fact ("c"), as if the process
    # died after applying b but before c was durable.
    probe.facts.discard("c")
    probe.record_calls = 0
    resume = bootstrapper.converge(probe)
    assert resume.mutations == 1  # only the missing step re-applied (a,b skipped via check())
    assert probe.facts == full_state  # final state identical to an uninterrupted run


def test_converge__unknown_requirement_fails_closed_at_construction() -> None:
    """A step requiring an unknown step is refused at construction (fail-closed DAG)."""
    with pytest.raises(ValueError, match="unknown step"):
        IdempotentEnvironmentBootstrapper((_FactStep("x", ("missing",)),))


def test_converge__dependency_cycle_is_refused() -> None:
    """A cyclic DAG cannot be ordered and is refused, not silently reordered."""
    with pytest.raises(ValueError, match="cycle"):
        IdempotentEnvironmentBootstrapper(
            (_FactStep("x", ("y",)), _FactStep("y", ("x",)))
        )


def test_converge__topological_order_respects_requires() -> None:
    """A step never converges before its requirements (order is honoured every run)."""
    probe = _Probe()
    bootstrapper = IdempotentEnvironmentBootstrapper(_steps())
    bootstrapper.converge(probe)
    applied_order = [o.step_id for o in bootstrapper.converge(_Probe()).outcomes]
    assert applied_order.index("a") < applied_order.index("b") < applied_order.index("c")


def test_converge__unconvergeable_required_step_resolves_failed() -> None:
    """A REQUIRED step whose apply() cannot converge resolves FAILED (fail-closed, not skipped)."""
    result = IdempotentEnvironmentBootstrapper(
        (_StuckStep("db.migrate", Criticality.REQUIRED),)
    ).converge(_Probe())
    assert result.outcomes[0].state is StepState.FAILED
    assert not result.converged  # a FAILED required step makes the run non-converged


def test_converge__unconvergeable_optional_step_degrades_platform_stays_up() -> None:
    """An OPTIONAL step that cannot converge DEGRADES (platform stays UP), never FAILED."""
    result = IdempotentEnvironmentBootstrapper(
        (_StuckStep("plotting", Criticality.OPTIONAL),)
    ).converge(_Probe())
    assert result.outcomes[0].state is StepState.DEGRADED
    assert result.converged  # DEGRADED is acceptable — no whole-platform block


def test_converge__writes_crash_atomic_ledger_with_no_temp_left_behind(tmp_path: Path) -> None:
    """The durable ledger is written atomically; no .tmp file survives a successful write."""
    ledger = tmp_path / "bootstrap_ledger.json"
    IdempotentEnvironmentBootstrapper(_steps(), ledger_path=ledger).converge(_Probe())
    assert ledger.exists()
    assert not ledger.with_suffix(ledger.suffix + ".tmp").exists()  # atomic rename consumed it
    import json

    persisted = json.loads(ledger.read_text())
    assert set(persisted) == {"a", "b", "c"}  # every step recorded, deterministic order
