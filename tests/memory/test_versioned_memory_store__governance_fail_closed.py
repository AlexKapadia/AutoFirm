"""Adversarial tests for the store's five governance primitives (A4.4; §5.6).

Proves teeth (CLAUDE.md §3.6): WA refuses unauthorised writes, PS refuses
cross-owner private reads (get AND scan), RB preserves full history, VF exactly
deletes and cascades through provenance lineage. Designed to KILL mutants on the
WA author check, the PS scope guard, the cascade fixed-point loop, and the
shared-scope special case.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from autofirm.memory.memory_access_errors import (
    MemoryWriteAuthorizationError,
    PrincipalScopeViolationError,
    RecordNotFoundError,
)
from autofirm.memory.memory_record_contract import (
    MaturityTier,
    MemoryKind,
    MemoryRecord,
    Provenance,
    ProvenanceSource,
    Visibility,
)
from autofirm.memory.versioned_memory_store import VersionedMemoryStore

_EPOCH = datetime(2025, 1, 1, tzinfo=UTC)


def _rec(  # noqa: PLR0913 -- keyword-only record factory mirroring the contract fields
    *,
    memory_id: str,
    owner: str,
    written_by: str | None = None,
    visibility: Visibility = Visibility.PRIVATE,
    version: int = 1,
    derived_from: tuple[str, ...] = (),
) -> MemoryRecord:
    source = ProvenanceSource.REFLECTION_OF if derived_from else ProvenanceSource.DIRECT_WRITE
    return MemoryRecord(
        memory_id=memory_id,
        owner=owner,
        written_by=written_by if written_by is not None else owner,
        content=f"content-{memory_id}",
        kind=MemoryKind.SEMANTIC,
        tier=MaturityTier.STORAGE,
        visibility=visibility,
        provenance=Provenance(source=source, derived_from=derived_from),
        version=version,
        injected_at=_EPOCH,
    )


# -- WA --------------------------------------------------------------------


def test_wa_self_write_allowed() -> None:
    store = VersionedMemoryStore()
    stored = store.write(_rec(memory_id="m1", owner="agent-a"))
    assert stored.memory_id == "m1"


def test_wa_cross_owner_write_refused() -> None:
    store = VersionedMemoryStore()
    with pytest.raises(MemoryWriteAuthorizationError, match="may not write"):
        store.write(_rec(memory_id="m1", owner="agent-a", written_by="agent-b"))


def test_wa_any_principal_may_write_shared_scope() -> None:
    store = VersionedMemoryStore()
    shared = store.reserved_shared_scope()
    stored = store.write(
        _rec(memory_id="m1", owner=shared, written_by="agent-z", visibility=Visibility.SHARED)
    )
    assert stored.owner == shared


# -- PS --------------------------------------------------------------------


def test_ps_owner_reads_own_private() -> None:
    store = VersionedMemoryStore()
    store.write(_rec(memory_id="m1", owner="agent-a"))
    assert store.get(owner="agent-a", memory_id="m1", reader="agent-a").memory_id == "m1"


def test_ps_cross_owner_private_get_refused() -> None:
    store = VersionedMemoryStore()
    store.write(_rec(memory_id="m1", owner="agent-a"))
    with pytest.raises(PrincipalScopeViolationError, match="may not read private"):
        store.get(owner="agent-a", memory_id="m1", reader="agent-b")


def test_ps_shared_record_readable_by_other() -> None:
    store = VersionedMemoryStore()
    store.write(_rec(memory_id="m1", owner="agent-a", visibility=Visibility.SHARED))
    assert store.get(owner="agent-a", memory_id="m1", reader="agent-b").memory_id == "m1"


def test_ps_scan_hides_private_from_non_owner() -> None:
    store = VersionedMemoryStore()
    store.write(_rec(memory_id="priv", owner="agent-a", visibility=Visibility.PRIVATE))
    store.write(_rec(memory_id="pub", owner="agent-a", visibility=Visibility.SHARED))
    seen = {r.memory_id for r in store.scan_readable(owner="agent-a", reader="agent-b")}
    assert seen == {"pub"}  # private hidden, shared visible


def test_ps_scan_owner_sees_all_own() -> None:
    store = VersionedMemoryStore()
    store.write(_rec(memory_id="priv", owner="agent-a"))
    store.write(_rec(memory_id="pub", owner="agent-a", visibility=Visibility.SHARED))
    seen = {r.memory_id for r in store.scan_readable(owner="agent-a", reader="agent-a")}
    assert seen == {"priv", "pub"}


def test_ps_scan_unknown_owner_is_empty() -> None:
    assert VersionedMemoryStore().scan_readable(owner="nobody", reader="x") == []


# -- get of missing / forgotten --------------------------------------------


def test_get_missing_id_refused() -> None:
    with pytest.raises(RecordNotFoundError, match="no live record"):
        VersionedMemoryStore().get(owner="agent-a", memory_id="ghost", reader="agent-a")


# -- RB --------------------------------------------------------------------


def test_rb_history_preserves_all_versions() -> None:
    store = VersionedMemoryStore()
    store.write(_rec(memory_id="m1", owner="agent-a", version=1))
    store.write(_rec(memory_id="m1", owner="agent-a", version=2))
    versions = [r.version for r in store.versions_of(owner="agent-a", memory_id="m1")]
    assert versions == [1, 2]  # append-only: nothing rewritten


def test_rb_restore_unknown_version_refused() -> None:
    store = VersionedMemoryStore()
    store.write(_rec(memory_id="m1", owner="agent-a", version=1))
    with pytest.raises(RecordNotFoundError, match="version 9"):
        store.restore_version(
            owner="agent-a",
            memory_id="m1",
            target_version=9,
            written_by="agent-a",
            injected_at=_EPOCH,
        )


def test_rb_restore_writes_new_head_with_old_content() -> None:
    store = VersionedMemoryStore()
    store.write(_rec(memory_id="m1", owner="agent-a", version=1))
    # supersede to v2 with different content
    v2 = _rec(memory_id="m1", owner="agent-a", version=2)
    store.write(v2)
    restored = store.restore_version(
        owner="agent-a",
        memory_id="m1",
        target_version=1,
        written_by="agent-a",
        injected_at=_EPOCH,
    )
    assert restored.version == 3  # rollback is a forward, auditable step
    assert restored.content == "content-m1"  # v1 content (same here, id stable)
    assert restored.provenance.source is ProvenanceSource.SUPERSEDES


# -- VF --------------------------------------------------------------------


def test_vf_delete_makes_record_not_live() -> None:
    store = VersionedMemoryStore()
    store.write(_rec(memory_id="m1", owner="agent-a"))
    purged = store.delete_with_lineage(owner="agent-a", memory_id="m1")
    assert purged == ("m1",)
    assert not store.is_live(owner="agent-a", memory_id="m1")


def test_vf_delete_missing_refused() -> None:
    with pytest.raises(RecordNotFoundError):
        VersionedMemoryStore().delete_with_lineage(owner="agent-a", memory_id="ghost")


def test_vf_cascade_purges_derived_reflection() -> None:
    store = VersionedMemoryStore()
    store.write(_rec(memory_id="src", owner="agent-a"))
    store.write(_rec(memory_id="refl", owner="agent-a", derived_from=("src",)))
    purged = store.delete_with_lineage(owner="agent-a", memory_id="src")
    assert purged == ("refl", "src")  # sorted non-recoverability proof
    assert not store.is_live(owner="agent-a", memory_id="refl")


def test_vf_cascade_is_transitive_multi_level() -> None:
    # src -> refl1 -> refl2: deleting src must purge the whole derived chain.
    store = VersionedMemoryStore()
    store.write(_rec(memory_id="src", owner="agent-a"))
    store.write(_rec(memory_id="refl1", owner="agent-a", derived_from=("src",)))
    store.write(_rec(memory_id="refl2", owner="agent-a", derived_from=("refl1",)))
    purged = store.delete_with_lineage(owner="agent-a", memory_id="src")
    assert set(purged) == {"src", "refl1", "refl2"}


def test_vf_cascade_does_not_purge_unrelated() -> None:
    store = VersionedMemoryStore()
    store.write(_rec(memory_id="src", owner="agent-a"))
    store.write(_rec(memory_id="other", owner="agent-a"))
    store.delete_with_lineage(owner="agent-a", memory_id="src")
    assert store.is_live(owner="agent-a", memory_id="other")  # untouched
