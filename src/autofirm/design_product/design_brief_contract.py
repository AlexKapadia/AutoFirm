"""The per-project design brief contract — the design org's output for a client.

What this does
--------------
Defines :class:`DesignBrief` — the immutable, validated brief AutoFirm's design
org authors for one client company's product, per CLAUDE.md §4.9.2 ("the brief,
not chat, is the contract the build agents work against"). It composes the real
design-token scales (:mod:`~autofirm.design_product.design_tokens_contract`), the
per-flow state coverage (:mod:`~autofirm.design_product.ui_state_coverage_contract`),
a non-trivial component inventory, and the explicit quality bar — and refuses any
brief that would let a happy-path / vibe-coded build through.

Why it exists / where it sits
-----------------------------
This is the top of the contract layer: a brief is the artifact a design role
owns and the design workflow (brief -> build -> review -> done) is built around.
It is general — no industry baked in — so the same contract governs a SaaS,
fintech, or marketplace client (SYNTHESIS §5 generality).

Security / compliance invariants upheld
---------------------------------------
* **Not-vibe-coded gate (fail-closed, §3.14):** the brief embeds
  :class:`DesignTokenScales`, whose own construction already refuses a brief that
  lacks a real type/spacing/motion scale or an accessible palette — so a brief
  cannot exist without a deliberate design system.
* **Every-state gate (fail-closed, §3.14):** every declared flow carries
  :class:`FlowStateCoverage`, which refuses a happy-path-only flow; the brief
  additionally requires at least one flow (a product with no flows is not a brief).
* **Real component inventory (fail-closed):** the brief must name at least
  :data:`MIN_COMPONENTS` distinct components — a one-component "inventory" is the
  template-grid AI-slop default the bar bans.
* **Immutable:** frozen once built; a re-scope produces a NEW brief (append-only
  authorship), never an in-place mutation.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, field_validator

from autofirm.design_product.design_tokens_contract import DesignTokenScales
from autofirm.design_product.ui_state_coverage_contract import FlowStateCoverage

__all__ = ["MIN_COMPONENTS", "DesignBrief"]

# A real product has a component system, not a single card repeated in a grid.
# Fewer than this is the template card-grid AI-slop signature the §3.14 bar bans.
MIN_COMPONENTS = 3


class DesignBrief(BaseModel):
    """An immutable, validated per-project design brief for one client product.

    Construction is fail-closed and compositional: it inherits the not-vibe-coded
    gate from its :class:`DesignTokenScales` and the every-state gate from each
    :class:`FlowStateCoverage`, and adds its own minimum-flows, minimum-components,
    and non-empty-quality-bar gates. A brief that would permit a happy-path or
    template build cannot be constructed.
    """

    model_config = ConfigDict(frozen=True)

    project_name: str  # the client product this brief governs
    tokens: DesignTokenScales  # the real design system (own not-vibe-coded gate)
    flows: tuple[FlowStateCoverage, ...]  # every user flow + its state coverage
    component_inventory: tuple[str, ...]  # the named components to build
    quality_bar: str  # the explicit standard this brief is held to (§4.9 DoD ref)

    @field_validator("project_name", "quality_bar")
    @classmethod
    def _required_text_non_empty(cls, value: str) -> str:
        # fail-closed: a brief with no project or no stated quality bar cannot be
        # traced or held to a standard. Refuse it (§4.9.2 brief-is-the-contract).
        if not value.strip():
            raise ValueError("project_name and quality_bar must be non-empty")
        return value

    @field_validator("flows")
    @classmethod
    def _at_least_one_unique_flow(
        cls, value: tuple[FlowStateCoverage, ...]
    ) -> tuple[FlowStateCoverage, ...]:
        # fail-closed: a product with no flows is not a design brief; duplicate
        # flow names make state coverage ambiguous. Refuse both.
        if not value:
            raise ValueError("a brief must declare at least one user flow")
        names = [flow.flow_name for flow in value]
        if len(set(names)) != len(names):
            raise ValueError("flow names must be unique within a brief")
        return value

    @field_validator("component_inventory")
    @classmethod
    def _real_component_inventory(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        # fail-closed (§3.14 no template card-grid): a real product is a system of
        # distinct components, not one card repeated. Require a genuine inventory.
        cleaned = [name.strip() for name in value]
        if any(not name for name in cleaned):
            raise ValueError("component names must be non-empty")
        if len(set(cleaned)) < MIN_COMPONENTS:
            raise ValueError(
                f"a real component inventory needs >= {MIN_COMPONENTS} distinct "
                f"components (a single repeated card is the AI-slop default)"
            )
        return value
