"""The fail-closed green-light (go/no-go) gate with an exact, explainable rationale.

What this does
--------------
:func:`decide_green_light` reduces a set of structured
:class:`~autofirm.market_intel.market_insight_contract.MarketInsight` records to a
:class:`GreenLightDecision` — GO / NO_GO / INSUFFICIENT_DATA — under a deterministic
:class:`GreenLightConfig`. It is the "decide" step of sense → decide → act, and the
verdict is **explainable by construction**: the decision carries the exact list of
contributing signals (each with its category, confidence, and weighted value), and
``total_score`` equals the sum of those contributions — so the rationale can never
drift from the verdict.

The decision rule (deterministic, fail-closed):

* Only insights at/above ``confidence_floor`` *count* (weaker signals are excluded
  from the rationale, not silently averaged in).
* If fewer than ``min_supporting_signals`` count, return **INSUFFICIENT_DATA** —
  fail-closed: refuse to recommend on thin evidence rather than guess GO/NO_GO.
* Otherwise sum ``weight(category) * confidence`` over the counting signals; GO iff
  that score is at/above ``go_score_threshold``, else NO_GO.

Why it exists / where it sits
-----------------------------
This is the green-light gate the daily sweep feeds. It is a pure function of
(insights, config) — no clock, no I/O — so it is trivially deterministic and the
explainability property is directly testable.

Security / compliance invariants upheld
---------------------------------------
* **Fail-closed (§5.6):** thin evidence yields INSUFFICIENT_DATA, never a default
  GO; the threshold is strict so a borderline score cannot accidentally pass.
* **Explain-every-decision (§3.11):** the returned contributions are exactly the
  signals that drove the score, and ``total_score`` equals their sum to the unit.
* **Determinism (§3.11):** contributions are emitted in a stable order.
"""

from __future__ import annotations

from collections.abc import Iterable

from autofirm.market_intel.green_light_decision_contract import (
    GreenLightConfig,
    GreenLightDecision,
    GreenLightVerdict,
    SignalContribution,
)
from autofirm.market_intel.market_insight_contract import InsightCategory, MarketInsight

__all__ = ["DEFAULT_CATEGORY_WEIGHT", "decide_green_light"]

# The weight a category carries when it is absent from the config's weight map: a
# neutral 1.0 (the signal counts at face value). Kept explicit (not a buried magic
# number) so the default behaviour is auditable.
DEFAULT_CATEGORY_WEIGHT = 1.0


def decide_green_light(
    insights: Iterable[MarketInsight], config: GreenLightConfig
) -> GreenLightDecision:
    """Recommend GO / NO_GO / INSUFFICIENT_DATA with an exact, matching rationale.

    Args:
        insights: the structured insights to decide from (any iterable).
        config: the deterministic thresholds and per-category weights.

    Returns:
        A :class:`GreenLightDecision` whose ``contributions`` are exactly the
        signals that counted, whose ``total_score`` equals the sum of their
        weighted values, and whose ``summary`` states the verdict.
    """
    contributions = _build_contributions(insights, config)
    total_score = sum(c.weighted_value for c in contributions)

    if len(contributions) < config.min_supporting_signals:
        # fail-closed (§5.6): too few signals clear the floor to decide — refuse
        # to recommend GO/NO_GO on thin evidence; surface INSUFFICIENT_DATA.
        return GreenLightDecision(
            verdict=GreenLightVerdict.INSUFFICIENT_DATA,
            total_score=total_score,
            contributions=contributions,
            summary=(
                f"INSUFFICIENT_DATA: {len(contributions)} signal(s) cleared the "
                f"confidence floor; {config.min_supporting_signals} required."
            ),
        )

    if total_score >= config.go_score_threshold:
        verdict = GreenLightVerdict.GO
        summary = (
            f"GO: weighted score {total_score:.4f} >= "
            f"threshold {config.go_score_threshold:.4f} on {len(contributions)} signal(s)."
        )
    else:
        # Strict comparison above means a score below threshold is a clear NO_GO;
        # there is no ambiguous middle band that could pass by accident.
        verdict = GreenLightVerdict.NO_GO
        summary = (
            f"NO_GO: weighted score {total_score:.4f} < "
            f"threshold {config.go_score_threshold:.4f} on {len(contributions)} signal(s)."
        )

    return GreenLightDecision(
        verdict=verdict,
        total_score=total_score,
        contributions=contributions,
        summary=summary,
    )


def _build_contributions(
    insights: Iterable[MarketInsight], config: GreenLightConfig
) -> tuple[SignalContribution, ...]:
    """Return the counting signals as ordered contributions (the rationale).

    Only insights at/above the confidence floor count; each is converted to a
    :class:`SignalContribution` carrying its weighted value. Order is preserved
    from the input iterable so the rationale is deterministic and traceable.
    """
    contributions: list[SignalContribution] = []
    for insight in insights:
        if insight.confidence < config.confidence_floor:
            # Below the floor: excluded from the rationale entirely (not averaged
            # in) so the explanation lists ONLY signals that actually counted.
            continue
        weight = _category_weight(insight.category, config)
        contributions.append(
            SignalContribution(
                source_name=insight.source_name,
                category=insight.category,
                confidence=insight.confidence,
                weighted_value=weight * insight.confidence,
            )
        )
    return tuple(contributions)


def _category_weight(category: InsightCategory, config: GreenLightConfig) -> float:
    """The configured weight for ``category``, or the neutral default if unset."""
    return config.category_weights.get(category, DEFAULT_CATEGORY_WEIGHT)
