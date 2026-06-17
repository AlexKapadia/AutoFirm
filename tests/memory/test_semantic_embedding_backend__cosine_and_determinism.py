"""Adversarial + property tests for the embedding backend + cosine (A4.2; DPR 07).

Proves teeth (CLAUDE.md §3.6): the deterministic embedder is reproducible and
order/case-insensitive at the bag level; cosine is in range, symmetric, refuses
mismatched dimensions (fail-closed), and handles zero vectors without dividing by
zero. Designed to KILL mutants on the norm guard, the dimension check, and the
dot-product accumulation.
"""

from __future__ import annotations

import math

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from autofirm.memory.semantic_embedding_backend import (
    DeterministicHashingEmbedder,
    cosine_similarity,
)


def test_embedder_rejects_non_positive_dimension() -> None:
    with pytest.raises(ValueError, match="dimension must be a positive"):
        DeterministicHashingEmbedder(dimension=0)


def test_same_text_embeds_identically_determinism() -> None:
    e = DeterministicHashingEmbedder()
    assert e.embed("pricing strategy") == e.embed("pricing strategy")


def test_embedding_is_case_and_spacing_insensitive_at_bag_level() -> None:
    e = DeterministicHashingEmbedder()
    assert e.embed("Pricing  STRATEGY") == e.embed("pricing strategy")


def test_self_cosine_is_one_for_nonempty_text() -> None:
    e = DeterministicHashingEmbedder()
    v = e.embed("customer churn model")
    assert math.isclose(cosine_similarity(v, v), 1.0, rel_tol=1e-9)


def test_disjoint_token_texts_have_zero_cosine() -> None:
    e = DeterministicHashingEmbedder(dimension=512)  # wide -> no hash collisions
    a = e.embed("alpha beta gamma")
    b = e.embed("delta epsilon zeta")
    assert math.isclose(cosine_similarity(a, b), 0.0, abs_tol=1e-9)


def test_shared_tokens_raise_cosine_above_disjoint() -> None:
    e = DeterministicHashingEmbedder(dimension=512)
    query = e.embed("pricing strategy saas")
    near = e.embed("pricing strategy enterprise")  # 2 shared tokens
    far = e.embed("weather forecast tomorrow")  # 0 shared tokens
    assert cosine_similarity(query, near) > cosine_similarity(query, far)


def test_cosine_refuses_mismatched_dimensions_fail_closed() -> None:
    with pytest.raises(ValueError, match="equal-length vectors"):
        cosine_similarity((1.0, 2.0), (1.0,))


def test_cosine_with_zero_vector_is_zero_not_nan() -> None:
    # Fail-safe: a zero-magnitude vector has no direction -> 0.0, never a NaN/div0.
    result = cosine_similarity((0.0, 0.0, 0.0), (1.0, 2.0, 3.0))
    assert result == 0.0


def test_cosine_denormal_magnitude_stays_within_unit_range() -> None:
    # Regression (pre-existing bug): a denormal/near-zero component made the
    # dot/(norm_a*norm_b) ratio round fractionally above 1.0 (observed 1.004...),
    # which is mathematically impossible. The clamp must absorb that FP epsilon so
    # the result is *exactly* within the closed unit interval [-1.0, 1.0].
    s = cosine_similarity((1.0,), (1.7e-161,))
    assert -1.0 <= s <= 1.0
    # Parallel same-sign vectors must clamp to exactly the upper bound.
    assert s == 1.0
    # The anti-parallel counterpart must clamp to exactly the lower bound.
    assert cosine_similarity((1.0,), (-1.7e-161,)) == -1.0


@settings(max_examples=200)
@given(text=st.text(min_size=1, max_size=120).filter(lambda s: s.split()))
def test_property_embedding_deterministic_and_self_cosine_one(text: str) -> None:
    e = DeterministicHashingEmbedder()
    v1 = e.embed(text)
    v2 = e.embed(text)
    assert v1 == v2  # determinism
    assert len(v1) == e.dimension
    # Any non-whitespace text has a non-zero vector, so self-cosine == 1.
    assert math.isclose(cosine_similarity(v1, v2), 1.0, rel_tol=1e-9)


@settings(max_examples=1000)
@given(
    a=st.lists(st.floats(-5, 5), min_size=1, max_size=8),
    b=st.lists(st.floats(-5, 5), min_size=1, max_size=8),
)
def test_property_cosine_bounded_and_symmetric(a: list[float], b: list[float]) -> None:
    if len(a) != len(b):
        with pytest.raises(ValueError):
            cosine_similarity(tuple(a), tuple(b))
        return
    s1 = cosine_similarity(tuple(a), tuple(b))
    s2 = cosine_similarity(tuple(b), tuple(a))
    assert math.isclose(s1, s2, rel_tol=1e-9, abs_tol=1e-12)  # symmetry
    # Strict closed unit interval -- the clamp must guarantee this exactly, with
    # NO epsilon slack (denormal/FP rounding previously breached 1.0; see the
    # denormal regression test above).
    assert -1.0 <= s1 <= 1.0  # bounded
