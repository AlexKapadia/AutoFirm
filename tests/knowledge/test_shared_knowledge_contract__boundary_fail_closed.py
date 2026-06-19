"""Adversarial + property tests for the shared-knowledge entry boundary (W2/§5.6).

Proves teeth (CLAUDE.md §3.6): the entry refuses every malformed shape at the
boundary -- empty/over-cap value, blank label/subject, too many tags, non-positive
limit, inverted event-time interval, inverted transaction-time interval, over-cap
lineage, out-of-set taint origin. Designed to KILL mutants on the value cap, the
limit guard, and BOTH temporal-ordering guards.
"""

from __future__ import annotations

import pytest
from hypothesis import given
from hypothesis import strategies as st
from pydantic import ValidationError

from autofirm.knowledge.shared_knowledge_contract import (
    MAX_TAGS,
    MAX_VALUE_BYTES,
    KnowledgeProvenance,
    TaintOrigin,
)
from tests.knowledge.synthetic_knowledge_fixtures import at_day, make_entry


def test_valid_entry_constructs_with_carried_taint() -> None:
    entry = make_entry(origin=TaintOrigin.UNTRUSTED)
    assert entry.origin is TaintOrigin.UNTRUSTED  # taint is set at write time
    assert entry.invalid_at is None and entry.superseded_at is None  # live + valid


def test_empty_value_is_refused_fail_closed() -> None:
    with pytest.raises(ValidationError, match="value must be non-empty"):
        make_entry(value="")


def test_over_cap_value_is_refused_fail_closed() -> None:
    with pytest.raises(ValidationError, match="exceeds MAX_VALUE_BYTES"):
        make_entry(value="x" * (MAX_VALUE_BYTES + 1))


def test_value_exactly_at_cap_is_accepted() -> None:
    # Boundary-exact: exactly MAX bytes passes; one more (above) is refused.
    entry = make_entry(value="x" * MAX_VALUE_BYTES)
    assert len(entry.value.encode("utf-8")) == MAX_VALUE_BYTES


def test_multibyte_value_counts_bytes_not_chars() -> None:
    # 2-byte char repeated (MAX//2 + 1) times exceeds the BYTE cap though the char
    # count is half -- proves the cap is on bytes, killing a len()-on-str mutant.
    with pytest.raises(ValidationError, match="exceeds MAX_VALUE_BYTES"):
        make_entry(value="é" * (MAX_VALUE_BYTES // 2 + 1))


@pytest.mark.parametrize("bad_limit", [0, -1, -512])
def test_non_positive_limit_is_refused(bad_limit: int) -> None:
    with pytest.raises(ValidationError, match="limit must be a positive"):
        make_entry(limit=bad_limit)


def test_limit_one_is_the_boundary_accepted() -> None:
    assert make_entry(limit=1).limit == 1  # just-on the positive boundary


def test_too_many_tags_refused_one_over_boundary() -> None:
    over = tuple(f"t{i}" for i in range(MAX_TAGS + 1))
    with pytest.raises(ValidationError, match="MAX_TAGS"):
        make_entry(tags=over)


def test_exactly_max_tags_accepted() -> None:
    at_cap = tuple(f"t{i}" for i in range(MAX_TAGS))
    assert len(make_entry(tags=at_cap).tags) == MAX_TAGS


def test_invalid_at_equal_to_valid_at_is_refused() -> None:
    # Zero-width event interval is malformed (a fact cannot stop being true the
    # instant it starts) -- kills a `<=` -> `<` mutant on the event-time guard.
    with pytest.raises(ValidationError, match="strictly after valid_at"):
        make_entry(valid_at=at_day(5), invalid_at=at_day(5))


def test_invalid_at_before_valid_at_is_refused() -> None:
    with pytest.raises(ValidationError, match="strictly after valid_at"):
        make_entry(valid_at=at_day(5), invalid_at=at_day(4))


def test_invalid_at_strictly_after_valid_at_accepted() -> None:
    entry = make_entry(valid_at=at_day(5), invalid_at=at_day(6))
    assert entry.invalid_at == at_day(6)


def test_superseded_at_equal_to_recorded_at_is_refused() -> None:
    # Kills a `<=` -> `<` mutant on the transaction-time guard.
    with pytest.raises(ValidationError, match="strictly after recorded_at"):
        make_entry(recorded_at=at_day(3), superseded_at=at_day(3))


def test_superseded_at_before_recorded_at_is_refused() -> None:
    with pytest.raises(ValidationError, match="strictly after recorded_at"):
        make_entry(recorded_at=at_day(3), superseded_at=at_day(2))


def test_blank_label_is_refused() -> None:
    with pytest.raises(ValidationError):
        make_entry(label="   ")  # strip_whitespace -> empty -> min_length fails


def test_origin_is_immutable_no_silent_elevation() -> None:
    # The frozen model refuses mutation: an untrusted entry can never be relabelled
    # TRUSTED after the fact (the core write-time-taint invariant, B6).
    entry = make_entry(origin=TaintOrigin.UNTRUSTED)
    with pytest.raises(ValidationError):
        entry.origin = TaintOrigin.TRUSTED  # type: ignore[misc]


def test_over_cap_lineage_refused() -> None:
    over = tuple(f"k{i}" for i in range(MAX_TAGS + 1))
    with pytest.raises(ValidationError, match="derived_from exceeds MAX_TAGS"):
        KnowledgeProvenance(written_by="a", source_provider="p", derived_from=over)


@given(
    valid_day=st.integers(min_value=0, max_value=100),
    span=st.integers(min_value=1, max_value=100),
)
def test_property_any_strictly_ordered_event_interval_constructs(
    valid_day: int, span: int
) -> None:
    # Property: ANY interval with invalid_at strictly after valid_at is accepted and
    # preserves the values exactly -- generality over arbitrary valid timelines.
    entry = make_entry(valid_at=at_day(valid_day), invalid_at=at_day(valid_day + span))
    assert entry.valid_at == at_day(valid_day)
    assert entry.invalid_at == at_day(valid_day + span)


@given(equal_day=st.integers(min_value=0, max_value=100))
def test_property_zero_or_negative_event_interval_always_refused(equal_day: int) -> None:
    # Property: NO non-positive-width event interval is ever accepted (the guard
    # holds for every instant, not just the hand-picked example above).
    with pytest.raises(ValidationError):
        make_entry(valid_at=at_day(equal_day), invalid_at=at_day(equal_day))
