"""Synthetic builders for the W2 shared-knowledge tests (no network, no real data).

All fixtures are SYNTHETIC (CLAUDE.md §3.12) and deterministic. ``make_entry`` is a
keyword-only builder with sensible bi-temporal defaults so each test states only the
field it is probing; ``make_graph`` returns a fresh in-memory backend. Timestamps
are fixed offsets from a synthetic epoch so as-of-time tests are reproducible.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from autofirm.knowledge.knowledge_graph_backend_protocol import (
    InMemoryBitemporalKnowledgeGraph,
)
from autofirm.knowledge.shared_knowledge_contract import (
    KnowledgeProvenance,
    SharedKnowledgeEntry,
    TaintOrigin,
)

# Synthetic epoch; tests build instants as EPOCH + N days so ordering is obvious.
EPOCH = datetime(2025, 1, 1, tzinfo=UTC)


def at_day(day: int) -> datetime:
    """Return EPOCH + ``day`` days (a readable synthetic instant)."""
    return EPOCH + timedelta(days=day)


def make_provenance(
    *,
    written_by: str = "agent-a",
    source_provider: str = "provider-x",
    derived_from: tuple[str, ...] = (),
) -> KnowledgeProvenance:
    """Build a synthetic provenance record (defaults to a trusted provider-X write)."""
    return KnowledgeProvenance(
        written_by=written_by,
        source_provider=source_provider,
        derived_from=derived_from,
    )


def make_entry(  # noqa: PLR0913 -- keyword-only builder mirroring the entry fields
    *,
    entry_id: str = "k-0",
    subject: str = "pricing_model",
    label: str = "pricing_model",
    description: str = "the current pricing model",
    value: str = "monthly subscription at fixed tiers",
    limit: int = 512,
    origin: TaintOrigin = TaintOrigin.TRUSTED,
    provenance: KnowledgeProvenance | None = None,
    tags: tuple[str, ...] = (),
    valid_at: datetime | None = None,
    invalid_at: datetime | None = None,
    recorded_at: datetime | None = None,
    superseded_at: datetime | None = None,
) -> SharedKnowledgeEntry:
    """Build a synthetic shared-knowledge entry with valid bi-temporal defaults."""
    return SharedKnowledgeEntry(
        entry_id=entry_id,
        subject=subject,
        label=label,
        description=description,
        value=value,
        limit=limit,
        origin=origin,
        provenance=provenance if provenance is not None else make_provenance(),
        tags=tags,
        valid_at=valid_at if valid_at is not None else at_day(1),
        invalid_at=invalid_at,
        recorded_at=recorded_at if recorded_at is not None else at_day(1),
        superseded_at=superseded_at,
    )


def make_graph() -> InMemoryBitemporalKnowledgeGraph:
    """Return a fresh, empty in-memory bi-temporal backend."""
    return InMemoryBitemporalKnowledgeGraph()
