"""Mutation-hardening tests for the pure saga model (contract + immutability).

These pin the *observable contract* of ``saga_model`` so the mutation gate has no
gaps on the data model the executor and audit log depend on (CLAUDE.md §3.6;
ADR-001 §3 step 6): the exact serialized enum values (what lands in the durable
checkpoint / audit record), dataclass immutability + slots (the append-only,
no-rewrite invariant — A6), the StepContext default hooks being real callables
(not ``None``), and the EXACT fail-closed ``ValueError`` messages and initial
``saga_step``. Synthetic only; no network.

Why exact-string asserts (not ``pytest.raises(match=...)``): a ``match`` is a
regex *search*, so a mutant that wraps the whole message (``"msg"`` -> ``"XXmsgXX"``)
still contains the searched substring and survives. Asserting ``str(exc) == "msg"``
kills that mutant class.
"""

from __future__ import annotations

import dataclasses

import pytest

from autofirm.orchestration.saga.saga_model import (
    Checkpoint,
    IdempotentEvent,
    Saga,
    SagaState,
    Step,
    StepContext,
    make_checkpoint,
    record_forward,
)


async def _ok_forward(ctx: StepContext) -> None:
    return None


async def _ok_comp(ctx: StepContext) -> None:
    return None


# --------------------------------------------------------------------------- #
# Enum values are part of the serialized contract (checkpoint / audit record).  #
# Pinning .value kills the string-literal mutants on every member.              #
# --------------------------------------------------------------------------- #


@pytest.mark.unit
def test_saga_state_values_are_exact_serialized_strings() -> None:
    # These strings are persisted into the durable checkpoint and the audit log,
    # so their exact spelling is a contract — not an implementation detail.
    assert SagaState.PENDING.value == "pending"
    assert SagaState.RUNNING.value == "running"
    assert SagaState.COMMITTED.value == "committed"
    assert SagaState.COMPENSATED.value == "compensated"
    assert SagaState.FAILED.value == "failed"
    # Exhaustive: exactly these five states exist (guards an added/renamed member).
    assert {s.value for s in SagaState} == {
        "pending",
        "running",
        "committed",
        "compensated",
        "failed",
    }


# --------------------------------------------------------------------------- #
# Dataclass immutability + slots = the append-only / no-rewrite invariant (A6). #
# frozen=True must forbid mutation; slots=True must forbid stray attributes.     #
# --------------------------------------------------------------------------- #


def _one_of_each_model() -> list[tuple[object, str]]:
    """Build one instance of every model dataclass + a mutable attr name.

    Constructed INSIDE the test body (not in a @parametrize decorator) on purpose:
    a mutant that drops the ``@dataclass`` decorator removes the generated
    ``__init__``, so these constructor calls raise ``TypeError`` *during the test*
    (a clean exit-1 failure that mutmut scores as a KILL) rather than at collection
    time (exit-2, which mutmut mis-handles as a survivor).
    """
    return [
        (Checkpoint(goal_verbatim="g", saga_step=0), "saga_step"),
        (IdempotentEvent(idempotency_key="k", step_name="s", applied=True), "applied"),
        (Step(name="a", forward=_ok_forward, compensator=_ok_comp), "name"),
        (Saga(name="s", steps=(Step("a", _ok_forward, _ok_comp),)), "name"),
        (StepContext(step_name="a", idempotency_key="k", already_applied=False), "already_applied"),
    ]


@pytest.mark.unit
def test_model_dataclasses_are_frozen() -> None:
    # frozen=True: a write must raise (immutability => the replay log/checkpoint is
    # never rewritten in place). Kills frozen=True -> frozen=False AND the dropped
    # @dataclass decorator (no __init__ => TypeError building the instance).
    for instance, attr in _one_of_each_model():
        with pytest.raises(dataclasses.FrozenInstanceError):
            setattr(instance, attr, "mutated")


@pytest.mark.unit
def test_model_dataclasses_use_slots() -> None:
    # slots=True: a slotted instance has no __dict__ (compact, no stray attrs).
    # Kills the slots=True -> slots=False mutant (a non-slotted instance has one).
    for instance, _attr in _one_of_each_model():
        assert not hasattr(instance, "__dict__")


# --------------------------------------------------------------------------- #
# StepContext default hooks are real no-op callables, not None.                 #
# A compensator's StepContext is built WITHOUT these args, so the defaults must  #
# be callable (calling None would crash). Kills the default -> None mutants.     #
# --------------------------------------------------------------------------- #


@pytest.mark.unit
async def test_stepcontext_default_hooks_are_callable_noops() -> None:
    ctx = StepContext(step_name="a", idempotency_key="k", already_applied=True)
    # request_cancel default: a real no-op callable (returns None, never raises).
    assert ctx.request_cancel() is None
    # checkpoint default: a real awaitable no-op.
    assert await ctx.checkpoint() is None


# --------------------------------------------------------------------------- #
# Checkpoint / make_checkpoint defaults are exact.                              #
# --------------------------------------------------------------------------- #


@pytest.mark.unit
def test_checkpoint_default_state_is_pending() -> None:
    # Default state must be PENDING (kills state default -> None and the initial
    # run-state contract). make_checkpoint relies on this default.
    assert Checkpoint(goal_verbatim="g", saga_step=0).state is SagaState.PENDING


@pytest.mark.unit
def test_make_checkpoint_starts_at_step_zero() -> None:
    # The initial resume anchor points at step 0 (kills saga_step=0 -> 1): a fresh
    # saga must begin at the FIRST step, never skip step 0.
    cp = make_checkpoint("the goal")
    assert cp.saga_step == 0
    assert cp.goal_verbatim == "the goal"
    assert cp.state is SagaState.PENDING


# --------------------------------------------------------------------------- #
# Fail-closed ValueError messages are exact (kills whole-string-wrap mutants).  #
# --------------------------------------------------------------------------- #


@pytest.mark.unit
def test_empty_saga_error_message_is_exact() -> None:
    with pytest.raises(ValueError) as exc:
        Saga(name="e", steps=())
    assert str(exc.value) == "saga must have at least one step"


@pytest.mark.unit
def test_missing_compensator_error_message_is_exact() -> None:
    bad = Step(name="a", forward=_ok_forward, compensator=None)  # type: ignore[arg-type]
    with pytest.raises(ValueError) as exc:
        Saga(name="m", steps=(bad,))
    assert str(exc.value) == "step 'a' has no compensator"


@pytest.mark.unit
def test_duplicate_step_name_error_message_is_exact() -> None:
    s = Step(name="dup", forward=_ok_forward, compensator=_ok_comp)
    with pytest.raises(ValueError) as exc:
        Saga(name="d", steps=(s, s))
    assert str(exc.value) == "duplicate step name 'dup'"


@pytest.mark.unit
def test_empty_goal_error_message_is_exact() -> None:
    with pytest.raises(ValueError) as exc:
        make_checkpoint("")
    assert str(exc.value) == "goal_verbatim must be non-empty"


# --------------------------------------------------------------------------- #
# record_forward advances saga_step to the supplied next index (append-only).   #
# --------------------------------------------------------------------------- #


@pytest.mark.unit
def test_record_forward_sets_next_step_and_appends_event() -> None:
    cp = make_checkpoint("g")
    cp2 = record_forward(cp, "g::a", "a", 1)
    assert cp2.saga_step == 1
    assert cp2.replay_log[-1] == IdempotentEvent("g::a", "a", applied=True)
    assert cp.saga_step == 0  # original untouched (immutable update)
