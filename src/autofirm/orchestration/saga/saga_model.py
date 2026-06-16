"""Runtime-agnostic saga model: steps, compensators, checkpoint, replay log.

What this does
--------------
Defines the pure, synchronous, runtime-independent data model for a *saga* — an
ordered list of locally-atomic steps, each pairing a **forward action** with a
**compensator** (semantic undo), plus the durable **checkpoint** and
**idempotent replay log** that let a crashed run resume without double-applying
side effects. This mirrors the ratified contract in ``data-contracts.md`` §4
(``Checkpoint`` / ``Compensator`` / ``IdempotentEvent``) and the A3 synthesis
(saga = forward + semantic compensation; coordinated checkpoint; idempotent
replay; "no orphan messages; every forward action has a registered compensator;
replay never double-applies").

Why it exists / where it sits
-----------------------------
The concurrency-runtime bake-off (ADR-001 §7) swaps *only* the async executor
underneath this model. Keeping the saga semantics here — written once, pure, and
runtime-free — is what makes the asyncio/AnyIO/Trio comparison apples-to-apples:
the only thing that varies between candidates is *how cancellation and child
tasks are expressed*, not what "exactly-once compensation" or "idempotent replay"
mean. Those invariants are defined and enforced here so every runtime inherits
them identically.

Security / compliance invariants upheld
---------------------------------------
Fail-closed (CLAUDE.md §5.6): a step *must* register a compensator — a saga with a
missing compensator is refused at construction with ``ValueError`` rather than
silently allowing an un-undoable forward action (``data-contracts.md`` §4: "fail-
closed if missing"). Idempotency keys are required on every side-effecting event
so replay can never double-apply (the A3 idempotency-key defense). The model is
pure and append-only — the replay log is never rewritten, mirroring the audit-log
append-only invariant already on ``main`` (A6).
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field, replace
from enum import StrEnum

__all__ = [
    "Checkpoint",
    "Saga",
    "SagaAbort",
    "SagaState",
    "Step",
    "make_checkpoint",
    "record_compensated",
    "record_forward",
]


class SagaAbort(Exception):
    """Raised by a forward action to request an orderly compensating rollback.

    This is a *business* abort (the step decided the saga cannot proceed), as
    opposed to a cancellation (an external stop) or a crash (process death). All
    three must leave the saga consistent; this one is the in-band, voluntary path.
    """


class SagaState(StrEnum):
    """Terminal/in-progress states of a saga run (deterministic, exhaustive)."""

    PENDING = "pending"
    RUNNING = "running"
    COMMITTED = "committed"  # all forward actions applied, none compensated
    COMPENSATED = "compensated"  # rolled back to a consistent state
    FAILED = "failed"  # a compensator itself failed -> needs operator (fail-closed)


# A forward action takes the immutable saga context and returns nothing; it
# performs its side effect via the supplied effect-recorder (see executor). A
# compensator semantically undoes a *previously applied* forward action.
ForwardAction = Callable[["StepContext"], Awaitable[None]]
Compensator = Callable[["StepContext"], Awaitable[None]]


def _no_cancel() -> None:
    """Default no-op cancel hook for forward actions that never self-cancel."""


async def _no_checkpoint() -> None:
    """Default no-op checkpoint hook for forward actions that never yield."""


@dataclass(frozen=True, slots=True)
class StepContext:
    """Immutable per-step context handed to forward actions and compensators.

    ``idempotency_key`` is the stable key for this step's side effect: a forward
    action consults the replay log (via ``already_applied``) and skips re-applying
    if the key is already present — the A3 "replay never double-applies" defense.
    ``request_cancel`` fires a *real* cancellation of the enclosing structured
    scope (used by tests/operations to interrupt a saga mid-flight); it defaults to
    a no-op so normal forward actions never need it.
    """

    step_name: str
    idempotency_key: str
    already_applied: bool
    request_cancel: Callable[[], None] = _no_cancel
    checkpoint: Callable[[], Awaitable[None]] = _no_checkpoint


@dataclass(frozen=True, slots=True)
class Step:
    """One locally-atomic saga step: a forward action + its semantic compensator.

    ``name`` is unique within a saga and is the stable idempotency key seed, so
    replay is deterministic. ``compensator`` is mandatory (fail-closed).
    """

    name: str
    forward: ForwardAction
    compensator: Compensator


@dataclass(frozen=True, slots=True)
class IdempotentEvent:
    """A recorded side effect carrying its idempotency key (``data-contracts`` §4)."""

    idempotency_key: str
    step_name: str
    applied: bool


@dataclass(frozen=True, slots=True)
class Checkpoint:
    """Durable saga checkpoint — the resume anchor (``data-contracts.md`` §4).

    Holds the verbatim goal (re-injected on resume, never re-inferred — A3 src 07),
    the index of the next step to run (``saga_step``), and the append-only
    ``replay_log`` of idempotent events. A resumed run replays from step 0 but
    every already-applied forward action is short-circuited by its key, so the
    final state is identical to a clean run.
    """

    goal_verbatim: str
    saga_step: int  # SO: index of the next forward step to attempt
    replay_log: tuple[IdempotentEvent, ...] = field(default_factory=tuple)
    state: SagaState = SagaState.PENDING

    def already_applied(self, key: str) -> bool:
        """Return True if a forward effect with ``key`` is already in the log.

        This is the single source of truth for idempotent replay: a forward
        action whose key is present must NOT run again (no double-apply).
        """
        return any(ev.idempotency_key == key and ev.applied for ev in self.replay_log)

    def compensated_keys(self) -> frozenset[str]:
        """Keys whose compensator has already run (so it never runs twice)."""
        return frozenset(ev.idempotency_key for ev in self.replay_log if not ev.applied)


@dataclass(frozen=True, slots=True)
class Saga:
    """An ordered, validated list of steps with mandatory compensators.

    Construction is fail-closed: duplicate step names or a missing compensator
    raise ``ValueError`` (``data-contracts.md`` §4 — every forward action must
    have a registered compensator). The class is immutable; runtime executors
    consume it without mutating it.
    """

    name: str
    steps: tuple[Step, ...]

    def __post_init__(self) -> None:
        """Validate the saga at construction (fail-closed — CLAUDE.md §5.6)."""
        if not self.steps:
            raise ValueError("saga must have at least one step")  # fail-closed
        seen: set[str] = set()
        for step in self.steps:
            if not callable(step.compensator):
                # fail-closed: a forward action with no registered (callable)
                # compensator is refused — it could never be safely undone
                # (data-contracts §4). Guards against a None/non-callable passed at
                # runtime despite the type annotation.
                raise ValueError(f"step {step.name!r} has no compensator")
            if step.name in seen:
                # fail-closed: duplicate names break idempotency-key determinism.
                raise ValueError(f"duplicate step name {step.name!r}")
            seen.add(step.name)

    def idempotency_key(self, step_name: str) -> str:
        """Deterministic idempotency key for a step (stable across resumes)."""
        return f"{self.name}::{step_name}"


def make_checkpoint(goal: str) -> Checkpoint:
    """Create the initial checkpoint for a saga run (verbatim goal, step 0)."""
    if not goal:
        raise ValueError("goal_verbatim must be non-empty")  # fail-closed: re-grounding
    return Checkpoint(goal_verbatim=goal, saga_step=0)


def record_forward(cp: Checkpoint, key: str, step_name: str, next_step: int) -> Checkpoint:
    """Append a forward-applied event and advance ``saga_step`` (append-only).

    Returns a NEW checkpoint (the model is immutable); the replay log is only ever
    extended, never rewritten — mirroring the A6 append-only audit invariant.
    """
    event = IdempotentEvent(idempotency_key=key, step_name=step_name, applied=True)
    return replace(cp, replay_log=(*cp.replay_log, event), saga_step=next_step)


def record_compensated(cp: Checkpoint, key: str, step_name: str) -> Checkpoint:
    """Append a compensated event (``applied=False``) for a step's undo (append-only)."""
    event = IdempotentEvent(idempotency_key=key, step_name=step_name, applied=False)
    return replace(cp, replay_log=(*cp.replay_log, event))
