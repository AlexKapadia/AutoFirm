"""State-coverage + brief tests: happy-path-only is refused; a real brief required.

Proves the §3.14 every-state rule and the brief's compositional gates: a flow
that omits ANY required state (loading/empty/error/ideal) is refused with the
missing states named; a brief with no flows, duplicate flow names, a thin
component inventory, or a blank quality bar is refused. Includes a Hypothesis
property: a FlowStateCoverage is accepted iff its declared states are a superset
of REQUIRED_STATES — never on a proper subset. Synthetic only; no network.
"""

from __future__ import annotations

import pytest
from hypothesis import given
from hypothesis import strategies as st
from pydantic import ValidationError

from autofirm.design_product.design_brief_contract import MIN_COMPONENTS, DesignBrief
from autofirm.design_product.design_tokens_contract import ColorRole, DesignTokenScales
from autofirm.design_product.ui_state_coverage_contract import (
    REQUIRED_STATES,
    FlowStateCoverage,
    UiState,
)

_ALL_STATES = list(UiState)
_TOKENS = DesignTokenScales(
    type_scale_px=(12.0, 16.0, 24.0),
    spacing_scale_px=(4.0, 8.0, 16.0),
    motion_scale_ms=(100.0, 200.0, 300.0),
    color_roles=(ColorRole(name="surface", color=(255, 255, 255), on_color=(0, 0, 0)),),
)
_FULL_FLOW = FlowStateCoverage(flow_name="checkout", states_covered=REQUIRED_STATES)


def _valid_brief(**overrides: object) -> DesignBrief:
    base: dict[str, object] = {
        "project_name": "Acme Storefront",
        "tokens": _TOKENS,
        "flows": (_FULL_FLOW,),
        "component_inventory": ("Button", "Card", "Nav"),
        "quality_bar": "UI Definition-of-Done §4.9",
    }
    base.update(overrides)
    return DesignBrief(**base)  # type: ignore[arg-type]


# --------------------------------------------------------------------------- #
# State coverage — every-state gate.                                           #
# --------------------------------------------------------------------------- #


def test_full_coverage_flow_builds() -> None:
    assert _FULL_FLOW.states_covered >= REQUIRED_STATES


_REQUIRED_STATES_SORTED: list[UiState] = sorted(REQUIRED_STATES)


@pytest.mark.parametrize("dropped", _REQUIRED_STATES_SORTED)
def test_dropping_any_required_state_is_refused_and_names_it(dropped: UiState) -> None:
    # Happy-path mockup: omit exactly one required state -> refused, state named.
    partial = REQUIRED_STATES - {dropped}
    with pytest.raises(ValidationError, match=dropped.value):
        FlowStateCoverage(flow_name="f", states_covered=partial)


def test_ideal_only_is_the_canonical_happy_path_defect() -> None:
    # The exact defect §3.14 bans: only IDEAL declared. Must be refused.
    with pytest.raises(ValidationError, match="missing required UI states"):
        FlowStateCoverage(flow_name="f", states_covered=frozenset({UiState.IDEAL}))


def test_superset_with_edge_is_accepted() -> None:
    # Covering MORE than required (adding EDGE) is fine — only omission is refused.
    cov = FlowStateCoverage(flow_name="f", states_covered=REQUIRED_STATES | {UiState.EDGE})
    assert UiState.EDGE in cov.states_covered


def test_empty_flow_name_refused() -> None:
    with pytest.raises(ValidationError, match="non-empty"):
        FlowStateCoverage(flow_name="  ", states_covered=REQUIRED_STATES)


@given(states=st.frozensets(st.sampled_from(_ALL_STATES)))
def test_property_accepted_iff_superset_of_required(states: frozenset[UiState]) -> None:
    # Property: a flow is accepted IFF it covers every required state.
    covers_all = states >= REQUIRED_STATES
    if covers_all:
        FlowStateCoverage(flow_name="f", states_covered=states)
    else:
        with pytest.raises(ValidationError):
            FlowStateCoverage(flow_name="f", states_covered=states)


# --------------------------------------------------------------------------- #
# Design brief — compositional gates.                                          #
# --------------------------------------------------------------------------- #


def test_valid_brief_builds_and_is_frozen() -> None:
    brief = _valid_brief()
    assert brief.project_name == "Acme Storefront"
    with pytest.raises(ValidationError):  # frozen
        brief.project_name = "x"


def test_brief_with_no_flows_refused() -> None:
    with pytest.raises(ValidationError, match="at least one user flow"):
        _valid_brief(flows=())


def test_brief_with_duplicate_flow_names_refused() -> None:
    with pytest.raises(ValidationError, match="unique"):
        _valid_brief(flows=(_FULL_FLOW, _FULL_FLOW))


def test_brief_inherits_every_state_gate_through_its_flow() -> None:
    # A brief cannot smuggle in a happy-path flow: the flow itself refuses first.
    with pytest.raises(ValidationError):
        bad_flow = FlowStateCoverage(  # noqa: F841 — constructed to prove refusal
            flow_name="f", states_covered=frozenset({UiState.IDEAL})
        )


@pytest.mark.parametrize("count", range(MIN_COMPONENTS))
def test_brief_with_thin_component_inventory_refused(count: int) -> None:
    # Fewer than MIN_COMPONENTS distinct components == template card-grid slop.
    inventory = tuple(f"Comp{i}" for i in range(count))
    with pytest.raises(ValidationError, match="real component inventory"):
        _valid_brief(component_inventory=inventory)


def test_brief_duplicate_components_dont_count_toward_minimum() -> None:
    # Three entries but one distinct name: still below the real-inventory floor.
    with pytest.raises(ValidationError, match="real component inventory"):
        _valid_brief(component_inventory=("Card", "Card", "Card"))


def test_brief_blank_component_name_refused() -> None:
    with pytest.raises(ValidationError, match="non-empty"):
        _valid_brief(component_inventory=("Button", "  ", "Nav"))


@pytest.mark.parametrize("field", ["project_name", "quality_bar"])
def test_brief_blank_required_text_refused(field: str) -> None:
    with pytest.raises(ValidationError, match="non-empty"):
        _valid_brief(**{field: "   "})
