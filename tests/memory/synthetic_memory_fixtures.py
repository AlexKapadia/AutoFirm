"""Synthetic fixtures + Hypothesis strategies for the memory-layer tests (A4).

Synthetic-only (CLAUDE.md §3.12): no real agents, no PII, no network. Provides a
fully-wired :class:`AgentMemoryLayer` factory, a record factory, and Hypothesis
strategies (owners, content, kinds, visibilities, whole records, and operation
sequences) for the property-based suites.
"""

from __future__ import annotations

from datetime import UTC, datetime

from hypothesis import strategies as st

from autofirm.memory.agent_memory_layer import AgentMemoryLayer
from autofirm.memory.memory_identifiers import (
    FrozenMemoryClock,
    SequentialMemoryIdGenerator,
)
from autofirm.memory.memory_record_contract import (
    MaturityTier,
    MemoryKind,
    Visibility,
)
from autofirm.memory.retrieval_ranking_score import RetrievalWeights
from autofirm.memory.semantic_embedding_backend import DeterministicHashingEmbedder

# A fixed UTC epoch every deterministic test starts from (no wall clock).
EPOCH = datetime(2025, 1, 1, tzinfo=UTC)


def make_layer(
    *,
    step_seconds: float = 3600.0,
    weights: RetrievalWeights | None = None,
    embed_dim: int = 64,
) -> AgentMemoryLayer:
    """Return a fully-wired, deterministic memory layer for tests.

    The clock advances ``step_seconds`` per read so successive writes get strictly
    increasing timestamps (exercising the recency component), and ids/embeddings
    are deterministic, so a test run is fully reproducible.
    """
    return AgentMemoryLayer(
        clock=FrozenMemoryClock(EPOCH, step_seconds=step_seconds),
        id_generator=SequentialMemoryIdGenerator(),
        embedder=DeterministicHashingEmbedder(dimension=embed_dim),
        weights=weights,
    )


# -- Hypothesis strategies --------------------------------------------------

# Bounded, distinct owner/principal ids (never empty -- the contract refuses that).
principals = st.sampled_from(["agent-a", "agent-b", "agent-c", "role-coo", "role-cto"])

# Non-empty, bounded content (the contract caps and refuses empty).
contents = st.text(min_size=1, max_size=200).filter(lambda s: s.strip() != "")

kinds = st.sampled_from(list(MemoryKind))
tiers = st.sampled_from(list(MaturityTier))
visibilities = st.sampled_from(list(Visibility))


@st.composite
def write_specs(draw: st.DrawFn) -> dict[str, object]:
    """A synthetic, valid ``remember`` keyword spec for property tests.

    Owner == written_by (a self-write always satisfies WA) so the property tests
    focus on the round-trip / scoping invariants rather than re-deriving WA, which
    has its own dedicated adversarial tests.
    """
    owner = draw(principals)
    return {
        "written_by": owner,
        "owner": owner,
        "content": draw(contents),
        "kind": draw(kinds),
        "tier": draw(tiers),
        "visibility": draw(visibilities),
    }
