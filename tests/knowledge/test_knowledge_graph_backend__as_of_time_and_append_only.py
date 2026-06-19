"""As-of-time correctness + append-only tests for the bi-temporal backend (W2/§3.11).

Proves teeth (CLAUDE.md §3.6): the headline guarantee is a PROPERTY -- no as-of-time
query ever returns a fact recorded AFTER the query instant, nor one whose
event-validity excludes it, and invalidation is logical (history survives). Designed
to KILL mutants on each of the four bi-temporal comparison operators and on the
append-only / fail-closed write+invalidate guards.
"""

from __future__ import annotations

import pytest
from hypothesis import given
from hypothesis import strategies as st

from autofirm.knowledge.knowledge_graph_backend_protocol import (
    InMemoryBitemporalKnowledgeGraph,
    KnowledgeBackendError,
)
from tests.knowledge.synthetic_knowledge_fixtures import at_day, make_entry, make_graph


def test_query_before_record_time_returns_nothing() -> None:
    # A fact recorded on day 5 is INVISIBLE to a query as-of day 4: the store did
    # not know it yet. Kills a `recorded_at <= as_of` -> `>=`/drop mutant.
    g = make_graph()
    g.write(make_entry(entry_id="k1", recorded_at=at_day(5), valid_at=at_day(1)))
    assert g.query_as_of(subject="pricing_model", as_of=at_day(4)) == ()


def test_query_on_record_day_returns_the_fact() -> None:
    # Boundary-exact: as_of == recorded_at is INSIDE the known window (<=).
    g = make_graph()
    entry = make_entry(entry_id="k1", recorded_at=at_day(5), valid_at=at_day(5))
    g.write(entry)
    assert g.query_as_of(subject="pricing_model", as_of=at_day(5)) == (entry,)


def test_query_before_event_validity_returns_nothing() -> None:
    # Recorded early (day 1) but only TRUE from day 10: a query as-of day 5 must not
    # surface it. Kills a `valid_at <= as_of` -> drop mutant (separates txn vs event).
    g = make_graph()
    g.write(make_entry(entry_id="k1", recorded_at=at_day(1), valid_at=at_day(10)))
    assert g.query_as_of(subject="pricing_model", as_of=at_day(5)) == ()


def test_query_after_event_invalidation_returns_nothing() -> None:
    # Valid [1,8); a query as-of day 8 (the invalid instant) must NOT return it.
    # Kills an `invalid_at > as_of` -> `>=` mutant.
    g = make_graph()
    g.write(make_entry(entry_id="k1", valid_at=at_day(1), invalid_at=at_day(8)))
    assert g.query_as_of(subject="pricing_model", as_of=at_day(8)) == ()
    # ...but day 7 (one before) still surfaces it.
    assert len(g.query_as_of(subject="pricing_model", as_of=at_day(7))) == 1


def test_query_after_transaction_supersession_returns_nothing() -> None:
    # superseded_at on day 6; a query as-of day 6 must not return the closed record.
    # Kills a `superseded_at > as_of` -> `>=` mutant.
    g = make_graph()
    g.write(make_entry(entry_id="k1", recorded_at=at_day(1)))
    g.invalidate(entry_id="k1", superseded_at=at_day(6))
    assert g.query_as_of(subject="pricing_model", as_of=at_day(6)) == ()
    assert len(g.query_as_of(subject="pricing_model", as_of=at_day(5))) == 1


def test_supersession_preserves_history_in_append_only_log() -> None:
    g = make_graph()
    g.write(make_entry(entry_id="k1", value="old price", recorded_at=at_day(1)))
    g.supersede(
        entry_id="k1",
        replacement=make_entry(entry_id="k2", value="new price", recorded_at=at_day(6)),
        superseded_at=at_day(6),
    )
    # Append-only: both records still in history; only the new one is live.
    history = g.history()
    assert len(history) == 2
    assert {e.value for e in history} == {"old price", "new price"}
    assert {e.value for e in g.all_live()} == {"new price"}
    # As-of day 3 still sees the OLD value (what the org knew then).
    assert g.query_as_of(subject="pricing_model", as_of=at_day(3))[0].value == "old price"
    # As-of day 7 sees the NEW value, never the stale one.
    assert g.query_as_of(subject="pricing_model", as_of=at_day(7))[0].value == "new price"


def test_duplicate_live_write_is_refused_with_exact_message() -> None:
    # Exact-message assertion KILLS an error-text mutant (the message names the id).
    g = make_graph()
    g.write(make_entry(entry_id="k1"))
    with pytest.raises(KnowledgeBackendError) as exc:
        g.write(make_entry(entry_id="k1", value="rival value"))
    assert str(exc.value) == "entry_id 'k1' already has a live record"


def test_write_of_pre_closed_entry_is_refused_with_exact_message() -> None:
    g = make_graph()
    closed = make_entry(entry_id="k1", recorded_at=at_day(1), superseded_at=at_day(2))
    with pytest.raises(KnowledgeBackendError) as exc:
        g.write(closed)
    assert str(exc.value) == "a written entry must be live (superseded_at is None)"


def test_invalidate_unknown_id_is_refused_with_exact_message() -> None:
    g = make_graph()
    with pytest.raises(KnowledgeBackendError) as exc:
        g.invalidate(entry_id="ghost", superseded_at=at_day(2))
    assert str(exc.value) == "no live record for entry_id 'ghost'"


def test_invalidate_already_superseded_is_refused() -> None:
    g = make_graph()
    g.write(make_entry(entry_id="k1", recorded_at=at_day(1)))
    g.invalidate(entry_id="k1", superseded_at=at_day(2))
    with pytest.raises(KnowledgeBackendError, match="no live record"):
        g.invalidate(entry_id="k1", superseded_at=at_day(3))


def test_subject_scoping_isolates_unrelated_entities() -> None:
    g = make_graph()
    g.write(make_entry(entry_id="k1", subject="pricing_model"))
    g.write(make_entry(entry_id="k2", subject="headcount", label="headcount"))
    hits = g.query_as_of(subject="pricing_model", as_of=at_day(2))
    assert [e.entry_id for e in hits] == ["k1"]


def test_query_scans_past_a_non_matching_subject_to_a_later_match() -> None:
    # An UNRELATED subject is written BEFORE a matching one. The scan must SKIP
    # (continue) the mismatch and still find the later match -- kills a
    # `continue` -> `break` mutant that would stop the scan at the first mismatch.
    g = make_graph()
    g.write(make_entry(entry_id="k0", subject="headcount", label="hc"))  # mismatch first
    g.write(make_entry(entry_id="k1", subject="pricing_model", label="pm"))  # match after
    hits = g.query_as_of(subject="pricing_model", as_of=at_day(2))
    assert [e.entry_id for e in hits] == ["k1"]  # found despite the earlier mismatch


def test_backend_satisfies_the_runtime_checkable_protocol() -> None:
    # The in-memory fake IS a KnowledgeGraphBackend at runtime -- proves the seam is
    # honoured and KILLS a mutant that drops the @runtime_checkable decorator (which
    # would make this isinstance check raise instead of return True).
    from autofirm.knowledge.knowledge_graph_backend_protocol import KnowledgeGraphBackend

    assert isinstance(make_graph(), KnowledgeGraphBackend)


def _build_timeline(g: InMemoryBitemporalKnowledgeGraph, facts: list[tuple[int, int]]) -> None:
    """Write ``facts`` as (record_day, valid_day) entries on subject 'topic'."""
    for index, (rec, val) in enumerate(facts):
        g.write(
            make_entry(
                entry_id=f"k{index}",
                subject="topic",
                label=f"f{index}",
                recorded_at=at_day(rec),
                valid_at=at_day(val),
            )
        )


@given(
    facts=st.lists(
        st.tuples(st.integers(0, 50), st.integers(0, 50)),
        min_size=0,
        max_size=8,
    ),
    as_of_day=st.integers(min_value=0, max_value=50),
)
def test_property_no_future_fact_ever_leaks_into_an_as_of_query(
    facts: list[tuple[int, int]], as_of_day: int
) -> None:
    # THE headline property: for ANY timeline and ANY query instant T, every returned
    # entry was BOTH recorded by T AND event-valid by T. A single future leak fails.
    g = make_graph()
    _build_timeline(g, facts)
    as_of = at_day(as_of_day)
    for entry in g.query_as_of(subject="topic", as_of=as_of):
        assert entry.recorded_at <= as_of  # never a fact the store did not yet know
        assert entry.valid_at <= as_of  # never a fact not yet true in the world
        assert entry.superseded_at is None or entry.superseded_at > as_of
        assert entry.invalid_at is None or entry.invalid_at > as_of


@given(as_of_day=st.integers(min_value=0, max_value=50))
def test_property_query_is_deterministic_across_repeats(as_of_day: int) -> None:
    # Determinism (§3.11): the same store + same as_of yields the identical tuple
    # (same items, same order) every call.
    g = make_graph()
    _build_timeline(g, [(1, 1), (2, 2), (3, 1), (4, 4)])
    as_of = at_day(as_of_day)
    first = g.query_as_of(subject="topic", as_of=as_of)
    for _ in range(5):
        assert g.query_as_of(subject="topic", as_of=as_of) == first
