"""Adversarial tests for the idempotent bootstrapper: no-op re-run, crash-resume, DAG order.

Proves the B3 idempotency contract has teeth: ``check()`` gates ``apply()`` (a re-run mutates
nothing), a crash mid-converge resumes to the same state, the topological order is stable and
fail-closed on a bad DAG, and an unconvergeable required step resolves FAILED while an
optional one degrades.
"""

from __future__ import annotations

import dataclasses
import json
import os
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


def test_converge__independent_steps_drain_in_a_single_pass_ordered_by_id() -> None:
    """Independent (no-``requires``) steps all become ready in pass 0 and emit sorted by id.

    Exercises the bounded-loop early-drain ``break``: with N independent steps the DAG empties
    in one pass, so passes 1..N-1 must short-circuit instead of treating the now-empty
    ``remaining`` as a cycle. Order is the deterministic id tie-break (B3 clause 7).
    """
    probe = _Probe()
    steps = (_FactStep("gamma"), _FactStep("alpha"), _FactStep("beta"))
    result = IdempotentEnvironmentBootstrapper(steps).converge(probe)
    assert [o.step_id for o in result.outcomes] == ["alpha", "beta", "gamma"]
    assert result.mutations == 3  # every independent step applied exactly once
    assert {o.state for o in result.outcomes} == {StepState.APPLIED}


def test_converge__three_node_dependency_cycle_is_refused_by_bounded_guard() -> None:
    """A 3-node cycle (a->b->c->a) is refused; the bounded loop cannot spin on it (§7.2)."""
    with pytest.raises(ValueError, match="cycle"):
        IdempotentEnvironmentBootstrapper(
            (_FactStep("a", ("c",)), _FactStep("b", ("a",)), _FactStep("c", ("b",)))
        )


def test_converge__deep_linear_chain_drains_within_the_pass_bound() -> None:
    """A linear chain of length N needs exactly N passes — the bound (== len) must NOT raise.

    Pins the bounded-loop ceiling at exactly ``len(steps)``: one fewer pass would leave the
    last link unordered (and convergence would silently drop a step). The chain is the
    worst-case depth, so a correct bound resolves every step to APPLIED with no cycle error.
    """
    probe = _Probe()
    n = 12
    # link_k requires link_{k-1}; reversed insertion order proves the sort, not input order.
    steps = tuple(
        _FactStep(f"link_{k:02d}", () if k == 0 else (f"link_{k - 1:02d}",))
        for k in reversed(range(n))
    )
    result = IdempotentEnvironmentBootstrapper(steps).converge(probe)
    assert result.mutations == n  # every link applied — none dropped by an off-by-one bound
    assert [o.step_id for o in result.outcomes] == [f"link_{k:02d}" for k in range(n)]


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
    persisted = json.loads(ledger.read_text())
    assert set(persisted) == {"a", "b", "c"}  # every step recorded, deterministic order


# ---------------------------------------------------------------------------
# Mutation-hardening (CLAUDE.md §3.6): each test below kills a specific mutant
# that the broader behavioural tests above left alive. They pin EXACT audit
# strings, the frozen-result invariant, the sorted-ledger byte determinism, and
# the crash-atomic temp-suffix convention — none are tautological.
# ---------------------------------------------------------------------------


def test_bootstrap_result__is_frozen_immutable() -> None:
    """The terminal result is an immutable audit record (kills the ``frozen=True`` mutant).

    A converge result is reported and persisted; a mutant that flips it to a mutable
    dataclass (``frozen=False``) would let bookkeeping be rewritten after the fact, so we
    prove the attribute assignment raises.
    """
    result = IdempotentEnvironmentBootstrapper(_steps()).converge(_Probe())
    with pytest.raises(dataclasses.FrozenInstanceError):
        result.mutations = 999  # type: ignore[misc]


def test_converge__unknown_requirement_message_is_byte_exact() -> None:
    """The dangling-requirement error text is pinned EXACTLY (kills the f-string-wrap mutant).

    The earlier test matches a substring, which a string-wrapping mutant survives (the
    substring is still present). Asserting the full message kills it.
    """
    with pytest.raises(ValueError) as exc:
        IdempotentEnvironmentBootstrapper((_FactStep("x", ("missing",)),))
    assert str(exc.value) == "step 'x' requires unknown step 'missing'"


def test_converge__dependency_cycle_message_is_byte_exact() -> None:
    """The cycle error text is pinned EXACTLY, including the sorted remaining-id list."""
    with pytest.raises(ValueError) as exc:
        IdempotentEnvironmentBootstrapper(
            (_FactStep("x", ("y",)), _FactStep("y", ("x",)))
        )
    assert str(exc.value) == "dependency cycle among steps: ['x', 'y']"


def test_converge__satisfied_outcome_detail_is_exact() -> None:
    """A no-op (already-converged) step carries the exact ``already_converged`` audit detail."""
    probe = _Probe(facts={"a", "b", "c"})  # every fact already present -> SATISFIED branch
    result = IdempotentEnvironmentBootstrapper(_steps()).converge(probe)
    assert {o.state for o in result.outcomes} == {StepState.SATISFIED}
    assert {o.detail for o in result.outcomes} == {"already_converged"}


def test_converge__applied_outcome_detail_is_exact() -> None:
    """A step converged this run carries the exact ``converged_this_run`` audit detail."""
    result = IdempotentEnvironmentBootstrapper(_steps()).converge(_Probe())
    assert {o.state for o in result.outcomes} == {StepState.APPLIED}
    assert {o.detail for o in result.outcomes} == {"converged_this_run"}


def test_converge__degraded_outcome_detail_is_exact() -> None:
    """An unconvergeable OPTIONAL step carries the exact degraded audit detail."""
    result = IdempotentEnvironmentBootstrapper(
        (_StuckStep("plotting", Criticality.OPTIONAL),)
    ).converge(_Probe())
    assert result.outcomes[0].detail == "optional_step_unconverged_capability_degraded"


def test_converge__failed_outcome_detail_is_exact() -> None:
    """An unconvergeable REQUIRED step carries the exact fail-closed audit detail."""
    result = IdempotentEnvironmentBootstrapper(
        (_StuckStep("db.migrate", Criticality.REQUIRED),)
    ).converge(_Probe())
    assert result.outcomes[0].detail == "critical_step_unconverged_failed_closed"


def test_converge__ledger_keys_are_serialised_sorted_not_insertion_order(
    tmp_path: Path,
) -> None:
    """The ledger is written with ``sort_keys=True`` so its bytes are order-independent.

    Uses steps whose topological (insertion) order [z, a] differs from sorted order [a, z]:
    a mutant flipping ``sort_keys`` to False would emit insertion order, so the on-disk key
    sequence pins the deterministic-bytes invariant (B3 §1.2.5).
    """
    ledger = tmp_path / "ledger.json"
    # `a` requires `z`, so the topological emit order is z-then-a (NOT alphabetical).
    steps = (_FactStep("a", ("z",)), _FactStep("z"))
    IdempotentEnvironmentBootstrapper(steps, ledger_path=ledger).converge(_Probe())
    persisted = json.loads(ledger.read_text())
    assert list(persisted) == ["a", "z"]  # sorted bytes, NOT the [z, a] insertion order


def test_converge__ledger_temp_file_uses_dot_tmp_suffix(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The crash-atomic write stages through ``<ledger>.tmp`` exactly (kills the suffix mutant).

    The atomic-rename protocol writes a sibling temp then ``os.replace``s it into place; the
    temp name convention is observable only via the rename source, so we spy on ``os.replace``
    and pin the staged path. A mutant that corrupts the ".tmp" suffix is caught here.
    """
    captured: dict[str, str] = {}
    real_replace = os.replace

    def _spy_replace(src: object, dst: object) -> None:
        captured["src"] = str(src)
        real_replace(src, dst)  # type: ignore[arg-type]

    monkeypatch.setattr(os, "replace", _spy_replace)
    ledger = tmp_path / "ledger.json"
    IdempotentEnvironmentBootstrapper(_steps(), ledger_path=ledger).converge(_Probe())
    assert captured["src"] == str(ledger) + ".tmp"
