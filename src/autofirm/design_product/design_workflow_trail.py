"""The append-only, gapless, legal-only trail of a design effort's stage changes.

What this does
--------------
Defines :class:`DesignStageTransition` — one immutable record of a single design
stage change (from-stage, to-stage, actor role, reason, injected timestamp,
gapless seq) — and :class:`DesignWorkflowTrail`, the strictly append-only log
that holds them and **enforces the state machine on every append**. The trail is
the complete, replayable provenance of how a client design effort moved from
brief to done (or rejection): who acted, when, why, and that every step was a
legal transition.

Why it exists / where it sits
-----------------------------
It composes :mod:`~autofirm.design_product.design_workflow_state_machine` (the
legal-edge authority) with the append-only / gapless discipline of
:mod:`autofirm.flow.work_item_flow_trail`. The difference from a bare table is
that this trail is what makes the workflow a *running* state machine: appending a
transition is the only way to advance, and an illegal or non-consecutive step is
refused — so the trail cannot record a stage jump or a rewritten history.

Security / compliance invariants upheld
---------------------------------------
* **Legal-only transitions (fail-closed, §4.9.5 / §5.6):** :meth:`advance`
  refuses any transition not in ``ALLOWED_DESIGN_TRANSITIONS`` — in particular a
  BUILDING -> DONE self-certification — and refuses advancing from a terminal
  stage. The build can never ship without passing through a separate review.
* **Append-only (§5.6 / §3.8):** :meth:`advance` returns a NEW trail; there is no
  mutate/delete path, so history only ever grows.
* **Gapless monotonic seq:** each transition's ``seq`` is exactly the current
  length; a gap, duplicate, or reorder is refused, so a dropped or rewritten
  stage is detectable.
* **Complete provenance:** every transition carries the acting role and a
  non-empty reason — an unexplained stage change is refused (§3.11).
* **Immutable records:** each :class:`DesignStageTransition` is frozen.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator

from autofirm.design_product.design_workflow_state_machine import (
    DesignStage,
    is_allowed_design_transition,
    is_design_terminal,
)

__all__ = ["DesignStageTransition", "DesignWorkflowTrail"]


class DesignStageTransition(BaseModel):
    """One immutable, sequence-numbered record of a single design stage change.

    Carries the acting role and a non-empty reason so every stage change is
    attributable and explained (§3.11). The ``from_stage``/``to_stage`` pair is
    validated against the state machine by the trail at append time, not here.
    """

    model_config = ConfigDict(frozen=True)

    seq: int  # gapless monotonic counter (== position in the trail)
    from_stage: DesignStage
    to_stage: DesignStage
    actor_role: str  # the role that performed this transition (always named)
    reason: str  # why this stage change happened (deterministic, PII-free, non-empty)
    timestamp: datetime  # from the injected Clock (deterministic, never ambient)

    @field_validator("seq")
    @classmethod
    def _seq_non_negative(cls, value: int) -> int:
        # fail-closed: sequence numbers are non-negative monotonic counters.
        if value < 0:
            raise ValueError("seq must be >= 0 (gapless monotonic counter)")
        return value

    @field_validator("actor_role", "reason")
    @classmethod
    def _required_text_non_empty(cls, value: str) -> str:
        # fail-closed: an anonymous actor or an unexplained stage change would break
        # provenance completeness — refuse a blank actor_role or reason (§3.11).
        if not value.strip():
            raise ValueError("actor_role and reason must be non-empty (complete provenance)")
        return value


class DesignWorkflowTrail(BaseModel):
    """An append-only, gapless, legal-only log of design stage transitions.

    Immutable: :meth:`advance` returns a new trail; there is no update or delete
    API. The trail starts at :data:`DesignStage.DESIGN_BRIEF` and is the single
    source of truth for *how* a client design effort reached its current stage —
    and that every step along the way was a legal, reviewed transition.
    """

    model_config = ConfigDict(frozen=True)

    transitions: tuple[DesignStageTransition, ...] = ()

    @property
    def current_stage(self) -> DesignStage:
        """The stage the effort is in now (DESIGN_BRIEF before any transition)."""
        if not self.transitions:
            return DesignStage.DESIGN_BRIEF
        return self.transitions[-1].to_stage

    @property
    def next_seq(self) -> int:
        """The seq the next appended transition must carry (== current length)."""
        return len(self.transitions)

    def advance(self, *, to_stage: DesignStage, actor_role: str, reason: str, at: datetime) -> (
        DesignWorkflowTrail
    ):
        """Return a NEW trail advanced to ``to_stage`` (the only way to progress).

        Fail-closed on three independent guards, in order:

        1. **Not terminal:** if the current stage is a sink (DONE/REJECTED), no
           further advance is allowed — a shipped or abandoned effort is final.
        2. **Legal edge:** the ``current_stage -> to_stage`` transition must be in
           the state machine, so a build can never jump to DONE without a separate
           review (§4.9.5 generator/evaluator split).
        3. **Gapless append:** the new transition's seq is exactly the current
           length, so history is strictly ordered and cannot be rewritten.

        Args:
            to_stage: The stage to advance to.
            actor_role: The role performing the transition (recorded, non-empty).
            reason: Why the transition happens (recorded, non-empty).
            at: The injected timestamp (deterministic, never ``datetime.now()``).

        Returns:
            A new :class:`DesignWorkflowTrail` with the transition appended.

        Raises:
            ValueError: if the current stage is terminal, or the transition is
                illegal — fail-closed.
        """
        source = self.current_stage
        if is_design_terminal(source):
            # fail-closed: DONE/REJECTED are sinks; advancing past them would
            # silently reopen a finished effort. Refuse it (§4.9.5).
            raise ValueError(f"cannot advance from terminal stage {source.value}")
        if not is_allowed_design_transition(source, to_stage):
            # fail-closed: an edge absent from the machine (e.g. BUILDING -> DONE)
            # would skip the separate review. Refuse the illegal transition.
            raise ValueError(f"illegal design transition: {source.value} -> {to_stage.value}")
        transition = DesignStageTransition(
            seq=len(self.transitions),  # gapless: exactly the current length
            from_stage=source,
            to_stage=to_stage,
            actor_role=actor_role,
            reason=reason,
            timestamp=at,
        )
        return DesignWorkflowTrail(transitions=(*self.transitions, transition))

    def is_gapless(self) -> bool:
        """Return True iff the recorded seqs are exactly ``0..n-1`` in order.

        A structural self-check the invariant tests assert against: the trail is
        complete (no missing stage) and ordered (no reordering).
        """
        return tuple(t.seq for t in self.transitions) == tuple(range(len(self.transitions)))
