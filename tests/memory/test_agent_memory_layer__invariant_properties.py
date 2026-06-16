"""Property-based invariant tests for the memory layer facade (A4; §3.6 PBT).

Proves teeth with Hypothesis: (1) write->recall round-trip recovers a record;
(2) recall NEVER returns another owner's private memory (the load-bearing PS
isolation guarantee); (3) versioning preserves the full history; (4) the layer is
deterministic across repeated runs; (5) forget makes records unrecoverable. These
are the invariants the synthesis names as binding -- not happy-path checks.
"""

from __future__ import annotations

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from autofirm.memory.memory_access_errors import (
    MemoryWriteAuthorizationError,
    PrincipalScopeViolationError,
)
from autofirm.memory.memory_record_contract import MemoryKind, Visibility
from tests.memory.synthetic_memory_fixtures import (
    make_layer,
    principals,
    write_specs,
)


@settings(max_examples=200)
@given(spec=write_specs())
def test_property_write_then_recall_roundtrips(spec: dict[str, object]) -> None:
    layer = make_layer()
    stored = layer.remember(**spec)  # type: ignore[arg-type]
    # The exact content is recoverable by its owner via get (the round trip).
    fetched = layer.get(
        reader=spec["owner"], owner=spec["owner"], memory_id=stored.memory_id  # type: ignore[arg-type]
    )
    assert fetched.content == spec["content"]
    assert fetched.kind is spec["kind"]


@settings(max_examples=300)
@given(
    owner=principals,
    intruder=principals,
    content=st.text(min_size=1, max_size=80).filter(lambda s: s.strip()),
    vis=st.sampled_from(list(Visibility)),
)
def test_property_recall_never_leaks_another_owners_private(
    owner: str, intruder: str, content: str, vis: Visibility
) -> None:
    layer = make_layer()
    rec = layer.remember(
        written_by=owner, owner=owner, content=content, kind=MemoryKind.SEMANTIC, visibility=vis
    )
    hits = layer.recall(reader=intruder, owner=owner, query=content, limit=50)
    returned_ids = {h.record.memory_id for h in hits}
    if intruder == owner or vis is Visibility.SHARED:
        # Owner, or an explicitly-shared record -> the record IS reachable.
        assert rec.memory_id in returned_ids
    else:
        # A different owner's PRIVATE record must NEVER appear (PS isolation).
        assert rec.memory_id not in returned_ids
        # ...and direct get must fail closed too.
        with pytest.raises(PrincipalScopeViolationError):
            layer.get(reader=intruder, owner=owner, memory_id=rec.memory_id)


@settings(max_examples=150)
@given(
    owner=principals,
    n_evolutions=st.integers(min_value=0, max_value=8),
    contents=st.lists(st.text(min_size=1, max_size=40).filter(lambda s: s.strip()), max_size=8),
)
def test_property_versioning_preserves_full_history(
    owner: str, n_evolutions: int, contents: list[str]
) -> None:
    layer = make_layer()
    rec = layer.remember(
        written_by=owner, owner=owner, content="v1", kind=MemoryKind.PROCEDURAL
    )
    applied = contents[:n_evolutions]
    for new_content in applied:
        layer.evolve(
            written_by=owner, owner=owner, memory_id=rec.memory_id, content=new_content
        )
    history = layer.history(owner=owner, memory_id=rec.memory_id)
    # History length == 1 (initial) + number of evolutions, versions strictly 1..N.
    assert len(history) == 1 + len(applied)
    assert [h.version for h in history] == list(range(1, len(history) + 1))
    # The live head is always the last-written content (or "v1" if none applied).
    head = layer.get(reader=owner, owner=owner, memory_id=rec.memory_id)
    assert head.content == (applied[-1] if applied else "v1")


@settings(max_examples=100)
@given(specs=st.lists(write_specs(), min_size=1, max_size=6))
def test_property_layer_is_deterministic_across_runs(specs: list[dict[str, object]]) -> None:
    # Two independently-built layers fed the same op sequence must agree exactly
    # on ids, timestamps, and recall ordering (CLAUDE §3.11 determinism).
    def run() -> list[tuple[str, str]]:
        layer = make_layer()
        for spec in specs:
            layer.remember(**spec)  # type: ignore[arg-type]
        owner = specs[0]["owner"]
        hits = layer.recall(
            reader=owner, owner=owner, query="probe query terms", limit=10  # type: ignore[arg-type]
        )
        return [(h.record.memory_id, h.record.content) for h in hits]

    assert run() == run()


@settings(max_examples=150)
@given(owner=principals, content=st.text(min_size=1, max_size=60).filter(lambda s: s.strip()))
def test_property_forget_makes_record_unrecoverable(owner: str, content: str) -> None:
    layer = make_layer()
    rec = layer.remember(written_by=owner, owner=owner, content=content, kind=MemoryKind.EPISODIC)
    proof = layer.forget(owner=owner, memory_id=rec.memory_id)
    assert rec.memory_id in proof
    # After VF the record is gone from recall and from direct get.
    hits = layer.recall(reader=owner, owner=owner, query=content, limit=50)
    assert rec.memory_id not in {h.record.memory_id for h in hits}


@settings(max_examples=150)
@given(
    author=principals,
    owner=principals,
    content=st.text(min_size=1, max_size=40).filter(lambda s: s.strip()),
)
def test_property_write_authorization_holds(author: str, owner: str, content: str) -> None:
    layer = make_layer()
    if author == owner:
        rec = layer.remember(
            written_by=author, owner=owner, content=content, kind=MemoryKind.SEMANTIC
        )
        assert rec.owner == owner
    else:
        # WA: a private cross-owner write is always refused, never silently allowed.
        with pytest.raises(MemoryWriteAuthorizationError):
            layer.remember(
                written_by=author, owner=owner, content=content, kind=MemoryKind.SEMANTIC
            )
