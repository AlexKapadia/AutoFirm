"""The append-only, gapless provenance trail of a work item's flow transitions.

What this does
--------------
Defines :class:`FlowTransition` — one immutable record of a single state change
(from-state, to-state, from-role, to-role, reason, injected timestamp, gapless
seq) — and :class:`FlowTrail`, the strictly append-only log that holds them. The
trail is the complete, replayable provenance of how a work item moved through the
org: who handed it to whom, when, and why. Every transition is recorded *with*
the state change, so the trail is gapless and complete by construction.

Why it exists / where it sits
-----------------------------
Realises "everything flows" as an audited primitive and mirrors the append-only
discipline already on ``main`` (``autofirm.org.org_lifecycle_events.OrgAuditTrail``
and the Merkle audit log): the trail only ever grows, sequence numbers are gapless
and monotonic, and no API exposes update or delete. The work item owns one of
these; the orchestrator can mirror each transition into the Merkle audit sink at
the composition root.

Security / compliance invariants upheld
---------------------------------------
* **Append-only (CLAUDE.md §5.6 / §3.8):** :meth:`FlowTrail.append` returns a NEW
  trail with the transition added; there is no mutate/delete path.
* **Gapless monotonic seq:** each transition's ``seq`` is exactly the current
  length; a gap, duplicate, or out-of-order insert is refused (fail-closed), so a
  dropped or rewritten step is detectable.
* **Complete provenance:** every transition carries both endpoints, both roles,
  and a non-empty reason — a transition with a blank reason is refused, so the
  trail can never record an unexplained move (explain-every-decision, §3.11).
* **Immutable records:** each :class:`FlowTransition` is frozen.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator

from autofirm.flow.flow_state_machine import WorkState

__all__ = ["FlowTrail", "FlowTransition"]


class FlowTransition(BaseModel):
    """One immutable, sequence-numbered record of a single flow transition.

    ``from_role`` is ``None`` only for the very first transition that brings a
    just-created item under its first owner (CREATED has no prior owner). Every
    other transition names both the relinquishing and the receiving role, so the
    handoff chain is fully traceable.
    """

    model_config = ConfigDict(frozen=True)

    seq: int  # gapless monotonic counter (== position in the trail)
    from_state: WorkState
    to_state: WorkState
    from_role: str | None  # the role relinquishing work (None on first assignment)
    to_role: str  # the role the work moves to (always named — no anonymous owner)
    reason: str  # why this move happened (deterministic, PII-free, non-empty)
    timestamp: datetime  # from the injected FlowClock (deterministic)

    @field_validator("seq")
    @classmethod
    def _seq_non_negative(cls, value: int) -> int:
        # fail-closed: sequence numbers are non-negative monotonic counters.
        if value < 0:
            raise ValueError("seq must be >= 0 (gapless monotonic counter)")
        return value

    @field_validator("to_role", "reason")
    @classmethod
    def _required_text_non_empty(cls, value: str) -> str:
        # fail-closed: an anonymous recipient or an unexplained move would break
        # provenance completeness — refuse a blank to_role or reason (§3.11).
        if not value.strip():
            raise ValueError("to_role and reason must be non-empty (complete provenance)")
        return value


class FlowTrail(BaseModel):
    """An append-only, gapless log of :class:`FlowTransition` records.

    Immutable: :meth:`append` returns a new trail; there is no update or delete
    API (append-only, CLAUDE.md §5.6 / §3.8). This is the single source of truth
    for *how* a work item reached its current state.
    """

    model_config = ConfigDict(frozen=True)

    transitions: tuple[FlowTransition, ...] = ()

    def append(self, transition: FlowTransition) -> FlowTrail:
        """Return a NEW trail with ``transition`` appended (append-only).

        Fail-closed: the transition's ``seq`` must equal the current length, so
        the log is gapless and strictly ordered — a caller cannot insert, skip,
        or overwrite a sequence number (which would let history be rewritten).
        """
        if transition.seq != len(self.transitions):
            # fail-closed: a non-consecutive seq would create a gap or overwrite,
            # breaking the append-only / gapless invariant (§5.6). Refuse it.
            raise ValueError(
                f"non-consecutive flow seq: expected {len(self.transitions)}, "
                f"got {transition.seq}"
            )
        return FlowTrail(transitions=(*self.transitions, transition))

    @property
    def next_seq(self) -> int:
        """The seq the next appended transition must carry (== current length)."""
        return len(self.transitions)

    def is_gapless(self) -> bool:
        """Return True iff the recorded seqs are exactly ``0..n-1`` in order.

        A structural self-check the invariant tests assert against: the trail is
        complete (no missing step) and ordered (no reordering).
        """
        return tuple(t.seq for t in self.transitions) == tuple(range(len(self.transitions)))
