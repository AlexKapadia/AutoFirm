"""The design/product workflow state machine: brief -> build -> review -> done.

What this does
--------------
Defines :class:`DesignStage` — the deterministic lifecycle of a client design/
product effort — and the **single source of truth for which stage transitions
are legal** (:data:`ALLOWED_DESIGN_TRANSITIONS`). It mirrors the §4.9 pipeline
(brief -> fan-out build -> visual review -> Definition-of-Done) AND its
**generator/evaluator split (§4.9.5)**: BUILDING (the generator) and
VISUAL_REVIEW (a SEPARATE evaluator) are distinct stages, and the only way to
reach DONE is *through* a passing review — a build can never self-certify as
done.

Why it exists / where it sits
-----------------------------
This is the design-specific analogue of
:mod:`autofirm.flow.flow_state_machine`: a pure, deterministic transition table
(``is_allowed_design_transition`` is a total function of its two inputs) that the
:mod:`~autofirm.design_product.design_workflow_trail` and the property tests
consult as the single authority. Keeping the legal edges in one frozen table
(not scattered ``if``s) is what lets the tests drive arbitrary stage sequences
and assert "no illegal transition is ever accepted".

Security / compliance invariants upheld
---------------------------------------
* **Closed transition set (fail-closed, §5.6):** an edge absent from
  :data:`ALLOWED_DESIGN_TRANSITIONS` is illegal by default — deny by omission.
* **Generator/evaluator separation (§4.9.5):** there is **no** BUILDING -> DONE
  edge. DONE is reachable only via VISUAL_REVIEW -> DONE, so a self-reviewing
  build cannot ship — the judge is always a separate stage.
* **No skipped stages:** edges only wire adjacent steps, so a brief cannot jump
  straight to DONE without being built and reviewed.
* **Review can bounce back:** VISUAL_REVIEW -> BUILDING lets a failing review
  send work back (the iterate-to-perfection loop, §3.7) rather than forcing a
  pass — refusal is a first-class outcome.
* **Terminal stages are sinks:** DONE (shipped) and REJECTED (abandoned) have no
  outgoing edges; neither is silently reopened.
"""

from __future__ import annotations

from enum import StrEnum

__all__ = [
    "ALLOWED_DESIGN_TRANSITIONS",
    "DESIGN_TERMINAL_STAGES",
    "DesignStage",
    "is_allowed_design_transition",
    "is_design_terminal",
]


class DesignStage(StrEnum):
    """The exhaustive deterministic lifecycle of a client design/product effort.

    Ordered by flow: a DESIGN_BRIEF is authored, the work is BUILDING (the
    generator stage, §4.9.3 fan-out), it enters VISUAL_REVIEW (the SEPARATE
    evaluator stage, §4.9.5), and ends either DONE (passed the Definition-of-Done
    and shipped) or REJECTED (abandoned). Review may bounce work back to BUILDING.
    """

    DESIGN_BRIEF = "DESIGN_BRIEF"  # the brief is authored (the build contract)
    BUILDING = "BUILDING"  # generator: UI/product built against the brief
    VISUAL_REVIEW = "VISUAL_REVIEW"  # evaluator: a SEPARATE agent judges the build
    DONE = "DONE"  # passed the UI Definition-of-Done — shipped (terminal sink)
    REJECTED = "REJECTED"  # abandoned (terminal sink — never silently reopened)


# The closed set of legal directed stage edges. Anything NOT listed is illegal by
# default (fail-closed). Crucially there is NO (BUILDING -> DONE) edge: DONE is
# reachable only through VISUAL_REVIEW, enforcing the generator/evaluator split.
ALLOWED_DESIGN_TRANSITIONS: frozenset[tuple[DesignStage, DesignStage]] = frozenset(
    {
        (DesignStage.DESIGN_BRIEF, DesignStage.BUILDING),  # brief approved -> build
        (DesignStage.DESIGN_BRIEF, DesignStage.REJECTED),  # brief killed before build
        (DesignStage.BUILDING, DesignStage.VISUAL_REVIEW),  # build -> SEPARATE review
        (DesignStage.BUILDING, DesignStage.REJECTED),  # build abandoned
        # The evaluator either ships it or bounces it back to the generator:
        (DesignStage.VISUAL_REVIEW, DesignStage.DONE),  # passed the DoD -> ship
        (DesignStage.VISUAL_REVIEW, DesignStage.BUILDING),  # failed review -> rebuild
        (DesignStage.VISUAL_REVIEW, DesignStage.REJECTED),  # review abandons the effort
    }
)

# Stages with no outgoing edge: a work item that reaches one can make no further
# transition. DONE and REJECTED are the two terminal sinks.
DESIGN_TERMINAL_STAGES: frozenset[DesignStage] = frozenset(
    {
        stage
        for stage in DesignStage
        if not any(src == stage for src, _ in ALLOWED_DESIGN_TRANSITIONS)
    }
)


def is_allowed_design_transition(source: DesignStage, target: DesignStage) -> bool:
    """Return True iff ``source -> target`` is a legal edge in the design machine.

    A total, deterministic function of its two inputs — the single authority every
    caller (the workflow trail, the property tests) consults. An edge absent from
    :data:`ALLOWED_DESIGN_TRANSITIONS` returns False (fail-closed). In particular
    ``is_allowed_design_transition(BUILDING, DONE)`` is always ``False`` — a build
    cannot ship without a separate review (§4.9.5).

    Args:
        source: The current design stage.
        target: The proposed next stage.

    Returns:
        True if the transition is permitted, False otherwise.
    """
    return (source, target) in ALLOWED_DESIGN_TRANSITIONS


def is_design_terminal(stage: DesignStage) -> bool:
    """Return True iff ``stage`` has no outgoing transition (a workflow sink)."""
    return stage in DESIGN_TERMINAL_STAGES
