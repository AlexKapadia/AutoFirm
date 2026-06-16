"""The context-window budget a session consumes, with a fail-closed exhaustion gate.

What this does
--------------
Defines :class:`ContextBudgetState` — the deterministic model of how much of a
session's finite context window has been consumed. It tracks ``limit_tokens``
(the window size), ``consumed_tokens`` (used so far), and a ``handoff_threshold``
(the fraction at which a handoff to a fresh session must be triggered, *before*
the hard limit, so the outgoing session still has room to write its handoff
summary). It exposes pure predicates — :meth:`is_exhausted`,
:meth:`remaining_tokens` — and a pure :meth:`consume` that returns a new state
(frozen / immutable, so budget accounting is replayable).

Why it exists / where it sits
-----------------------------
A3 SYNTHESIS L1.A3.2: long-horizon failure is dominated by memory/context loss;
the mandate is to checkpoint and hand off *before* the window is lost, never to
let a session silently drift as it fills. A5 SYNTHESIS §1: context windows are
finite and per-session. This type makes "is it time to hand off?" a
deterministic, boundary-exact decision instead of a guess, so the lifecycle
engine triggers handoff at a predictable, tested point.

Security / compliance invariants upheld
---------------------------------------
* **Determinism (§3.11):** budget is pure data; ``consume`` is a total function
  with no I/O, so a sequence of consumptions replays identically.
* **Fail-closed (§5.6):** an over-consumption (more than remains) is *clamped to
  full*, not allowed to wrap negative — an exhausted budget can never look
  un-exhausted. Invalid construction (non-positive limit, threshold outside
  ``(0, 1]``) is refused.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

__all__ = ["ContextBudgetState"]


class ContextBudgetState(BaseModel):
    """Immutable accounting of one session's context-window consumption.

    A handoff is required once consumption reaches ``handoff_threshold`` of the
    limit (see :meth:`is_exhausted`), which is set below ``1.0`` so the outgoing
    session retains headroom to serialize its handoff summary before the hard
    window limit.
    """

    model_config = ConfigDict(frozen=True)

    limit_tokens: int  # total context-window size for this session (> 0)
    consumed_tokens: int  # tokens used so far (0 <= consumed <= limit)
    handoff_threshold: float  # fraction in (0, 1] at which handoff is forced

    @field_validator("limit_tokens")
    @classmethod
    def _positive_limit(cls, value: int) -> int:
        # fail-closed: a zero/negative window is not a usable budget -> refuse it,
        # so a session can never be modelled as having no context at all.
        if value <= 0:
            raise ValueError("limit_tokens must be positive")
        return value

    @field_validator("consumed_tokens")
    @classmethod
    def _non_negative_consumed(cls, value: int) -> int:
        # fail-closed: negative consumption is nonsensical and could mask exhaustion.
        if value < 0:
            raise ValueError("consumed_tokens must be >= 0")
        return value

    @field_validator("handoff_threshold")
    @classmethod
    def _threshold_in_range(cls, value: float) -> float:
        # fail-closed: a threshold of 0 would hand off immediately and a threshold
        # above 1 could never fire before the hard limit -> refuse both.
        if not (0.0 < value <= 1.0):
            raise ValueError("handoff_threshold must be in (0, 1]")
        return value

    @model_validator(mode="after")
    def _consumed_within_limit(self) -> ContextBudgetState:
        # fail-closed: consumed can never exceed the window; an out-of-range state
        # is refused so callers can rely on 0 <= consumed <= limit everywhere.
        if self.consumed_tokens > self.limit_tokens:
            raise ValueError("consumed_tokens cannot exceed limit_tokens")
        return self

    def remaining_tokens(self) -> int:
        """Return the unused budget (never negative)."""
        return self.limit_tokens - self.consumed_tokens

    def is_exhausted(self) -> bool:
        """Return True iff consumption has reached the handoff threshold.

        Boundary-exact: uses ``>=`` against the threshold token count, so the
        exact threshold instant already requires a handoff. Computed in integer
        token space (``ceil`` of ``threshold * limit``) to keep the decision
        deterministic and free of float drift at the boundary.
        """
        # ceil(threshold * limit) without importing math: integer arithmetic only,
        # so the threshold token count is exact and reproducible.
        scaled = self.handoff_threshold * self.limit_tokens
        threshold_tokens = int(scaled)
        if threshold_tokens < scaled:  # there was a fractional part -> round up
            threshold_tokens += 1
        # fail-closed handoff: at or past the threshold, the session MUST hand off.
        return self.consumed_tokens >= threshold_tokens

    def consume(self, tokens: int) -> ContextBudgetState:
        """Return a new state with ``tokens`` more consumed (clamped at the limit).

        Over-consumption is *clamped to the full limit* rather than allowed to
        exceed it: an exhausted budget must never wrap to look un-exhausted
        (fail-closed). ``tokens`` must be non-negative.
        """
        if tokens < 0:
            raise ValueError("cannot consume a negative number of tokens")  # fail-closed
        # clamp at the limit so consumed in [0, limit] is an enforced invariant.
        new_consumed = min(self.consumed_tokens + tokens, self.limit_tokens)
        return self.model_copy(update={"consumed_tokens": new_consumed})
