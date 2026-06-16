"""AutoFirm memory & learning layer (A4): persistent, evolving agent/org memory.

Implements the A4-recommended design (``docs/research/A4-memory-and-learning-
infra/SYNTHESIS.md``): external, swappable memory (NOT context-stuffing) with an
explainable recency/relevance/importance retriever, a two-axis CoALA x maturity
taxonomy, an append-only/versioned record so memory evolves without losing
history, and the five fail-closed governance primitives (WA / PV / PS / RB / VF).

The runtime core never imports a vector DB, embedding service, or any network
client directly -- the embedding backend is injected behind
:class:`autofirm.memory.semantic_embedding_backend.EmbeddingBackend`, and the
deterministic in-memory store keeps unit tests network-free (CLAUDE §5.5).
"""
