"""Synthetic, instrumented saga builders for the concurrency bake-off tests.

What this provides
------------------
Deterministic, side-effect-free saga fixtures whose forward actions and
compensators record their calls into an in-memory ledger, plus fault injectors
that trigger a cancel or a crash at a chosen step boundary *or* mid-step. No
network, no real I/O, no real PII — synthetic only (CLAUDE.md §5.5/§3.12).

Cancellation model (runtime-agnostic, deterministic)
----------------------------------------------------
Cancellation is injected via a *real* scope cancel (``ctx.request_cancel``), not
by raising the runtime's cancel exception by hand — Trio forbids the latter
(``trio.Cancelled`` may only originate from a cancel scope), so the real-cancel
path is the only faithful, apples-to-apples injection across all three runtimes.
A forward action can land the cancel mid-step (deliver at ``ctx.checkpoint``
BEFORE its effect) or at the boundary (apply its effect, then let the cancel fire
at the next step boundary) — both reproducible at any step offset.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from autofirm.orchestration.saga.saga_model import (
    Saga,
    SagaAbort,
    Step,
    StepContext,
)


@dataclass
class Ledger:
    """Records forward/compensate calls so tests can assert exactly-once semantics."""

    forwards: list[str] = field(default_factory=list)
    compensations: list[str] = field(default_factory=list)
    children_seen: int = 0

    def forward_count(self, name: str) -> int:
        """How many times step ``name``'s forward action actually applied."""
        return self.forwards.count(name)

    def compensate_count(self, name: str) -> int:
        """How many times step ``name``'s compensator ran."""
        return self.compensations.count(name)


@dataclass
class FaultPlan:
    """Where to inject a fault during the forward pass.

    ``cancel_at_step``  : raise the adapter's cancel when this step's forward runs.
    ``abort_at_step``   : raise SagaAbort (voluntary business rollback) at this step.
    ``mid_step``        : if True, sleep (a cancellation point) BEFORE raising, so the
                          fault lands "mid-step" rather than at the boundary.
    """

    cancel_at_step: int | None = None
    abort_at_step: int | None = None
    mid_step: bool = False


def build_saga(
    name: str,
    step_names: list[str],
    ledger: Ledger,
    plan: FaultPlan | None = None,
) -> Saga:
    """Build an instrumented saga over ``step_names`` with optional fault injection."""
    plan = plan or FaultPlan()
    steps: list[Step] = []
    for index, step_name in enumerate(step_names):
        steps.append(
            Step(
                name=step_name,
                forward=_make_forward(index, step_name, ledger, plan),
                compensator=_make_compensator(step_name, ledger),
            )
        )
    return Saga(name=name, steps=tuple(steps))


def _make_forward(
    index: int,
    step_name: str,
    ledger: Ledger,
    plan: FaultPlan,
):
    async def _forward(ctx: StepContext) -> None:
        if index == plan.abort_at_step:
            # Voluntary business abort BEFORE applying this step's effect.
            raise SagaAbort(step_name)
        if index == plan.cancel_at_step:
            # Fire a REAL cancellation of the enclosing structured scope (the only
            # faithful cancel path — Trio forbids raising trio.Cancelled by hand).
            ctx.request_cancel()
            if plan.mid_step:
                # Mid-step: deliver the cancel at a checkpoint BEFORE this step's
                # effect is applied -> this step is never recorded/compensated.
                await ctx.checkpoint()
            else:
                # Boundary: apply this step's effect first, then let the cancel be
                # delivered at the NEXT step-boundary checkpoint -> this step IS
                # applied and must be compensated exactly once.
                ledger.forwards.append(step_name)
            return
        ledger.forwards.append(step_name)

    return _forward


def _make_compensator(step_name: str, ledger: Ledger):
    async def _compensator(ctx: StepContext) -> None:
        ledger.compensations.append(step_name)

    return _compensator
