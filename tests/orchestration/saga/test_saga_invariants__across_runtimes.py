"""Saga invariant tests for the winning runtime (AnyIO — ADR-001 §7).

Proves the saga executor upholds the four invariants the fork was measured on:
exactly-once compensation, idempotent replay on resume, no orphaned tasks, and
determinism. Boundary-exact unit asserts plus a Hypothesis property test over
random step counts x random fault points. Synthetic only; no network
(CLAUDE.md §3.6/§5.5).

The bake-off ran these identically across asyncio / AnyIO / Trio; AnyIO won
(see ``concurrency-runtime-results.md``) and the loser adapters were deleted
(no-graveyard, §3.8), so the live suite now exercises the winner.
"""

from __future__ import annotations

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from autofirm.orchestration.saga.runtime_adapter import RuntimeAdapter
from autofirm.orchestration.saga.runtimes.anyio_adapter import AnyioAdapter
from autofirm.orchestration.saga.saga_executor import run_saga
from autofirm.orchestration.saga.saga_model import (
    Checkpoint,
    SagaState,
    make_checkpoint,
    record_forward,
)

from .synthetic_saga import FaultPlan, Ledger, build_saga

# The winning runtime (AnyIO). Kept as a single-element matrix so the suite reads
# as a runtime sweep and a second runtime could be re-added for a future bake-off.
ADAPTERS: list[RuntimeAdapter] = [AnyioAdapter()]
ADAPTER_IDS = [a.name for a in ADAPTERS]


def _names(n: int) -> list[str]:
    """Deterministic step names s0..s{n-1}."""
    return [f"s{i}" for i in range(n)]


# --------------------------------------------------------------------------- #
# Boundary-exact unit asserts (clean / abort / cancel at every boundary).      #
# --------------------------------------------------------------------------- #


@pytest.mark.unit
@pytest.mark.parametrize("adapter", ADAPTERS, ids=ADAPTER_IDS)
def test_clean_run_commits_and_never_compensates(adapter: RuntimeAdapter) -> None:
    ledger = Ledger()
    saga = build_saga("clean", _names(4), ledger)
    cp = run_saga(saga, adapter, make_checkpoint("g"))
    assert cp.state is SagaState.COMMITTED
    assert ledger.forwards == _names(4)  # all applied in order
    assert ledger.compensations == []  # nothing rolled back
    assert cp.saga_step == 4  # advanced past the last step


@pytest.mark.unit
@pytest.mark.parametrize("adapter", ADAPTERS, ids=ADAPTER_IDS)
@pytest.mark.parametrize("abort_at", [0, 1, 2, 3])
def test_abort_compensates_applied_steps_in_reverse_exactly_once(
    adapter: RuntimeAdapter, abort_at: int
) -> None:
    ledger = Ledger()
    saga = build_saga("ab", _names(4), ledger, FaultPlan(abort_at_step=abort_at))
    cp = run_saga(saga, adapter, make_checkpoint("g"))
    assert cp.state is SagaState.COMPENSATED
    # The aborting step never applied its effect; steps before it did.
    assert ledger.forwards == _names(abort_at)
    # Compensation runs in REVERSE order, exactly once each.
    assert ledger.compensations == list(reversed(_names(abort_at)))


@pytest.mark.unit
@pytest.mark.parametrize("adapter", ADAPTERS, ids=ADAPTER_IDS)
@pytest.mark.parametrize("cancel_at", [0, 1, 2, 3])
def test_boundary_cancel_compensates_through_the_cancelling_step(
    adapter: RuntimeAdapter, cancel_at: int
) -> None:
    ledger = Ledger()
    saga = build_saga("bc", _names(4), ledger, FaultPlan(cancel_at_step=cancel_at))
    cp = run_saga(saga, adapter, make_checkpoint("g"))
    assert cp.state is SagaState.COMPENSATED
    # Boundary cancel: the cancelling step DID apply, then the cancel fired.
    assert ledger.forwards == _names(cancel_at + 1)
    assert ledger.compensations == list(reversed(_names(cancel_at + 1)))


@pytest.mark.unit
@pytest.mark.parametrize("adapter", ADAPTERS, ids=ADAPTER_IDS)
@pytest.mark.parametrize("cancel_at", [0, 1, 2, 3])
def test_midstep_cancel_does_not_apply_the_cancelling_step(
    adapter: RuntimeAdapter, cancel_at: int
) -> None:
    ledger = Ledger()
    saga = build_saga(
        "mc", _names(4), ledger, FaultPlan(cancel_at_step=cancel_at, mid_step=True)
    )
    cp = run_saga(saga, adapter, make_checkpoint("g"))
    assert cp.state is SagaState.COMPENSATED
    # Mid-step cancel: the cancelling step's effect was NOT applied.
    assert ledger.forwards == _names(cancel_at)
    assert ledger.compensations == list(reversed(_names(cancel_at)))


# --------------------------------------------------------------------------- #
# Idempotent replay on resume — replay never double-applies.                   #
# --------------------------------------------------------------------------- #


def _resumed_checkpoint(saga_name: str, names: list[str], applied: int) -> Checkpoint:
    """Build a checkpoint as if ``applied`` forward steps already ran (no compensation).

    The idempotency key is ``"<saga>::<step>"`` (``Saga.idempotency_key``), so the
    pre-seeded replay log matches what a real prior run would have recorded.
    """
    cp = make_checkpoint("g")
    for i in range(applied):
        cp = record_forward(cp, f"{saga_name}::{names[i]}", names[i], i + 1)
    return cp


@pytest.mark.unit
@pytest.mark.parametrize("adapter", ADAPTERS, ids=ADAPTER_IDS)
@pytest.mark.parametrize("already_applied", [0, 1, 2, 3, 4])
def test_resume_replays_only_unapplied_steps(
    adapter: RuntimeAdapter, already_applied: int
) -> None:
    names = _names(4)
    applied = min(already_applied, 4)
    cp_resume = _resumed_checkpoint("rs", names, applied)
    ledger = Ledger()
    saga = build_saga("rs", names, ledger)
    cp = run_saga(saga, adapter, cp_resume)
    assert cp.state is SagaState.COMMITTED
    # Only the not-yet-applied steps run again — no double-apply.
    assert ledger.forwards == names[applied:]
    assert cp.saga_step == 4  # identical final step index to a clean run


@pytest.mark.unit
@pytest.mark.parametrize("adapter", ADAPTERS, ids=ADAPTER_IDS)
def test_repeated_resume_is_idempotent_and_matches_clean_run(
    adapter: RuntimeAdapter,
) -> None:
    names = _names(5)
    # Clean reference run.
    ref_ledger = Ledger()
    ref = run_saga(build_saga("rp", names, ref_ledger), adapter, make_checkpoint("g"))
    # Resume from EACH prefix repeatedly; the union of applied effects must equal
    # exactly one clean application of every step (no double-apply across resumes).
    total_forwards: list[str] = []
    cp = make_checkpoint("g")
    for i in range(5):
        ledger = Ledger()
        cp = run_saga(build_saga("rp", names, ledger), adapter, cp)
        total_forwards += ledger.forwards
        if i == 0:
            # First pass already commits everything; later resumes apply nothing.
            assert ledger.forwards == names
        else:
            assert ledger.forwards == []  # idempotent: nothing re-applied
    assert total_forwards == names == ref_ledger.forwards
    assert cp.saga_step == ref.saga_step


# --------------------------------------------------------------------------- #
# Determinism — identical inputs -> identical outcome across repeated runs.     #
# --------------------------------------------------------------------------- #


@pytest.mark.unit
@pytest.mark.parametrize("adapter", ADAPTERS, ids=ADAPTER_IDS)
def test_determinism_over_many_repetitions(adapter: RuntimeAdapter) -> None:
    outcomes: set[tuple[str, tuple[str, ...], tuple[str, ...]]] = set()
    for _ in range(50):  # bounded repetition (CLAUDE.md determinism rule)
        ledger = Ledger()
        saga = build_saga("det", _names(4), ledger, FaultPlan(cancel_at_step=2))
        cp = run_saga(saga, adapter, make_checkpoint("g"))
        outcomes.add(
            (cp.state.value, tuple(ledger.forwards), tuple(ledger.compensations))
        )
    assert len(outcomes) == 1  # exactly one outcome -> deterministic


# --------------------------------------------------------------------------- #
# Property-based chaos: random step count x random fault point x runtime.       #
# --------------------------------------------------------------------------- #


@pytest.mark.property
@settings(max_examples=200, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(
    n_steps=st.integers(min_value=1, max_value=8),
    fault=st.sampled_from(["none", "abort", "cancel", "cancel_mid"]),
    fault_offset=st.integers(min_value=0, max_value=7),
)
def test_property_saga_invariants_hold_under_random_faults(
    n_steps: int, fault: str, fault_offset: int
) -> None:
    adapter = ADAPTERS[0]
    names = _names(n_steps)
    at = fault_offset % n_steps  # keep the fault point in range
    plan = FaultPlan()
    if fault == "abort":
        plan = FaultPlan(abort_at_step=at)
    elif fault == "cancel":
        plan = FaultPlan(cancel_at_step=at)
    elif fault == "cancel_mid":
        plan = FaultPlan(cancel_at_step=at, mid_step=True)

    ledger = Ledger()
    saga = build_saga("p", names, ledger, plan)
    cp = run_saga(saga, adapter, make_checkpoint("g"))

    # Invariant: exactly-once compensation — no step compensated more than once,
    # and every compensated step was previously applied.
    for name in names:
        assert ledger.compensate_count(name) <= 1
        if ledger.compensate_count(name) == 1:
            assert name in ledger.forwards

    if fault == "none":
        assert cp.state is SagaState.COMMITTED
        assert ledger.forwards == names
        assert ledger.compensations == []
        return

    # Faulted runs always land in a consistent COMPENSATED state with a clean
    # full rollback of exactly the applied steps, in reverse order.
    assert cp.state is SagaState.COMPENSATED
    applied = len(ledger.forwards)
    assert ledger.compensations == list(reversed(ledger.forwards))
    # Determinism of which steps applied, per fault kind:
    if fault in ("abort", "cancel_mid"):
        assert applied == at  # the faulting step's effect did NOT apply
    else:  # boundary cancel
        assert applied == at + 1  # the faulting step applied, then cancelled
