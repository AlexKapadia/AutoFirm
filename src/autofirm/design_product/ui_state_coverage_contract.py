"""The UI state-coverage contract: every flow must cover every required state.

What this does
--------------
Defines :class:`UiState` — the exhaustive set of states a real interface must
handle — and :class:`FlowStateCoverage`, a per-flow declaration of which states
that flow designs for. It turns CLAUDE.md §3.14/§4.9's "built around real data
and **every state** (loading / empty / error / edge), never happy-path mockups"
into a checkable contract: a flow that only covers the IDEAL (happy) state is
refused, because the missing loading/empty/error states are exactly the
happy-path-mockup defect the bar bans.

Why it exists / where it sits
-----------------------------
Per ``docs/research/B13-product-and-design/SYNTHESIS.md`` §1 L1.B13.3, the
four-state minimum (loading / empty / error / ideal, source 09) operationalises
Nielsen's Heuristic 1 (visibility of system status). A design brief composes one
:class:`FlowStateCoverage` per user flow; the brief is refused if any flow skips
a required state.

Security / compliance invariants upheld
---------------------------------------
* **Every-state gate (fail-closed, §3.14):** a flow must cover all of
  :data:`REQUIRED_STATES`. A flow missing any required state is refused with the
  missing states named — happy-path-only is a defect, not a default.
* **Deterministic:** coverage checking is a pure set operation over the declared
  states; no ambient state.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

__all__ = ["REQUIRED_STATES", "FlowStateCoverage", "UiState"]


class UiState(StrEnum):
    """The exhaustive set of UI states a real, non-static interface must handle.

    LOADING/EMPTY/ERROR/IDEAL are the four-state minimum (SYNTHESIS source 09);
    EDGE captures the boundary cases (maximal/degenerate data) the §3.6 edge-case
    bar demands. IDEAL is the happy path — necessary but, on its own, the
    happy-path-mockup defect the §3.14 bar bans.
    """

    LOADING = "LOADING"  # data in flight — system-status visibility (Nielsen H1)
    EMPTY = "EMPTY"  # no data yet / zero results — must be designed, not blank
    ERROR = "ERROR"  # the request failed — must recover, not white-screen
    IDEAL = "IDEAL"  # the happy path with representative real-shaped data
    EDGE = "EDGE"  # boundary data (maximal / degenerate) — §3.6 edge cases


# The states a real flow MUST design for. IDEAL alone is the happy-path mockup the
# §3.14 bar rejects; the loading/empty/error trio is what makes an interface real.
# EDGE is encouraged but not mandated here (it is enforced by the §3.6 test bar).
REQUIRED_STATES: frozenset[UiState] = frozenset(
    {UiState.LOADING, UiState.EMPTY, UiState.ERROR, UiState.IDEAL}
)


class FlowStateCoverage(BaseModel):
    """A single user flow plus the exact set of UI states it designs for.

    Construction is fail-closed: the declared ``states_covered`` must be a
    superset of :data:`REQUIRED_STATES`, so a flow can never be accepted while
    silently omitting its loading, empty, or error design (§3.14 every-state).
    """

    model_config = ConfigDict(frozen=True)

    flow_name: str  # the user flow this covers (e.g. "checkout", "onboarding")
    states_covered: frozenset[UiState]  # the states this flow explicitly designs

    @field_validator("flow_name")
    @classmethod
    def _flow_name_non_empty(cls, value: str) -> str:
        # fail-closed: an unnamed flow cannot be reviewed or traced. Refuse it.
        if not value.strip():
            raise ValueError("flow_name must be non-empty")
        return value

    @model_validator(mode="after")
    def _covers_every_required_state(self) -> FlowStateCoverage:
        missing = REQUIRED_STATES - self.states_covered
        # fail-closed (§3.14 every-state): a flow missing any required state is a
        # happy-path mockup. Refuse it and name exactly what is missing.
        if missing:
            missing_names = ", ".join(sorted(state.value for state in missing))
            raise ValueError(
                f"flow {self.flow_name!r} is missing required UI states: {missing_names}"
            )
        return self
