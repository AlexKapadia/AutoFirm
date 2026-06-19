"""Frozen value types for the risk-scored approval decision (no logic, no I/O).

What this does
--------------
Defines the immutable inputs and output of the approval surface: :class:`RiskLevel`
(the overall severity of an action), :class:`ReversibilityClass` (can it be undone),
:class:`PendingAction` (the action awaiting a decision, carrying its risk attributes and
the :class:`~autofirm.cockpit.core.autonomy_tier_model.ActionKind` it falls under), and
:class:`ApprovalDecision` (the three-valued verdict). These are dumb, validated records;
all decision logic lives in :mod:`approval_risk_scorer`.

Why it exists / where it sits
-----------------------------
Splitting the data from the decision (cockpit-research/PLAN.md §1.1) keeps each file under
one responsibility and lets the scorer be a single pure function over these frozen types —
the mutation target. Sits in the pure core; depends only on :mod:`autonomy_tier_model`.

Security / compliance invariants upheld
---------------------------------------
* **Fail-closed construction (CLAUDE.md §5.6):** :class:`PendingAction` refuses to be built
  from a malformed risk level / reversibility / action kind — an ambiguous action cannot
  exist as a valid object, so the scorer never sees a half-specified input.
* **Immutability:** every type is frozen, so a decision is a deterministic function of
  values that cannot mutate between scoring and audit.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, IntEnum

from autofirm.cockpit.core.autonomy_tier_model import ActionKind

__all__ = [
    "ApprovalDecision",
    "PendingAction",
    "ReversibilityClass",
    "RiskLevel",
]


class RiskLevel(IntEnum):
    """The overall risk severity of a pending action, ordered low → high.

    ``IntEnum`` so severity comparisons (``>=``) in the scorer are exact and ordered.
    """

    LOW = 0
    MEDIUM = 1
    HIGH = 2
    CRITICAL = 3


class ReversibilityClass(Enum):
    """Whether the action's effect can be undone after it fires."""

    REVERSIBLE = "reversible"  # can be cleanly rolled back
    PARTIALLY_REVERSIBLE = "partially_reversible"  # rollback is lossy/incomplete
    IRREVERSIBLE = "irreversible"  # cannot be undone (publish, send, pay)


class ApprovalDecision(Enum):
    """The three-valued verdict for a pending action.

    There is no implicit fourth state: the scorer always returns exactly one of these.
    """

    AUTO_APPROVE = "auto_approve"  # the agent may proceed unattended
    REQUIRE_HUMAN = "require_human"  # a human must review before it proceeds
    REFUSE = "refuse"  # the action is refused outright (never auto, never queued to human)


@dataclass(frozen=True, slots=True)
class PendingAction:
    """An action awaiting an approval decision, with its validated risk attributes.

    The fields are the *only* inputs to the scorer. Construction is fail-closed: a
    malformed attribute raises, so a :class:`PendingAction` that exists is always fully and
    validly specified — the scorer never has to decide on an ambiguous record.

    Attributes:
        action_kind: The kind of action (drives the always-gated rules).
        risk_level: The overall assessed severity.
        reversibility: Whether the effect can be undone.
        requires_external_call: Whether it reaches outside AutoFirm (untrusted boundary).
        estimated_blast_radius: Count of entities/records the action would affect; must be
            ``>= 0`` (a negative blast radius is nonsense and is refused).
    """

    action_kind: ActionKind
    risk_level: RiskLevel
    reversibility: ReversibilityClass
    requires_external_call: bool
    estimated_blast_radius: int

    def __post_init__(self) -> None:
        """Validate every field fail-closed; a malformed action cannot be constructed.

        Raises:
            TypeError: If any field is the wrong type — an unknown risk level / action
                kind / reversibility must not masquerade as a valid input (the scorer
                would otherwise have to guess, and guessing on a security input is banned).
            ValueError: If ``estimated_blast_radius`` is negative.
        """
        # fail-closed: each enum field must be the exact enum — a bare int/str/None that
        # looked plausible must be refused, never coerced into a risk decision.
        if not isinstance(self.action_kind, ActionKind):
            raise TypeError("action_kind must be an ActionKind")
        if not isinstance(self.risk_level, RiskLevel):
            raise TypeError("risk_level must be a RiskLevel")
        if not isinstance(self.reversibility, ReversibilityClass):
            raise TypeError("reversibility must be a ReversibilityClass")
        # fail-closed: a non-bool external-call flag is ambiguous; refuse rather than
        # truthiness-test it (bool is a subclass of int, so this excludes 0/1/2 ints too).
        if not isinstance(self.requires_external_call, bool):
            raise TypeError("requires_external_call must be a bool")
        if not isinstance(self.estimated_blast_radius, bool) and isinstance(
            self.estimated_blast_radius, int
        ):
            if self.estimated_blast_radius < 0:  # fail-closed: blast radius cannot be negative
                raise ValueError("estimated_blast_radius must be >= 0")
        else:
            raise TypeError("estimated_blast_radius must be an int")
