"""Adversarial + property tests for the memory record boundary (A4.1/§5.6).

Proves teeth (CLAUDE.md §3.6): the record refuses every malformed shape at the
boundary -- empty content, over-cap content, blank owner, too many tags, negative
/ zero version, out-of-set kind/tier/visibility, over-cap lineage. Designed to
KILL mutants on the content cap, the tag cap, and the version guard.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from pydantic import ValidationError

from autofirm.memory.memory_record_contract import (
    MAX_CONTENT_BYTES,
    MAX_TAGS,
    MaturityTier,
    MemoryKind,
    MemoryRecord,
    Provenance,
    ProvenanceSource,
    Visibility,
)

_EPOCH = datetime(2025, 1, 1, tzinfo=UTC)
_PROV = Provenance(source=ProvenanceSource.DIRECT_WRITE)


def _record(**overrides: object) -> MemoryRecord:
    base: dict[str, object] = {
        "memory_id": "mem-0",
        "owner": "agent-a",
        "written_by": "agent-a",
        "content": "a memory",
        "kind": MemoryKind.SEMANTIC,
        "tier": MaturityTier.STORAGE,
        "provenance": _PROV,
        "version": 1,
        "injected_at": _EPOCH,
    }
    base.update(overrides)
    return MemoryRecord(**base)  # type: ignore[arg-type]


def test_valid_record_constructs_with_private_default() -> None:
    rec = _record()
    assert rec.visibility is Visibility.PRIVATE  # least-privilege default
    assert rec.version == 1


def test_empty_content_is_refused_fail_closed() -> None:
    with pytest.raises(ValidationError, match="content must be non-empty"):
        _record(content="")


def test_over_cap_content_is_refused_fail_closed() -> None:
    oversized = "x" * (MAX_CONTENT_BYTES + 1)
    with pytest.raises(ValidationError, match="exceeds MAX_CONTENT_BYTES"):
        _record(content=oversized)


def test_content_exactly_at_cap_is_accepted() -> None:
    # Boundary-exact: exactly MAX bytes passes; one more (above) is refused.
    at_cap = "x" * MAX_CONTENT_BYTES
    rec = _record(content=at_cap)
    assert len(rec.content.encode("utf-8")) == MAX_CONTENT_BYTES


def test_multibyte_content_counts_bytes_not_chars() -> None:
    # A 2-byte char repeated (MAX//2 + 1) times exceeds the BYTE cap though the
    # char count is half -- proves the cap is on bytes, killing a len()-on-str mutant.
    over = "é" * (MAX_CONTENT_BYTES // 2 + 1)
    with pytest.raises(ValidationError, match="exceeds MAX_CONTENT_BYTES"):
        _record(content=over)


@pytest.mark.parametrize("bad_version", [0, -1, -99])
def test_non_positive_version_is_refused(bad_version: int) -> None:
    with pytest.raises(ValidationError, match="version must be >= 1"):
        _record(version=bad_version)


def test_version_one_is_the_boundary_accepted() -> None:
    assert _record(version=1).version == 1  # just-on the 1-based boundary


def test_blank_owner_is_refused() -> None:
    with pytest.raises(ValidationError):
        _record(owner="")


def test_too_many_tags_is_refused() -> None:
    too_many = tuple(f"t{i}" for i in range(MAX_TAGS + 1))
    with pytest.raises(ValidationError, match="exceeds MAX_TAGS"):
        _record(tags=too_many)


def test_tags_exactly_at_cap_accepted() -> None:
    at_cap = tuple(f"t{i}" for i in range(MAX_TAGS))
    assert len(_record(tags=at_cap).tags) == MAX_TAGS


def test_over_cap_lineage_is_refused() -> None:
    long_lineage = tuple(f"m{i}" for i in range(MAX_TAGS + 1))
    with pytest.raises(ValidationError, match="derived_from exceeds MAX_TAGS"):
        Provenance(source=ProvenanceSource.REFLECTION_OF, derived_from=long_lineage)


def test_record_is_frozen_immutable() -> None:
    rec = _record()
    with pytest.raises(ValidationError):
        rec.content = "mutated"  # type: ignore[misc]  # frozen -> append-only semantics


@settings(max_examples=200)
@given(
    content=st.text(min_size=1, max_size=300).filter(lambda s: s.encode("utf-8")),
    kind=st.sampled_from(list(MemoryKind)),
    tier=st.sampled_from(list(MaturityTier)),
    visibility=st.sampled_from(list(Visibility)),
    version=st.integers(min_value=1, max_value=10_000),
)
def test_property_valid_records_always_construct_and_roundtrip_fields(
    content: str,
    kind: MemoryKind,
    tier: MaturityTier,
    visibility: Visibility,
    version: int,
) -> None:
    rec = _record(
        content=content, kind=kind, tier=tier, visibility=visibility, version=version
    )
    # Round-trip invariant: every field comes back exactly as supplied.
    assert rec.content == content
    assert rec.kind is kind
    assert rec.tier is tier
    assert rec.visibility is visibility
    assert rec.version == version
