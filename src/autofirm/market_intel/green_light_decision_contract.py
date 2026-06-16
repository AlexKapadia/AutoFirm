"""Typed contracts for the green-light (go/no-go) gate: config + explainable verdict.

What this does
--------------
Defines the inputs and outputs of the green-light gate:

* :class:`GreenLightVerdict` — the closed verdict set (GO / NO_GO / INSUFFICIENT_DATA).
* :class:`GreenLightConfig` — the deterministic, validated thresholds the gate
  decides against (how many supporting insights are required, the confidence floor
  a signal must clear to count, and the per-category weights).
* :class:`SignalContribution` — one line of the EXPLANATION: which insight counted,
  in which category, at what confidence, and the weight it carried.
* :class:`GreenLightDecision` — the verdict plus the full list of contributions
  (the rationale) and a human-readable summary. The rationale is the proof: the
  contributions listed are exactly the signals that drove the verdict.

Why it exists / where it sits
-----------------------------
Separating the typed contracts from the decision *logic*
(``green_light_decision_gate``) keeps each file single-responsibility and lets the
explainability invariant — "the rationale matches the verdict exactly" — be
asserted against typed, frozen data rather than ad-hoc dicts.

Security / compliance invariants upheld
---------------------------------------
* **Explain-every-decision (§3.11):** the decision carries the exact set of
  contributing signals; a verdict with no traceable rationale cannot be built.
* **Validated thresholds (fail-closed):** a non-positive support requirement or a
  confidence floor outside [0, 1] is refused — the gate can never be mis-configured
  into trivially passing.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator

from autofirm.market_intel.market_insight_contract import InsightCategory

__all__ = [
    "GreenLightConfig",
    "GreenLightDecision",
    "GreenLightVerdict",
    "SignalContribution",
]


class GreenLightVerdict(StrEnum):
    """The closed verdict set of the green-light gate.

    ``INSUFFICIENT_DATA`` is a distinct fail-closed outcome (NOT a silent NO_GO):
    when too few signals clear the confidence floor to decide either way, the gate
    refuses to recommend rather than guessing.
    """

    GO = "go"
    NO_GO = "no_go"
    INSUFFICIENT_DATA = "insufficient_data"  # fail-closed: not enough to decide


class GreenLightConfig(BaseModel):
    """The deterministic, validated thresholds the green-light gate decides against.

    ``category_weights`` lets some signal categories count more toward a GO than
    others (e.g. customer demand may outweigh a single competitor move); a category
    absent from the map carries the neutral :data:`DEFAULT_CATEGORY_WEIGHT`.
    """

    model_config = ConfigDict(frozen=True)

    # Minimum number of insights that must clear the confidence floor for the gate
    # to decide at all; below this it returns INSUFFICIENT_DATA (fail-closed).
    min_supporting_signals: int = Field(default=2, ge=1)
    # A signal must reach at least this confidence to count toward the decision.
    confidence_floor: float = 0.5
    # Weighted score (sum of weight*confidence over counting signals) at/above
    # which the verdict is GO; strictly below it is NO_GO.
    go_score_threshold: float = Field(default=1.0, gt=0.0)
    category_weights: dict[InsightCategory, float] = Field(default_factory=dict)

    @field_validator("confidence_floor")
    @classmethod
    def _floor_in_unit_interval(cls, value: float) -> float:
        # fail-closed: a confidence floor outside [0, 1] could admit every signal
        # (floor < 0) or none (floor > 1), defeating the gate — refuse it.
        if not 0.0 <= value <= 1.0:
            raise ValueError("confidence_floor must be within [0.0, 1.0]")
        return value

    @field_validator("category_weights")
    @classmethod
    def _weights_non_negative(
        cls, value: dict[InsightCategory, float]
    ) -> dict[InsightCategory, float]:
        # fail-closed: a negative category weight would let a strong signal PUSH
        # AGAINST a GO, inverting the gate's meaning — refuse negative weights.
        if any(weight < 0 for weight in value.values()):
            raise ValueError("category_weights must be non-negative")
        return value


class SignalContribution(BaseModel):
    """One line of the explanation: an insight that counted and the weight it bore.

    Carried in :class:`GreenLightDecision.contributions`; the list of these IS the
    rationale — it names exactly which signals drove the verdict (§3.11).
    """

    model_config = ConfigDict(frozen=True)

    source_name: str
    category: InsightCategory
    confidence: float
    weighted_value: float  # weight(category) * confidence — its contribution to the score


class GreenLightDecision(BaseModel):
    """The gate's verdict plus its full, exact rationale.

    Invariant (asserted by the gate's tests): ``contributions`` lists every signal
    that counted toward ``verdict`` and nothing else, ``total_score`` equals the
    sum of their ``weighted_value``, and ``summary`` states the verdict — so the
    explanation can never drift from the decision.
    """

    model_config = ConfigDict(frozen=True)

    verdict: GreenLightVerdict
    total_score: float
    contributions: tuple[SignalContribution, ...]
    summary: str
