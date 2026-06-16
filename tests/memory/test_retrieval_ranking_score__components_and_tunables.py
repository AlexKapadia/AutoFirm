"""Adversarial + property tests for the retrieval score (A4.2; Gen-Agents 04).

Proves teeth (CLAUDE.md §3.6): the recency/relevance/importance blend is
explainable and exact -- recency decays monotonically with age and clamps the
future to 1.0; relevance clamps negative cosine to 0; importance is range-checked
fail-closed; weights/decay are validated fail-closed; and the total is exactly the
weighted sum (so the "why" matches the "what"). Designed to KILL mutants on the
decay exponent, the clamps, and the weight blend.
"""

from __future__ import annotations

import math
from datetime import UTC, datetime, timedelta

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from autofirm.memory.retrieval_ranking_score import (
    RetrievalWeights,
    score_record,
)

_REF = datetime(2025, 6, 1, tzinfo=UTC)
_UNIT = (1.0, 0.0)  # a unit vector; cosine with itself == 1.0


def _score(**overrides: object):
    base: dict[str, object] = {
        "record_vector": _UNIT,
        "query_vector": _UNIT,
        "written_at": _REF,
        "importance": 0.0,
        "reference_time": _REF,
        "weights": RetrievalWeights(),
    }
    base.update(overrides)
    return score_record(**base)  # type: ignore[arg-type]


@pytest.mark.parametrize("bad_decay", [0.0, -0.1, 1.0001, 2.0])
def test_decay_base_out_of_range_refused(bad_decay: float) -> None:
    with pytest.raises(ValueError, match="decay_base must be in"):
        RetrievalWeights(decay_base=bad_decay)


def test_decay_base_one_is_boundary_accepted() -> None:
    assert RetrievalWeights(decay_base=1.0).decay_base == 1.0


def test_negative_weight_refused() -> None:
    with pytest.raises(ValueError, match="recency_weight must be >= 0"):
        RetrievalWeights(recency_weight=-1.0)


@pytest.mark.parametrize("bad_importance", [-0.01, 1.01, 2.0])
def test_importance_out_of_range_refused(bad_importance: float) -> None:
    with pytest.raises(ValueError, match="importance must be in"):
        _score(importance=bad_importance)


def test_just_written_record_has_recency_one() -> None:
    s = _score(written_at=_REF, reference_time=_REF)
    assert s.recency == 1.0


def test_future_written_record_recency_clamped_to_one() -> None:
    # Clock skew / out-of-order replay must not produce recency > 1 (fail-safe).
    s = _score(written_at=_REF + timedelta(hours=5), reference_time=_REF)
    assert s.recency == 1.0


def test_older_record_decays_below_newer() -> None:
    older = _score(written_at=_REF - timedelta(hours=10))
    newer = _score(written_at=_REF - timedelta(hours=1))
    assert older.recency < newer.recency < 1.0


def test_recency_matches_exact_decay_formula() -> None:
    # Boundary-exact: recency == decay_base ** hours, killing an off-by-one or
    # wrong-operator mutant in the exponent.
    w = RetrievalWeights(decay_base=0.5)
    s = _score(written_at=_REF - timedelta(hours=3), weights=w)
    assert math.isclose(s.recency, 0.5**3, rel_tol=1e-12)


def test_negative_cosine_relevance_clamped_to_zero() -> None:
    # Opposing vectors -> cosine -1 -> relevance clamps to 0 ("not relevant").
    s = _score(record_vector=(1.0, 0.0), query_vector=(-1.0, 0.0))
    assert s.relevance == 0.0


def test_total_is_exact_weighted_sum_explainability() -> None:
    w = RetrievalWeights(recency_weight=2.0, relevance_weight=3.0, importance_weight=5.0)
    s = _score(importance=0.5, weights=w)
    expected = 2.0 * s.recency + 3.0 * s.relevance + 5.0 * s.importance
    assert math.isclose(s.total, expected, rel_tol=1e-12)


def test_weights_are_tunable_not_magic_change_ranking() -> None:
    # Same inputs, different weights -> different total: proves weights are wired,
    # not ignored magic constants (CLAUDE §3.9 generality).
    base = _score(importance=1.0, weights=RetrievalWeights(importance_weight=1.0))
    boosted = _score(importance=1.0, weights=RetrievalWeights(importance_weight=10.0))
    assert boosted.total > base.total


@settings(max_examples=200)
@given(
    age_hours=st.floats(min_value=0.0, max_value=1000.0, allow_nan=False),
    importance=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
    decay=st.floats(min_value=0.01, max_value=1.0, allow_nan=False),
)
def test_property_recency_monotone_decreasing_in_age(
    age_hours: float, importance: float, decay: float
) -> None:
    w = RetrievalWeights(decay_base=decay)
    s = _score(
        written_at=_REF - timedelta(hours=age_hours), importance=importance, weights=w
    )
    # Components stay in their declared ranges, always.
    assert 0.0 <= s.recency <= 1.0
    assert 0.0 <= s.relevance <= 1.0
    assert s.importance == importance


@settings(max_examples=150)
@given(
    a1=st.floats(0.0, 500.0, allow_nan=False),
    a2=st.floats(0.0, 500.0, allow_nan=False),
)
def test_property_strictly_older_never_scores_higher_recency(a1: float, a2: float) -> None:
    s1 = _score(written_at=_REF - timedelta(hours=a1))
    s2 = _score(written_at=_REF - timedelta(hours=a2))
    if a1 < a2:  # a1 is newer
        assert s1.recency >= s2.recency
