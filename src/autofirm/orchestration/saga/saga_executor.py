"""The single, runtime-agnostic saga executor (the bake-off's unit-under-test).

What this does
--------------
Drives a :class:`~autofirm.orchestration.saga.saga_model.Saga` to a consistent
terminal state through any :class:`~autofirm.orchestration.saga.runtime_adapter.RuntimeAdapter`.
It enforces the three saga invariants identically for asyncio, AnyIO, and Trio:

  1. **Exactly-once compensation.** If a forward step aborts or the run is
     cancelled mid-/between steps, every *already-applied* forward action is
     compensated exactly once, in reverse order — no double-compensate, no
     skipped compensate.
  2. **Idempotent replay on resume.** Re-running from a checkpoint never
     re-applies a forward action whose idempotency key is already in the replay
     log; the final state is identical to a clean run.
  3. **No orphaned tasks.** Any child work a step spawns runs inside the adapter's
     structured scope, so a cancel cancels-and-joins it — nothing leaks.

Why it exists / where it sits
-----------------------------
This is the file the concurrency-runtime experiment (ADR-001 §7) measures: the
saga semantics live here *once*, and only the adapter swaps. It is the
mutation-hardened core of the winning runtime.

Compensation runs *inside* the structured scope and the executor returns a
terminal checkpoint normally rather than letting a cancel/abort propagate through
the scope. This deliberately side-steps asyncio.TaskGroup's exception-group
wrapping (a structured-concurrency ergonomics difference the bake-off records):
by handling the fault inside the scope body, the scope always exits cleanly while
still cancelling+joining any children (no orphans) on every runtime.

Security / compliance invariants upheld
---------------------------------------
Fail-closed (CLAUDE.md §5.6): a cancellation is always handled (compensate then
mark COMPENSATED) — never converted into a falsely-COMMITTED success. If a
compensator itself fails, the saga ends ``FAILED`` (operator-attention), never
falsely ``COMPENSATED``. The replay log is append-only (mirrors A6); idempotency
keys gate every forward effect so replay can never double-apply (A3 src 09).
"""

from __future__ import annotations

from .runtime_adapter import RuntimeAdapter, Scope
from .saga_model import (
    Checkpoint,
    Saga,
    SagaAbort,
    SagaState,
    StepContext,
    record_compensated,
    record_forward,
)

__all__ = ["CompensatorFailed", "run_saga"]


class CompensatorFailed(Exception):
    """A compensator raised during rollback — the saga is left FAILED (fail-closed)."""


async def _compensate(
    saga: Saga,
    checkpoint: Checkpoint,
    applied_indices: list[int],
) -> Checkpoint:
    """Run compensators for the applied steps in reverse, exactly once each.

    ``applied_indices`` is the ordered list of step indices whose forward action
    actually ran in THIS attempt. We undo in reverse order. Each compensator whose
    key is not already in the log's compensated set runs once, then is recorded. A
    compensator failure raises :class:`CompensatorFailed` (the saga becomes FAILED).
    """
    cp = checkpoint
    already_undone = cp.compensated_keys()
    for idx in reversed(applied_indices):
        step = saga.steps[idx]
        key = saga.idempotency_key(step.name)
        if key in already_undone:
            # exactly-once: this compensator already ran on a prior attempt -> skip.
            continue
        ctx = StepContext(step_name=step.name, idempotency_key=key, already_applied=True)
        try:
            await step.compensator(ctx)
        except Exception as exc:
            # fail-closed: a failed undo cannot be glossed as a clean rollback.
            raise CompensatorFailed(step.name) from exc
        cp = record_compensated(cp, key, step.name)
    return cp


async def _forward_pass(
    saga: Saga,
    adapter: RuntimeAdapter,
    scope: Scope,
    checkpoint: Checkpoint,
    applied_this_attempt: list[int],
) -> Checkpoint:
    """Apply each not-yet-applied forward step in order inside ``scope``.

    Appends the index of every step applied in THIS attempt to
    ``applied_this_attempt`` (so the caller can compensate exactly those on a
    fault). Raises ``SagaAbort`` or ``adapter.cancelled_exc`` out to the caller
    (handled in :func:`_drive` while still inside the scope) on a fault.
    """
    cp = checkpoint

    async def _step_checkpoint() -> None:
        # Loop-invariant (scope/adapter fixed for this saga run): a forward action
        # uses this to land a mid-step cancel after calling request_cancel().
        await adapter.checkpoint(scope)

    for idx, step in enumerate(saga.steps):
        key = saga.idempotency_key(step.name)
        # idempotent replay: skip a forward action already applied on a prior run.
        if cp.already_applied(key):
            continue
        # cancellation checkpoint at the step boundary: a pending cancel (requested
        # during an earlier step) is delivered HERE, before the next side effect,
        # so a boundary cancel never half-runs the following step.
        await adapter.checkpoint(scope)
        ctx = StepContext(
            step_name=step.name,
            idempotency_key=key,
            already_applied=False,
            request_cancel=scope.cancel,
            checkpoint=_step_checkpoint,
        )
        # A forward action may (a) complete its effect, (b) raise SagaAbort, or
        # (c) request_cancel()+await ctx.checkpoint() to land a mid-step cancel
        # BEFORE its effect — in which case it never reaches record_forward below.
        await step.forward(ctx)
        # Structured spawn: any child the step wants runs inside `scope`, so a
        # later cancel cancels+joins it (no orphan). The no-op marker child
        # exercises the structured-ownership path on every runtime.
        await adapter.spawn(scope, _noop_child)
        cp = record_forward(cp, key, step.name, idx + 1)
        applied_this_attempt.append(idx)
    # Final cancellation checkpoint: a cancel requested DURING the last step (a
    # boundary cancel with no following iteration to deliver it) is honoured here,
    # so a late cancel still triggers rollback rather than a false COMMITTED.
    await adapter.checkpoint(scope)
    return cp


async def _drive(
    saga: Saga,
    adapter: RuntimeAdapter,
    checkpoint: Checkpoint,
) -> Checkpoint:
    """Forward pass with rollback-on-abort/cancel, all inside one structured scope.

    The scope always exits cleanly (no exception propagates through it), so the
    asyncio.TaskGroup exception-group wrapping never fires and children are always
    cancelled+joined. Returns the terminal checkpoint.
    """
    cp = _with_state(checkpoint, SagaState.RUNNING)
    applied: list[int] = []
    async with adapter.open_scope() as scope:
        try:
            cp = await _forward_pass(saga, adapter, scope, cp, applied)
        except SagaAbort:
            # voluntary business rollback: compensate (shielded) then COMPENSATED.
            async with adapter.shielded():
                return await _rollback(saga, cp, applied, terminal=SagaState.COMPENSATED)
        except adapter.cancelled_exc:
            # external cancel: compensate under a shield so the rollback runs to
            # completion despite the fired cancel scope (exactly-once compensation
            # must never be interrupted), then end COMPENSATED. The cancel is
            # consumed here so the structured scope exits cleanly; children were
            # already cancelled+joined on entering this handler within the scope.
            async with adapter.shielded():
                return await _rollback(saga, cp, applied, terminal=SagaState.COMPENSATED)
    return _with_state(cp, SagaState.COMMITTED)


async def _rollback(
    saga: Saga,
    cp: Checkpoint,
    applied: list[int],
    *,
    terminal: SagaState,
) -> Checkpoint:
    """Compensate the applied steps and return the terminal checkpoint (fail-closed)."""
    try:
        cp = await _compensate(saga, cp, applied)
    except CompensatorFailed:
        # fail-closed: a failed undo => FAILED, never a clean COMPENSATED.
        return _with_state(cp, SagaState.FAILED)
    return _with_state(cp, terminal)


async def _noop_child() -> None:
    """A trivial structured child task used to exercise scope ownership/joining."""
    return None


def _with_state(cp: Checkpoint, state: SagaState) -> Checkpoint:
    """Return ``cp`` with its ``state`` field set (immutable update)."""
    return Checkpoint(
        goal_verbatim=cp.goal_verbatim,
        saga_step=cp.saga_step,
        replay_log=cp.replay_log,
        state=state,
    )


def run_saga(
    saga: Saga,
    adapter: RuntimeAdapter,
    checkpoint: Checkpoint,
) -> Checkpoint:
    """Run ``saga`` on ``adapter`` from ``checkpoint``; return the terminal checkpoint.

    Synchronous entry point: it enters the adapter's event loop via ``run`` and
    returns the terminal checkpoint (state ``COMMITTED`` on success, ``COMPENSATED``
    after an abort/cancel rollback, or ``FAILED`` if a compensator failed). The
    consistent, durable checkpoint is always returned for the caller/audit.
    """

    async def _main() -> Checkpoint:
        return await _drive(saga, adapter, checkpoint)

    return adapter.run(_main)
