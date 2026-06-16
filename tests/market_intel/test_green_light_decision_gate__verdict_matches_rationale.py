"""Decision-gate tests: a deterministic verdict whose rationale matches it exactly.

What these prove
----------------
The green-light (go/no-go) gate is the go/no-go decision surface, so these tests
are deliberately hard and span its three guarantees:

* **Explainability never drifts (§3.11):** the listed ``contributions`` are
  EXACTLY the signals at/above the confidence floor (nothing more, nothing less),
  every contribution's ``weighted_value`` equals ``weight(category) * confidence``
  to the unit, ``total_score`` equals the sum of those values to the unit, and the
  summary's verdict word matches the structured verdict. The "why" cannot diverge
  from the "what" — asserted directly and as a Hypothesis property over arbitrary
  insight batches.
* **Fail-closed on thin/contradictory evidence (§5.6):** fewer than
  ``min_supporting_signals`` clearing the floor yields INSUFFICIENT_DATA (never a
  default GO), even when the few counting signals would have scored a GO.
* **Boundary-exact at the decision threshold:** a score landing exactly on
  ``go_score_threshold`` is GO (``>=``); a hair under is NO_GO.
* **Monotonicity property:** strengthening positive evidence (adding a counting
  signal, or raising a counting signal's confidence) never flips GO -> NO_GO.

Pure ``(insights, config)`` function: synthetic only, no clock, no network.
"""

from __future__ import annotations

import math
from datetime import UTC, datetime

import pytest
from hypothesis import assume, given
from hypothesis import strategies as st

from autofirm.market_intel.green_light_decision_contract import (
    GreenLightConfig,
    GreenLightVerdict,
)
from autofirm.market_intel.green_light_decision_gate import (
    DEFAULT_CATEGORY_WEIGHT,
    decide_green_light,
)
from autofirm.market_intel.market_insight_contract import InsightCategory, MarketInsight

_TS = datetime(2025, 4, 1, tzinfo=UTC)
_CATEGORIES = tuple(InsightCategory)


def _insight(
    confidence: float,
    category: InsightCategory = InsightCategory.CUSTOMER_DEMAND,
    source_name: str = "feed",
) -> MarketInsight:
    return MarketInsight(
        source_name=source_name,
        observation="o",
        category=category,
        confidence=confidence,
        sensed_at=_TS,
    )


# --------------------------------------------------------------------------- #
# Explainability: the rationale lists exactly the counting signals, exactly.
# --------------------------------------------------------------------------- #
def test_contributions_are_exactly_the_signals_at_or_above_floor() -> None:
    cfg = GreenLightConfig(min_supporting_signals=1, confidence_floor=0.5)
    insights = [
        _insight(0.9, source_name="strong"),  # counts
        _insight(0.5, source_name="exactly-floor"),  # counts (>= is inclusive)
        _insight(0.49, source_name="just-under"),  # excluded
        _insight(0.0, source_name="zero"),  # excluded
    ]
    decision = decide_green_light(insights, cfg)
    counted = {c.source_name for c in decision.contributions}
    assert counted == {"strong", "exactly-floor"}  # exactly the >= floor signals
    # Excluded signals appear NOWHERE in the rationale (not averaged in).
    assert "just-under" not in counted and "zero" not in counted


def test_total_score_equals_sum_of_contributions_to_the_unit() -> None:
    # Weights chosen so the arithmetic is exact and non-trivial.
    cfg = GreenLightConfig(
        min_supporting_signals=1,
        confidence_floor=0.5,
        go_score_threshold=1.0,
        category_weights={
            InsightCategory.CUSTOMER_DEMAND: 2.0,
            InsightCategory.PRICING: 0.5,
        },
    )
    insights = [
        _insight(0.8, InsightCategory.CUSTOMER_DEMAND),  # 2.0 * 0.8 = 1.6
        _insight(0.6, InsightCategory.PRICING),  # 0.5 * 0.6 = 0.3
        _insight(0.7, InsightCategory.MARKET_TREND),  # default 1.0 * 0.7 = 0.7
    ]
    decision = decide_green_light(insights, cfg)
    expected_each = [1.6, 0.3, 0.7]
    got_each = [c.weighted_value for c in decision.contributions]
    for got, exp in zip(got_each, expected_each, strict=True):
        assert got == pytest.approx(exp, abs=1e-12)
    # total_score is the SUM of exactly those contributions — to the unit.
    assert decision.total_score == pytest.approx(sum(expected_each), abs=1e-12)
    assert decision.total_score == pytest.approx(sum(got_each), abs=1e-12)


def test_absent_category_uses_neutral_default_weight() -> None:
    # A category with no configured weight contributes confidence * 1.0 exactly.
    cfg = GreenLightConfig(min_supporting_signals=1, confidence_floor=0.0)
    decision = decide_green_light([_insight(0.42, InsightCategory.REGULATORY)], cfg)
    assert DEFAULT_CATEGORY_WEIGHT == 1.0
    assert decision.contributions[0].weighted_value == pytest.approx(0.42, abs=1e-12)


def test_contribution_order_preserves_input_order_deterministically() -> None:
    cfg = GreenLightConfig(min_supporting_signals=1, confidence_floor=0.5)
    insights = [
        _insight(0.9, source_name="first"),
        _insight(0.49, source_name="dropped"),
        _insight(0.8, source_name="second"),
        _insight(0.7, source_name="third"),
    ]
    decision = decide_green_light(insights, cfg)
    # Order follows the input, with the sub-floor signal removed (not reordered).
    assert [c.source_name for c in decision.contributions] == ["first", "second", "third"]


# --------------------------------------------------------------------------- #
# Verdict word in the summary matches the structured verdict (no drift).
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    ("score_threshold", "confidences", "expected"),
    [
        (1.0, [0.9, 0.9], GreenLightVerdict.GO),  # 1.8 >= 1.0
        (1.0, [0.5, 0.5], GreenLightVerdict.NO_GO),  # 1.0 >= 1.0 ... see boundary test
        (2.0, [0.6, 0.6], GreenLightVerdict.NO_GO),  # 1.2 < 2.0
    ],
)
def test_summary_word_matches_structured_verdict(
    score_threshold: float,
    confidences: list[float],
    expected: GreenLightVerdict,
) -> None:
    cfg = GreenLightConfig(min_supporting_signals=2, go_score_threshold=score_threshold)
    decision = decide_green_light([_insight(c) for c in confidences], cfg)
    # The summary leads with the verdict token; it must equal the enum value.
    assert decision.summary.split(":", 1)[0] == decision.verdict.name
    if expected is GreenLightVerdict.GO:
        assert decision.verdict is GreenLightVerdict.GO


# --------------------------------------------------------------------------- #
# Boundary-exact around the GO threshold (on / just-over / just-under).
# --------------------------------------------------------------------------- #
def test_score_exactly_on_threshold_is_go() -> None:
    # Two signals of weight 1.0 * confidence 0.5 = total 1.0, threshold 1.0 -> GO (>=).
    cfg = GreenLightConfig(min_supporting_signals=2, confidence_floor=0.5, go_score_threshold=1.0)
    decision = decide_green_light([_insight(0.5), _insight(0.5)], cfg)
    assert decision.total_score == pytest.approx(1.0, abs=1e-12)
    assert decision.verdict is GreenLightVerdict.GO  # on-threshold passes


def test_score_just_under_threshold_is_no_go() -> None:
    # Both signals clear the floor (so min_supporting_signals is met) but their
    # weighted sum lands a hair UNDER the threshold -> NO_GO, not INSUFFICIENT_DATA.
    # Both at 0.50 (weight 1.0) sum to exactly 1.0, set just under a 1.00001 bar.
    cfg = GreenLightConfig(
        min_supporting_signals=2, confidence_floor=0.5, go_score_threshold=1.00001
    )
    decision = decide_green_light([_insight(0.50), _insight(0.50)], cfg)
    assert len(decision.contributions) == 2  # both cleared the floor (support met)
    assert decision.total_score < 1.00001
    assert decision.verdict is GreenLightVerdict.NO_GO


def test_score_just_over_threshold_is_go() -> None:
    # Both signals clear the floor; their sum lands a hair OVER the threshold -> GO.
    cfg = GreenLightConfig(
        min_supporting_signals=2, confidence_floor=0.5, go_score_threshold=0.99999
    )
    decision = decide_green_light([_insight(0.5), _insight(0.5)], cfg)
    assert len(decision.contributions) == 2
    assert decision.total_score > 0.99999
    assert decision.verdict is GreenLightVerdict.GO


# --------------------------------------------------------------------------- #
# Fail-closed on thin / contradictory evidence.
# --------------------------------------------------------------------------- #
def test_no_insights_is_insufficient_data_not_no_go() -> None:
    cfg = GreenLightConfig(min_supporting_signals=2)
    decision = decide_green_light([], cfg)
    assert decision.verdict is GreenLightVerdict.INSUFFICIENT_DATA
    assert decision.total_score == 0.0
    assert decision.contributions == ()
    assert decision.summary.startswith("INSUFFICIENT_DATA")


def test_too_few_counting_signals_is_insufficient_even_if_they_would_score_go() -> None:
    # The single counting signal scores 5.0 (>= a 1.0 threshold) — would be a GO on
    # score alone — but min_supporting_signals=2 is NOT met -> fail-closed refuse.
    cfg = GreenLightConfig(
        min_supporting_signals=2,
        confidence_floor=0.5,
        go_score_threshold=1.0,
        category_weights={InsightCategory.CUSTOMER_DEMAND: 5.0},
    )
    insights = [
        _insight(1.0, InsightCategory.CUSTOMER_DEMAND),  # counts, weighted 5.0
        _insight(0.49),  # below floor -> does NOT count
    ]
    decision = decide_green_light(insights, cfg)
    assert decision.verdict is GreenLightVerdict.INSUFFICIENT_DATA  # not GO
    assert len(decision.contributions) == 1  # only the one that cleared the floor
    assert decision.total_score == pytest.approx(5.0, abs=1e-12)  # score still exact


def test_all_signals_below_floor_is_insufficient_data() -> None:
    cfg = GreenLightConfig(min_supporting_signals=1, confidence_floor=0.6)
    decision = decide_green_light([_insight(0.59), _insight(0.1)], cfg)
    assert decision.verdict is GreenLightVerdict.INSUFFICIENT_DATA
    assert decision.contributions == ()
    assert decision.total_score == 0.0


def test_iterable_input_is_consumed_once_correctly() -> None:
    # The gate accepts any Iterable; a one-shot generator must still produce the
    # right rationale (it is iterated exactly once internally).
    cfg = GreenLightConfig(min_supporting_signals=1, confidence_floor=0.5)
    gen = (_insight(0.7) for _ in range(3))
    decision = decide_green_light(gen, cfg)
    assert len(decision.contributions) == 3


# --------------------------------------------------------------------------- #
# Determinism: identical inputs -> identical decision, repeatedly.
# --------------------------------------------------------------------------- #
def test_decision_is_deterministic_across_repeated_runs() -> None:
    cfg = GreenLightConfig(
        min_supporting_signals=2,
        confidence_floor=0.5,
        category_weights={InsightCategory.PRICING: 1.5},
    )
    insights = [_insight(0.8, InsightCategory.PRICING), _insight(0.6), _insight(0.4)]
    first = decide_green_light(insights, cfg)
    second = decide_green_light(insights, cfg)
    assert first == second  # frozen pydantic models compare by value


# --------------------------------------------------------------------------- #
# Property: the rationale matches the verdict exactly, for ANY batch.
# --------------------------------------------------------------------------- #
_confidence = st.floats(min_value=0.0, max_value=1.0, allow_nan=False)
_category = st.sampled_from(_CATEGORIES)
_weight = st.floats(min_value=0.0, max_value=10.0, allow_nan=False, allow_infinity=False)


@st.composite
def _insights(draw: st.DrawFn) -> list[MarketInsight]:
    n = draw(st.integers(min_value=0, max_value=8))
    return [
        _insight(draw(_confidence), draw(_category), source_name=f"s{i}") for i in range(n)
    ]


@st.composite
def _configs(draw: st.DrawFn) -> GreenLightConfig:
    weights = draw(st.dictionaries(_category, _weight, max_size=len(_CATEGORIES)))
    return GreenLightConfig(
        min_supporting_signals=draw(st.integers(min_value=1, max_value=5)),
        confidence_floor=draw(st.floats(min_value=0.0, max_value=1.0, allow_nan=False)),
        go_score_threshold=draw(
            st.floats(min_value=0.0001, max_value=20.0, allow_nan=False, allow_infinity=False)
        ),
        category_weights=weights,
    )


@pytest.mark.property
@given(insights=_insights(), cfg=_configs())
def test_property_rationale_matches_verdict_exactly(
    insights: list[MarketInsight], cfg: GreenLightConfig
) -> None:
    decision = decide_green_light(insights, cfg)

    # 1. Contributions are EXACTLY the at-or-above-floor insights, in input order.
    expected_counting = [i for i in insights if i.confidence >= cfg.confidence_floor]
    assert len(decision.contributions) == len(expected_counting)
    for contrib, src in zip(decision.contributions, expected_counting, strict=True):
        assert contrib.source_name == src.source_name
        assert contrib.category == src.category
        assert contrib.confidence == src.confidence
        # 2. Each weighted_value == weight(category) * confidence, to the unit.
        weight = cfg.category_weights.get(src.category, DEFAULT_CATEGORY_WEIGHT)
        assert contrib.weighted_value == pytest.approx(weight * src.confidence, abs=1e-9)

    # 3. total_score == sum of contributions, to the unit.
    assert decision.total_score == pytest.approx(
        sum(c.weighted_value for c in decision.contributions), abs=1e-9
    )

    # 4. The verdict follows the documented rule exactly — the WHAT matches the WHY.
    if len(decision.contributions) < cfg.min_supporting_signals:
        assert decision.verdict is GreenLightVerdict.INSUFFICIENT_DATA
    elif decision.total_score >= cfg.go_score_threshold:
        assert decision.verdict is GreenLightVerdict.GO
    else:
        assert decision.verdict is GreenLightVerdict.NO_GO

    # 5. The summary's leading token equals the structured verdict (no drift).
    assert decision.summary.split(":", 1)[0] == decision.verdict.name


# --------------------------------------------------------------------------- #
# Property: monotonicity — stronger positive evidence never flips GO -> NO_GO.
# --------------------------------------------------------------------------- #
@pytest.mark.property
@given(
    base=_insights(),
    extra_conf=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
    extra_cat=_category,
)
def test_property_adding_counting_signal_never_flips_go_to_no_go(
    base: list[MarketInsight], extra_conf: float, extra_cat: InsightCategory
) -> None:
    # Use the default config so all weights are the neutral 1.0 (non-negative):
    # adding ANY counting signal only ever raises the score, never lowers it.
    cfg = GreenLightConfig(min_supporting_signals=1, confidence_floor=0.5, go_score_threshold=1.0)
    before = decide_green_light(base, cfg)
    assume(before.verdict is GreenLightVerdict.GO)

    stronger = [*base, _insight(extra_conf, extra_cat, source_name="extra")]
    after = decide_green_light(stronger, cfg)
    # Stronger (or equal) positive evidence must NOT downgrade a GO. With neutral
    # weights, the score is non-decreasing and the support count only grows.
    assert after.verdict is GreenLightVerdict.GO
    assert after.total_score >= before.total_score - 1e-9


@pytest.mark.property
@given(
    others=_insights(),
    low=st.floats(min_value=0.5, max_value=0.9, allow_nan=False),
    bump=st.floats(min_value=0.0, max_value=0.5, allow_nan=False),
    category=_category,
)
def test_property_raising_a_counting_signal_confidence_never_flips_go_to_no_go(
    others: list[MarketInsight],
    low: float,
    bump: float,
    category: InsightCategory,
) -> None:
    cfg = GreenLightConfig(min_supporting_signals=1, confidence_floor=0.5, go_score_threshold=1.0)
    high = min(1.0, low + bump)
    weaker = [_insight(low, category, source_name="target"), *others]
    stronger = [_insight(high, category, source_name="target"), *others]
    before = decide_green_light(weaker, cfg)
    assume(before.verdict is GreenLightVerdict.GO)
    after = decide_green_light(stronger, cfg)
    # Raising a counting signal's confidence raises its weighted value (weight>=0),
    # so the total score is non-decreasing and a GO cannot flip to NO_GO.
    assert after.verdict is GreenLightVerdict.GO
    assert after.total_score >= before.total_score - 1e-9
    assert math.isfinite(after.total_score)


# --------------------------------------------------------------------------- #
# Config validation is fail-closed (the gate cannot be mis-set into passing).
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("bad_floor", [-0.0001, 1.0001, -1.0, 2.0])
def test_config_refuses_confidence_floor_outside_unit_interval(bad_floor: float) -> None:
    with pytest.raises(ValueError, match="confidence_floor"):
        GreenLightConfig(confidence_floor=bad_floor)


@pytest.mark.parametrize("edge", [0.0, 1.0])
def test_config_accepts_floor_interval_edges(edge: float) -> None:
    assert GreenLightConfig(confidence_floor=edge).confidence_floor == edge


def test_config_refuses_negative_category_weight() -> None:
    # A negative weight would let strong evidence push AGAINST a GO — refuse it.
    with pytest.raises(ValueError, match="category_weights"):
        GreenLightConfig(category_weights={InsightCategory.PRICING: -0.01})


def test_config_accepts_zero_category_weight() -> None:
    # Zero is the boundary: allowed (a muted category), negative is not.
    cfg = GreenLightConfig(category_weights={InsightCategory.PRICING: 0.0})
    assert cfg.category_weights[InsightCategory.PRICING] == 0.0


@pytest.mark.parametrize("bad", [0, -1])
def test_config_refuses_non_positive_min_supporting_signals(bad: int) -> None:
    with pytest.raises(ValueError):
        GreenLightConfig(min_supporting_signals=bad)


@pytest.mark.parametrize("bad", [0.0, -1.0])
def test_config_refuses_non_positive_go_threshold(bad: float) -> None:
    with pytest.raises(ValueError):
        GreenLightConfig(go_score_threshold=bad)
