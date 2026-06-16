"""Embedding backend interface + deterministic in-memory fake (A4.2 retrieval).

What this does
--------------
Defines :class:`EmbeddingBackend`, the Protocol the retrieval layer depends on to
turn text into a fixed-length vector for dense (semantic) similarity, plus
:class:`DeterministicHashingEmbedder`, a fully in-memory, network-free embedder
used by the core and every unit test. Real deployments inject a production
encoder (e.g. a hosted embedding model) behind the SAME interface; the core never
imports a vector DB or an embedding service directly.

Why it exists / where it sits
-----------------------------
Per ``docs/research/A4-memory-and-learning-infra/SYNTHESIS.md`` L1.A4.2 retrieval
uses a hybrid dense + lexical pipeline; durable knowledge lives in a SWAPPABLE
external index (Lewis 05) so it is never trusted to model weights and is
per-tenant isolable. We honour that here by abstracting the encoder behind an
interface -- the deterministic fake keeps unit tests free of network/external
services (CLAUDE §5.5 "no network in unit tests") while preserving the real
cosine-similarity ranking behaviour DPR (07) specifies.

Security / compliance invariants upheld
---------------------------------------
* **No network in unit tests (§5.5):** the fake is pure-Python and deterministic;
  the same text always maps to the same vector, so cosine scores are reproducible
  across runs (§3.11 determinism).
* **Bounded work (§5.6):** the embedder reads at most the content the record
  already passed the boundary cap for; no unbounded external call in the core.
"""

from __future__ import annotations

import hashlib
import math
from typing import Protocol, runtime_checkable

__all__ = [
    "DeterministicHashingEmbedder",
    "EmbeddingBackend",
    "cosine_similarity",
]


@runtime_checkable
class EmbeddingBackend(Protocol):
    """Turns text into a fixed-length dense vector for semantic similarity.

    The contract: identical text -> identical vector (so retrieval is
    deterministic), and every vector has the same dimension (so cosine is
    well-defined). Real backends call a hosted encoder; the in-memory fake hashes.
    """

    @property
    def dimension(self) -> int:
        """The fixed length of every vector this backend returns (> 0)."""
        ...

    def embed(self, text: str) -> tuple[float, ...]:
        """Return the dense embedding of ``text`` as a ``dimension``-length tuple."""
        ...


def cosine_similarity(a: tuple[float, ...], b: tuple[float, ...]) -> float:
    """Return the cosine similarity of two equal-length vectors in ``[-1, 1]``.

    Cosine = dot(a, b) / (||a|| * ||b||) -- the dense-retrieval ranking score
    (DPR 07). A zero-magnitude vector has no direction, so similarity is defined
    as 0.0 (fail-safe: never divide by zero). Refuses mismatched dimensions
    (fail-closed) because comparing different-length vectors is meaningless.
    """
    if len(a) != len(b):
        # fail-closed: a dimension mismatch is a wiring bug, not a 0-similarity.
        raise ValueError("cosine_similarity requires equal-length vectors")
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0  # a zero vector has no direction -> defined as orthogonal
    return dot / (norm_a * norm_b)


class DeterministicHashingEmbedder:
    """A network-free, deterministic embedder: hashes token n-grams into buckets.

    Each whitespace token contributes a unit of weight to the bucket its
    SHA-256 hash selects; the vector is the per-bucket token counts. This is a
    bag-of-hashed-tokens model: it is deterministic, dependency-free, and gives
    *higher cosine similarity to texts that share more tokens* -- enough to drive
    and test the semantic-ranking path without a real encoder or any network.
    """

    def __init__(self, dimension: int = 64) -> None:
        """Create an embedder producing ``dimension``-length vectors (> 0)."""
        if dimension <= 0:
            raise ValueError("dimension must be a positive integer")  # fail-closed
        self._dimension = dimension

    @property
    def dimension(self) -> int:
        """The fixed vector length this embedder produces."""
        return self._dimension

    def embed(self, text: str) -> tuple[float, ...]:
        """Return a deterministic bag-of-hashed-tokens vector for ``text``.

        Lower-casing + whitespace tokenisation make the vector robust to casing
        and spacing; the SHA-256 bucket assignment is stable across processes and
        platforms, so the same text always embeds to the same vector (§3.11).
        """
        buckets = [0.0] * self._dimension
        for token in text.lower().split():
            # SHA-256 of the token -> a stable, well-distributed bucket index.
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:8], "big") % self._dimension
            buckets[index] += 1.0
        return tuple(buckets)
