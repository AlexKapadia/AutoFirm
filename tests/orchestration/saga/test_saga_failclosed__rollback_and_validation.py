"""Fail-closed + rollback-failure hardening tests for the saga core.

Targets the security/correctness-critical branches the mutation gate must see
killed (CLAUDE.md §3.6; ADR-001 §3 step 6): a failing compensator must yield a
FAILED (never falsely COMPENSATED) terminal state, saga construction must refuse
malformed sagas (empty / missing-compensator / duplicate-name), and the
compensated-once short-circuit on repeated rollback must hold. Synthetic only.
"""

from __future__ import annotations

import pytest

from autofirm.orchestration.saga.runtimes.anyio_adapter import AnyioAdapter
from autofirm.orchestration.saga.saga_executor import run_saga
from autofirm.orchestration.saga.saga_model import (
    Saga,
    SagaAbort,
    SagaState,
    Step,
    StepContext,
    make_checkpoint,
    record_compensated,
    record_forward,
)

ADAPTER = AnyioAdapter()


async def _ok_forward(ctx: StepContext) -> None:
    return None


async def _ok_comp(ctx: StepContext) -> None:
    return None


async def _aborting_forward(ctx: StepContext) -> None:
    raise SagaAbort(ctx.step_name)


async def _raising_comp(ctx: StepContext) -> None:
    raise RuntimeError("compensator blew up")


# --------------------------------------------------------------------------- #
# A failing compensator => FAILED (fail-closed: never a clean COMPENSATED).     #
# --------------------------------------------------------------------------- #


@pytest.mark.unit
def test_failing_compensator_yields_failed_not_compensated() -> None:
    saga = Saga(
        name="f",
        steps=(
            Step(name="a", forward=_ok_forward, compensator=_raising_comp),
            Step(name="b", forward=_aborting_forward, compensator=_ok_comp),
        ),
    )
    cp = run_saga(saga, ADAPTER, make_checkpoint("g"))
    # a applied, b aborts -> rollback a -> a's compensator raises -> FAILED.
    assert cp.state is SagaState.FAILED
    assert cp.state is not SagaState.COMPENSATED  # fail-closed boundary


@pytest.mark.unit
def test_successful_rollback_is_compensated_not_failed() -> None:
    saga = Saga(
        name="ok",
        steps=(
            Step(name="a", forward=_ok_forward, compensator=_ok_comp),
            Step(name="b", forward=_aborting_forward, compensator=_ok_comp),
        ),
    )
    cp = run_saga(saga, ADAPTER, make_checkpoint("g"))
    assert cp.state is SagaState.COMPENSATED


# --------------------------------------------------------------------------- #
# Saga construction is fail-closed.                                            #
# --------------------------------------------------------------------------- #


@pytest.mark.unit
def test_empty_saga_is_refused() -> None:
    with pytest.raises(ValueError, match="at least one step"):
        Saga(name="e", steps=())


@pytest.mark.unit
def test_missing_compensator_is_refused() -> None:
    bad = Step(name="a", forward=_ok_forward, compensator=None)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="no compensator"):
        Saga(name="m", steps=(bad,))


@pytest.mark.unit
def test_duplicate_step_name_is_refused() -> None:
    s = Step(name="dup", forward=_ok_forward, compensator=_ok_comp)
    with pytest.raises(ValueError, match="duplicate step name"):
        Saga(name="d", steps=(s, s))


@pytest.mark.unit
def test_make_checkpoint_refuses_empty_goal() -> None:
    with pytest.raises(ValueError, match="goal_verbatim"):
        make_checkpoint("")


# --------------------------------------------------------------------------- #
# Replay-log accessors + compensated-once short-circuit (exactly-once).        #
# --------------------------------------------------------------------------- #


@pytest.mark.unit
def test_already_applied_and_compensated_keys_track_the_log() -> None:
    cp = make_checkpoint("g")
    cp = record_forward(cp, "k1", "a", 1)
    assert cp.already_applied("k1") is True
    assert cp.already_applied("k2") is False
    assert cp.compensated_keys() == frozenset()
    cp = record_compensated(cp, "k1", "a")
    assert cp.compensated_keys() == frozenset({"k1"})


@pytest.mark.unit
def test_resume_mid_rollback_compensates_only_outstanding_steps_exactly_once() -> None:
    # Crash-during-rollback resume: a,b,c were applied; c was already compensated
    # before the crash. On resume, an immediate abort must compensate ONLY b and a
    # (c is short-circuited by already_undone), each exactly once, reverse order.
    calls: list[str] = []

    async def comp(ctx: StepContext) -> None:
        calls.append(ctx.step_name)

    async def applied_fwd(ctx: StepContext) -> None:
        # Already-applied steps are skipped by the forward pass; this body would
        # only run if idempotency failed (it must not).
        calls.append(f"FORWARD-{ctx.step_name}")

    async def aborting(ctx: StepContext) -> None:
        raise SagaAbort(ctx.step_name)

    saga = Saga(
        name="mr",
        steps=(
            Step(name="a", forward=applied_fwd, compensator=comp),
            Step(name="b", forward=applied_fwd, compensator=comp),
            Step(name="c", forward=applied_fwd, compensator=comp),
            Step(name="d", forward=aborting, compensator=comp),
        ),
    )
    # Pre-seed the replay log: a,b,c applied; c already compensated (partial rollback).
    cp = make_checkpoint("g")
    for name, i in (("a", 1), ("b", 2), ("c", 3)):
        cp = record_forward(cp, saga.idempotency_key(name), name, i)
    cp = record_compensated(cp, saga.idempotency_key("c"), "c")

    out = run_saga(saga, ADAPTER, cp)
    assert out.state is SagaState.COMPENSATED
    # Only b and a compensated, reverse order, exactly once each; c short-circuited;
    # no forward re-applied (idempotency held).
    assert calls == ["b", "a"]


@pytest.mark.unit
def test_compensator_does_not_run_twice_across_two_rollbacks() -> None:
    # An aborting saga rolls back fully; running the SAME saga again from the
    # resulting checkpoint must not re-fire any compensator (all keys already undone).
    calls: list[str] = []

    async def comp(ctx: StepContext) -> None:
        calls.append(ctx.step_name)

    async def fwd(ctx: StepContext) -> None:
        return None

    async def aborting(ctx: StepContext) -> None:
        raise SagaAbort(ctx.step_name)

    saga = Saga(
        name="sa",
        steps=(
            Step(name="a", forward=fwd, compensator=comp),
            Step(name="b", forward=aborting, compensator=comp),
        ),
    )
    cp = run_saga(saga, ADAPTER, make_checkpoint("g"))
    assert calls == ["a"]  # a compensated once on the first rollback
    # Resume from the compensated checkpoint: nothing re-applies, nothing re-undoes.
    out = run_saga(saga, ADAPTER, cp)
    assert calls == ["a"]  # still exactly once
    assert out.state is SagaState.COMPENSATED
