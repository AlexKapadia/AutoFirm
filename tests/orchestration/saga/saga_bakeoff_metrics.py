"""Bake-off measurement harness: the golden-set metrics, computed per runtime.

What this provides
------------------
The pre-registered golden-set evaluation for the ADR-001 §7 concurrency fork,
computed identically for each runtime adapter:

  * ``cancellation_safety_violations`` — over a cancel injected at every step
    boundary AND mid-step, count any run that did NOT land COMPENSATED, or whose
    compensators did not run exactly once each (double-/skipped-compensate).
  * ``idempotency_double_applies`` — over resume-from-every-prefix, count any
    forward action applied more than once across the resume sequence.
  * ``orphan_tasks`` — after a cancelled run, count event-loop tasks still alive
    beyond the entry task (a structured-concurrency leak).
  * ``determinism_violations`` — count distinct outcomes over repeated identical
    runs (must be 0 -> 1 unique outcome).

These functions are pure measurement (no asserts) so the same numbers feed both
the metric test (``test_bakeoff_metrics__golden_set``) and the results doc /
evidence. Synthetic only; no network.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

from autofirm.orchestration.saga.runtime_adapter import RuntimeAdapter
from autofirm.orchestration.saga.saga_executor import run_saga
from autofirm.orchestration.saga.saga_model import (
    Checkpoint,
    SagaState,
    make_checkpoint,
    record_forward,
)

from .synthetic_saga import FaultPlan, Ledger, build_saga

_GOLDEN_STEPS = 6  # the golden saga length used across every metric


@dataclass(frozen=True, slots=True)
class RuntimeMetrics:
    """The golden-set numbers for one runtime (lower is better; 0 is perfect)."""

    runtime: str
    cancellation_safety_violations: int
    idempotency_double_applies: int
    orphan_tasks: int
    determinism_violations: int


def _names(n: int) -> list[str]:
    return [f"s{i}" for i in range(n)]


def _exactly_once_ok(ledger: Ledger) -> bool:
    """True if every compensator ran at most once and only for applied steps."""
    for name in set(ledger.compensations):
        if ledger.compensate_count(name) != 1:
            return False
        if name not in ledger.forwards:
            return False
    # And the rollback must be the exact reverse of the applied steps.
    return ledger.compensations == list(reversed(ledger.forwards))


def measure_cancellation_safety(adapter: RuntimeAdapter) -> int:
    """Count cancellation-safety violations over boundary + mid-step cancels."""
    violations = 0
    names = _names(_GOLDEN_STEPS)
    for at in range(_GOLDEN_STEPS):
        for mid in (False, True):
            ledger = Ledger()
            saga = build_saga(
                "cs", names, ledger, FaultPlan(cancel_at_step=at, mid_step=mid)
            )
            cp = run_saga(saga, adapter, make_checkpoint("g"))
            if cp.state is not SagaState.COMPENSATED or not _exactly_once_ok(ledger):
                violations += 1
    return violations


def measure_idempotent_replay(adapter: RuntimeAdapter) -> int:
    """Count forward double-applies over resume-from-every-prefix sequences."""
    double_applies = 0
    names = _names(_GOLDEN_STEPS)
    for prefix in range(_GOLDEN_STEPS + 1):
        cp = _resumed_checkpoint("ir", names, prefix)
        ledger = Ledger()
        run_saga(build_saga("ir", names, ledger), adapter, cp)
        # A pre-applied step must NOT run again on resume.
        for i in range(prefix):
            double_applies += ledger.forward_count(names[i])
    return double_applies


def measure_orphans(adapter: RuntimeAdapter) -> int:
    """Count event-loop tasks left alive after a cancelled run (structured leak).

    Runs a cancel-injecting saga on the asyncio loop (the AnyIO winner uses the
    asyncio backend) and counts tasks beyond the single entry task. A structured
    runtime guarantees 0 because every child is joined on scope exit.
    """
    names = _names(_GOLDEN_STEPS)
    leaked = 0

    async def _probe() -> None:
        nonlocal leaked
        ledger = Ledger()
        saga = build_saga("orph", names, ledger, FaultPlan(cancel_at_step=2))
        # Drive the saga to completion within THIS loop, then inspect live tasks.
        await _drive_in_loop(saga, adapter)
        await asyncio.sleep(0)  # let any leaked child get a chance to be scheduled
        alive = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
        leaked = len([t for t in alive if not t.done()])

    asyncio.run(_probe())
    return leaked


async def _drive_in_loop(saga, adapter: RuntimeAdapter) -> None:  # type: ignore[no-untyped-def]
    """Run a saga's async core on the already-running asyncio loop (orphan probe)."""
    from autofirm.orchestration.saga.saga_executor import _drive  # noqa: PLC0415

    await _drive(saga, adapter, make_checkpoint("g"))


def measure_determinism(adapter: RuntimeAdapter) -> int:
    """Count distinct outcomes over repeated identical runs (0 violations = 1 outcome)."""
    names = _names(_GOLDEN_STEPS)
    outcomes: set[tuple[str, tuple[str, ...], tuple[str, ...]]] = set()
    for _ in range(30):
        ledger = Ledger()
        saga = build_saga("det", names, ledger, FaultPlan(cancel_at_step=3))
        cp = run_saga(saga, adapter, make_checkpoint("g"))
        outcomes.add((cp.state.value, tuple(ledger.forwards), tuple(ledger.compensations)))
    return len(outcomes) - 1  # >0 means non-deterministic


def _resumed_checkpoint(saga_name: str, names: list[str], applied: int) -> Checkpoint:
    """Build a checkpoint as if ``applied`` forward steps already ran."""
    cp = make_checkpoint("g")
    for i in range(applied):
        cp = record_forward(cp, f"{saga_name}::{names[i]}", names[i], i + 1)
    return cp


def measure_runtime(adapter: RuntimeAdapter) -> RuntimeMetrics:
    """Compute the full golden-set metric tuple for one runtime."""
    return RuntimeMetrics(
        runtime=adapter.name,
        cancellation_safety_violations=measure_cancellation_safety(adapter),
        idempotency_double_applies=measure_idempotent_replay(adapter),
        orphan_tasks=measure_orphans(adapter),
        determinism_violations=measure_determinism(adapter),
    )
