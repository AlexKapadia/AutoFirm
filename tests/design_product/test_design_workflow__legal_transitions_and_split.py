"""Workflow tests: only legal stages, gapless audited trail, NO self-certified ship.

Proves the design state machine is the single legality authority and that the
§4.9.5 generator/evaluator split is structural, not advisory: there is NO
BUILDING->DONE edge, so a build can never ship without a SEPARATE VISUAL_REVIEW;
the trail refuses illegal transitions, advancing past a terminal stage, and any
non-gapless sequence, while keeping a complete, attributed, explained provenance.
Includes Hypothesis properties: (1) is_allowed_design_transition agrees with the
table exactly over arbitrary stage pairs, and (2) the trail's recorded path is
always a legal, gapless walk no matter what random legal advances are applied.
Synthetic only; no network.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from hypothesis import given
from hypothesis import strategies as st
from pydantic import ValidationError

from autofirm.design_product.design_workflow_state_machine import (
    ALLOWED_DESIGN_TRANSITIONS,
    DESIGN_TERMINAL_STAGES,
    DesignStage,
    is_allowed_design_transition,
    is_design_terminal,
)
from autofirm.design_product.design_workflow_trail import (
    DesignStageTransition,
    DesignWorkflowTrail,
)

_AT = datetime(2026, 1, 1, tzinfo=UTC)
_ALL_STAGES = list(DesignStage)
_stage = st.sampled_from(_ALL_STAGES)

# Edges that must NEVER be legal — the load-bearing one is the self-certify ship.
_FORBIDDEN_EDGES = [
    (DesignStage.BUILDING, DesignStage.DONE),  # the generator/evaluator split (§4.9.5)
    (DesignStage.DESIGN_BRIEF, DesignStage.DONE),  # skipping build AND review
    (DesignStage.DESIGN_BRIEF, DesignStage.VISUAL_REVIEW),  # skipping the build
    (DesignStage.DONE, DesignStage.BUILDING),  # reopening a shipped effort
    (DesignStage.REJECTED, DesignStage.BUILDING),  # reopening an abandoned effort
]


# --------------------------------------------------------------------------- #
# State machine legality.                                                      #
# --------------------------------------------------------------------------- #


def test_no_building_to_done_edge_enforces_generator_evaluator_split() -> None:
    # The crux: a build CANNOT ship itself. DONE is reachable only via review.
    assert (DesignStage.BUILDING, DesignStage.DONE) not in ALLOWED_DESIGN_TRANSITIONS
    assert is_allowed_design_transition(DesignStage.BUILDING, DesignStage.DONE) is False
    assert is_allowed_design_transition(DesignStage.VISUAL_REVIEW, DesignStage.DONE) is True


@pytest.mark.parametrize("edge", _FORBIDDEN_EDGES)
def test_forbidden_edges_are_illegal(edge: tuple[DesignStage, DesignStage]) -> None:
    assert is_allowed_design_transition(*edge) is False


def test_done_and_rejected_are_the_only_terminal_sinks() -> None:
    assert set(DESIGN_TERMINAL_STAGES) == {DesignStage.DONE, DesignStage.REJECTED}
    assert is_design_terminal(DesignStage.DONE) and is_design_terminal(DesignStage.REJECTED)
    assert not is_design_terminal(DesignStage.BUILDING)


def test_review_can_bounce_back_to_building() -> None:
    # The iterate-to-perfection loop (§3.7): a failing review rebuilds, not ships.
    assert is_allowed_design_transition(DesignStage.VISUAL_REVIEW, DesignStage.BUILDING) is True


@given(source=_stage, target=_stage)
def test_property_function_agrees_with_table_exactly(
    source: DesignStage, target: DesignStage
) -> None:
    # Property: the function is EXACTLY table membership — no hidden allowances.
    assert is_allowed_design_transition(source, target) == (
        (source, target) in ALLOWED_DESIGN_TRANSITIONS
    )


def test_no_legal_edge_targets_design_brief() -> None:
    # DESIGN_BRIEF is the unique start — nothing transitions back into it.
    assert all(target is not DesignStage.DESIGN_BRIEF for _, target in ALLOWED_DESIGN_TRANSITIONS)


# --------------------------------------------------------------------------- #
# Audited trail — append-only, gapless, legal-only.                           #
# --------------------------------------------------------------------------- #


def test_empty_trail_starts_at_design_brief() -> None:
    t = DesignWorkflowTrail()
    assert t.current_stage is DesignStage.DESIGN_BRIEF
    assert t.next_seq == 0
    assert t.is_gapless()


def test_happy_path_to_done_is_gapless_and_attributed() -> None:
    t = (
        DesignWorkflowTrail()
        .advance(to_stage=DesignStage.BUILDING, actor_role="cdo", reason="brief ok", at=_AT)
        .advance(to_stage=DesignStage.VISUAL_REVIEW, actor_role="builder", reason="built", at=_AT)
        .advance(to_stage=DesignStage.DONE, actor_role="reviewer", reason="DoD pass", at=_AT)
    )
    assert t.current_stage is DesignStage.DONE
    assert t.is_gapless()
    assert tuple(tr.seq for tr in t.transitions) == (0, 1, 2)
    assert t.transitions[-1].actor_role == "reviewer"  # the SEPARATE evaluator


def test_advance_returns_new_trail_original_unchanged() -> None:
    t0 = DesignWorkflowTrail()
    t1 = t0.advance(to_stage=DesignStage.BUILDING, actor_role="x", reason="r", at=_AT)
    assert t0.transitions == ()  # append-only: original is untouched
    assert len(t1.transitions) == 1


def test_build_cannot_self_certify_as_done() -> None:
    building = DesignWorkflowTrail().advance(
        to_stage=DesignStage.BUILDING, actor_role="x", reason="r", at=_AT
    )
    with pytest.raises(ValueError, match="illegal design transition: BUILDING -> DONE"):
        building.advance(to_stage=DesignStage.DONE, actor_role="x", reason="r", at=_AT)


def test_cannot_advance_past_terminal_stage() -> None:
    done = (
        DesignWorkflowTrail()
        .advance(to_stage=DesignStage.BUILDING, actor_role="x", reason="r", at=_AT)
        .advance(to_stage=DesignStage.VISUAL_REVIEW, actor_role="x", reason="r", at=_AT)
        .advance(to_stage=DesignStage.DONE, actor_role="x", reason="r", at=_AT)
    )
    with pytest.raises(ValueError, match="terminal stage DONE"):
        done.advance(to_stage=DesignStage.BUILDING, actor_role="x", reason="r", at=_AT)


def test_transition_requires_non_empty_actor_and_reason() -> None:
    with pytest.raises(ValidationError, match="non-empty"):
        DesignStageTransition(
            seq=0,
            from_stage=DesignStage.DESIGN_BRIEF,
            to_stage=DesignStage.BUILDING,
            actor_role="  ",
            reason="r",
            timestamp=_AT,
        )
    with pytest.raises(ValidationError, match="non-empty"):
        DesignStageTransition(
            seq=0,
            from_stage=DesignStage.DESIGN_BRIEF,
            to_stage=DesignStage.BUILDING,
            actor_role="x",
            reason="",
            timestamp=_AT,
        )


def test_transition_negative_seq_refused() -> None:
    with pytest.raises(ValidationError, match=">= 0"):
        DesignStageTransition(
            seq=-1,
            from_stage=DesignStage.DESIGN_BRIEF,
            to_stage=DesignStage.BUILDING,
            actor_role="x",
            reason="r",
            timestamp=_AT,
        )


def test_directly_constructed_non_gapless_trail_is_detected() -> None:
    # A hand-built trail that skips a seq is detectably non-gapless (rewrite guard).
    gapped = DesignWorkflowTrail(
        transitions=(
            DesignStageTransition(
                seq=0,
                from_stage=DesignStage.DESIGN_BRIEF,
                to_stage=DesignStage.BUILDING,
                actor_role="x",
                reason="r",
                timestamp=_AT,
            ),
            DesignStageTransition(
                seq=2,  # gap: should be 1
                from_stage=DesignStage.BUILDING,
                to_stage=DesignStage.VISUAL_REVIEW,
                actor_role="x",
                reason="r",
                timestamp=_AT,
            ),
        )
    )
    assert gapped.is_gapless() is False


@st.composite
def _legal_walks(draw: st.DrawFn) -> DesignWorkflowTrail:
    # Drive the trail only via legal advances, so the resulting path is, by
    # construction, a legal gapless walk — the property asserts the trail keeps it.
    trail = DesignWorkflowTrail()
    for _ in range(draw(st.integers(min_value=0, max_value=8))):
        if is_design_terminal(trail.current_stage):
            break
        legal_targets = [
            target
            for (src, target) in ALLOWED_DESIGN_TRANSITIONS
            if src is trail.current_stage
        ]
        target = draw(st.sampled_from(legal_targets))
        trail = trail.advance(to_stage=target, actor_role="agent", reason="step", at=_AT)
    return trail


@given(trail=_legal_walks())
def test_property_legal_walk_is_always_gapless_and_legal(trail: DesignWorkflowTrail) -> None:
    # Property: any sequence of legal advances yields a gapless trail whose every
    # recorded edge is legal and whose seqs are exactly 0..n-1.
    assert trail.is_gapless()
    for transition in trail.transitions:
        assert is_allowed_design_transition(transition.from_stage, transition.to_stage)
    assert tuple(tr.seq for tr in trail.transitions) == tuple(range(len(trail.transitions)))
