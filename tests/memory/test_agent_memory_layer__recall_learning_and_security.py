"""Behaviour + red-team tests for recall ranking, learning, and poisoning (A4).

Proves teeth (CLAUDE.md §3.6): recall ranks relevant memories above irrelevant
ones and honours the limit; the reflection/learning lineage is purged on VF
(AgentPoison 13 -- a poisoned lesson cannot survive deletion of its tainted
source); shared org memory is readable cross-principal; and recall fail-closes on
a non-positive limit. Designed to KILL mutants on the ranking sort, the limit
truncation, and the shared-scope path.
"""

from __future__ import annotations

import pytest

from autofirm.memory.memory_record_contract import MaturityTier, MemoryKind, Visibility
from tests.memory.synthetic_memory_fixtures import make_layer


def test_recall_ranks_relevant_above_irrelevant() -> None:
    layer = make_layer()
    layer.remember(
        written_by="agent-a", owner="agent-a",
        content="quarterly saas pricing strategy review", kind=MemoryKind.SEMANTIC,
    )
    layer.remember(
        written_by="agent-a", owner="agent-a",
        content="office plant watering schedule", kind=MemoryKind.SEMANTIC,
    )
    hits = layer.recall(
        reader="agent-a", owner="agent-a", query="saas pricing strategy", limit=2
    )
    assert "pricing" in hits[0].record.content  # most-relevant ranked first
    assert hits[0].score.relevance > hits[1].score.relevance


def test_recall_honours_limit_truncation() -> None:
    layer = make_layer()
    for i in range(5):
        layer.remember(
            written_by="agent-a", owner="agent-a",
            content=f"memory number {i} about pricing", kind=MemoryKind.SEMANTIC,
        )
    assert len(layer.recall(reader="agent-a", owner="agent-a", query="pricing", limit=3)) == 3


def test_recall_non_positive_limit_refused_fail_closed() -> None:
    layer = make_layer()
    with pytest.raises(ValueError, match="limit must be a positive"):
        layer.recall(reader="agent-a", owner="agent-a", query="x", limit=0)


def test_importance_boosts_ranking_explainably() -> None:
    layer = make_layer()
    a = layer.remember(
        written_by="agent-a", owner="agent-a", content="alpha note", kind=MemoryKind.SEMANTIC
    )
    b = layer.remember(
        written_by="agent-a", owner="agent-a", content="beta note", kind=MemoryKind.SEMANTIC
    )
    # With b marked maximally important, it must rank first; the breakdown shows why.
    hits = layer.recall(
        reader="agent-a", owner="agent-a", query="unrelated probe", limit=2,
        importance_of={b.memory_id: 1.0, a.memory_id: 0.0},
    )
    assert hits[0].record.memory_id == b.memory_id
    assert hits[0].score.importance == 1.0


def test_learning_reflection_purged_with_poisoned_source() -> None:
    # AgentPoison (13) red-team: a reflection distilled from a tainted source must
    # not outlive the source it was derived from -- VF walks the lineage.
    layer = make_layer()
    src = layer.remember(
        written_by="agent-a", owner="agent-a",
        content="observation that turned out to be poisoned", kind=MemoryKind.EPISODIC,
    )
    lesson = layer.remember(
        written_by="agent-a", owner="agent-a",
        content="lesson learned from the observation", kind=MemoryKind.INSIGHT,
        tier=MaturityTier.EXPERIENCE, derived_from=(src.memory_id,),
    )
    proof = layer.forget(owner="agent-a", memory_id=src.memory_id)
    assert lesson.memory_id in proof  # derived insight purged with its source
    hits = layer.recall(reader="agent-a", owner="agent-a", query="lesson", limit=50)
    assert lesson.memory_id not in {h.record.memory_id for h in hits}


def test_shared_org_memory_readable_cross_principal() -> None:
    layer = make_layer()
    shared = layer.shared_scope()
    rec = layer.remember(
        written_by="role-coo", owner=shared,
        content="org-wide pricing playbook", kind=MemoryKind.PROCEDURAL,
        visibility=Visibility.SHARED,
    )
    # Any principal can recall org-shared memory.
    hits = layer.recall(reader="agent-x", owner=shared, query="pricing playbook", limit=5)
    assert rec.memory_id in {h.record.memory_id for h in hits}


def test_evolve_inherits_unspecified_fields() -> None:
    layer = make_layer()
    rec = layer.remember(
        written_by="agent-a", owner="agent-a", content="v1",
        kind=MemoryKind.PROCEDURAL, tags=("skill", "pricing"), visibility=Visibility.SHARED,
    )
    evolved = layer.evolve(written_by="agent-a", owner="agent-a", memory_id=rec.memory_id, content="v2")
    # Unspecified tags/visibility inherit from the head; kind always inherits.
    assert evolved.tags == ("skill", "pricing")
    assert evolved.visibility is Visibility.SHARED
    assert evolved.kind is MemoryKind.PROCEDURAL
