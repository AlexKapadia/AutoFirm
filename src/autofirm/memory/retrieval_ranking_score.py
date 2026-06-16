"""Explainable recency + relevance + importance retrieval score (A4.2; Gen-Agents 04).

What this does
--------------
Defines :class:`RetrievalWeights` (the TUNABLE -- never magic-constant -- score
parameters) and :func:`score_record`, which ranks a candidate memory against a
query by the Generative Agents (04) heuristic: a normalised blend of **recency**
(exponential decay since the record was written), **relevance** (cosine semantic
similarity to the query, DPR 07), and **importance** (a caller-supplied salience
in ``[0, 1]``). Each component is returned alongside the total so every retrieval
is *explainable* (CLAUDE §3.11 -- the "why" matches the "what").

Why it exists / where it sits
-----------------------------
Per ``docs/research/A4-memory-and-learning-infra/SYNTHESIS.md`` L1.A4.2 the
retriever ranks by "the explainable recency/relevance/importance score
(Generative Agents 04), weights/decay as TUNED PARAMETERS, never magic
constants." The decay base and component weights live in :class:`RetrievalWeights`
so they are explicit, defaulted to the paper's values, and tunable per golden set
-- the synthesis's binding requirement against overfitting (CLAUDE §3.9).

Security / compliance invariants upheld
---------------------------------------
* **Determinism (§3.11):** the score is a pure function of (record, query vector,
  reference time, weights). No wall-clock, no randomness -- identical inputs give
  an identical, explainable breakdown every run.
* **Bounded / fail-closed (§5.6):** weights and importance are validated to their
  legal ranges at the boundary; an out-of-range decay base or weight is refused.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from autofirm.memory.semantic_embedding_backend import cosine_similarity

__all__ = ["RetrievalScore", "RetrievalWeights", "score_record"]

# Generative Agents (04) recency decay base per hour: 0.995. Kept as a NAMED,
# overridable default (RetrievalWeights) -- never a bare magic number in the
# scoring path -- so it can be tuned per golden set without editing logic (§3.9).
_DEFAULT_DECAY_BASE = 0.995


@dataclass(frozen=True)
class RetrievalWeights:
    """Tunable weights + decay for the recency/relevance/importance blend (04).

    Defaults reproduce the Generative Agents (04) equal-weight, 0.995/hr-decay
    setting. ``decay_base`` is the per-hour exponential-decay base (0 < b <= 1);
    the three weights need not sum to 1 (the score is reported raw and per-
    component so it stays explainable). All are validated fail-closed.
    """

    recency_weight: float = 1.0
    relevance_weight: float = 1.0
    importance_weight: float = 1.0
    decay_base: float = _DEFAULT_DECAY_BASE

    def __post_init__(self) -> None:
        """Fail-closed: refuse out-of-range weights / decay at construction (§5.6)."""
        for name, w in (
            ("recency_weight", self.recency_weight),
            ("relevance_weight", self.relevance_weight),
            ("importance_weight", self.importance_weight),
        ):
            if w < 0.0:
                raise ValueError(f"{name} must be >= 0")  # fail-closed: negative weight
        if not 0.0 < self.decay_base <= 1.0:
            # A decay base outside (0, 1] is not an exponential decay -> refuse.
            raise ValueError("decay_base must be in the interval (0, 1]")


@dataclass(frozen=True)
class RetrievalScore:
    """The explainable breakdown of one record's retrieval score.

    ``total`` is the weighted blend; ``recency`` / ``relevance`` / ``importance``
    are the three normalised components (each in ``[0, 1]``) so a caller can
    justify *why* a record ranked where it did (CLAUDE §3.11 explainability).
    """

    total: float
    recency: float
    relevance: float
    importance: float


def _recency_factor(written_at: datetime, reference: datetime, decay_base: float) -> float:
    """Exponential recency in ``[0, 1]``: ``decay_base ** hours_since_written``.

    A record written AT the reference time scores 1.0; older records decay toward
    0. A record written in the future relative to ``reference`` (clock skew /
    out-of-order replay) is clamped to 1.0 rather than scoring > 1 -- fail-safe:
    recency is a fraction, never an amplifier.
    """
    elapsed_hours = (reference - written_at).total_seconds() / 3600.0
    if elapsed_hours <= 0.0:
        return 1.0  # clamp future/just-written records to the max (no >1 score)
    return decay_base**elapsed_hours


def score_record(
    *,
    record_vector: tuple[float, ...],
    query_vector: tuple[float, ...],
    written_at: datetime,
    importance: float,
    reference_time: datetime,
    weights: RetrievalWeights,
) -> RetrievalScore:
    """Return the explainable recency/relevance/importance score (Gen-Agents 04).

    ``relevance`` is cosine(record, query) clamped to ``[0, 1]`` (negative cosine
    -> 0, i.e. "not relevant"); ``recency`` is the exponential decay factor; and
    ``importance`` is the caller's salience, validated to ``[0, 1]`` fail-closed.
    The total is the weight-blended sum, kept additive and per-component so the
    result is fully explainable.
    """
    if not 0.0 <= importance <= 1.0:
        # fail-closed: importance is a normalised salience; out-of-range is a bug.
        raise ValueError("importance must be in the interval [0, 1]")
    relevance = max(0.0, cosine_similarity(record_vector, query_vector))
    recency = _recency_factor(written_at, reference_time, weights.decay_base)
    total = (
        weights.recency_weight * recency
        + weights.relevance_weight * relevance
        + weights.importance_weight * importance
    )
    return RetrievalScore(
        total=total, recency=recency, relevance=relevance, importance=importance
    )
