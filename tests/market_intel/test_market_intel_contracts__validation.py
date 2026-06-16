"""Validation tests for the market-intel typed contracts (fail-closed fields).

What these prove
----------------
Every typed contract refuses malformed data at construction: a MarketInsight with
blank text / out-of-range confidence / naive timestamp is rejected; a RawMarketSignal
without a source is rejected; the audit entry enforces the exactly-one-outcome
(accept XOR reject) invariant that underpins "every signal accounted for"; the
in-memory source is deterministic and never hits the network. Boundary-exact on the
confidence interval; property-based on the audit XOR invariant.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from hypothesis import given
from hypothesis import strategies as st
from pydantic import ValidationError

from autofirm.market_intel.market_insight_audit_sink import (
    InMemoryMarketInsightAuditSink,
    MarketInsightAuditEntry,
)
from autofirm.market_intel.market_insight_contract import InsightCategory, MarketInsight
from autofirm.market_intel.market_signal_source import (
    InMemoryMarketSignalSource,
    MarketSignalSource,
    RawMarketSignal,
)

_TS = datetime(2025, 3, 1, tzinfo=UTC)


def _insight(confidence: float = 0.7) -> MarketInsight:
    return MarketInsight(
        source_name="feed-x",
        observation="rival launched a new tier",
        category=InsightCategory.COMPETITOR_MOVE,
        confidence=confidence,
        sensed_at=_TS,
    )


def test_insight_rejects_blank_text() -> None:
    with pytest.raises(ValidationError):
        MarketInsight(
            source_name=" ",
            observation="x",
            category=InsightCategory.PRICING,
            confidence=0.5,
            sensed_at=_TS,
        )


@pytest.mark.parametrize("bad", [-0.0001, 1.0001, -1.0, 2.0])
def test_insight_rejects_out_of_range_confidence(bad: float) -> None:
    with pytest.raises(ValidationError):
        _insight(confidence=bad)


@pytest.mark.parametrize("edge", [0.0, 1.0])
def test_insight_accepts_unit_interval_edges(edge: float) -> None:
    # Boundary-exact: 0.0 and 1.0 are valid (inclusive interval).
    assert _insight(confidence=edge).confidence == edge


def test_insight_rejects_naive_timestamp() -> None:
    with pytest.raises(ValidationError):
        MarketInsight(
            source_name="f",
            observation="o",
            category=InsightCategory.MARKET_TREND,
            confidence=0.5,
            sensed_at=datetime(2025, 1, 1),
        )


def test_raw_signal_rejects_blank_source() -> None:
    with pytest.raises(ValidationError):
        RawMarketSignal(
            source_name="", observation="o", proposed_category=InsightCategory.PRICING
        )


def test_in_memory_source_is_deterministic_and_satisfies_protocol() -> None:
    signals = (
        RawMarketSignal(
            source_name="s", observation="o", proposed_category=InsightCategory.PRICING
        ),
    )
    source = InMemoryMarketSignalSource("s", signals)
    assert isinstance(source, MarketSignalSource)  # structural Protocol check
    assert source.fetch() == source.fetch() == signals  # deterministic, same object batch
    assert source.source_name == "s"


def test_in_memory_source_refuses_blank_name() -> None:
    with pytest.raises(ValueError, match="source_name"):
        InMemoryMarketSignalSource("  ", ())


def test_audit_entry_requires_exactly_one_outcome() -> None:
    # Neither outcome -> refused.
    with pytest.raises(ValidationError):
        MarketInsightAuditEntry(source_name="s", recorded_at=_TS)
    # Both outcomes -> refused.
    with pytest.raises(ValidationError):
        MarketInsightAuditEntry(
            source_name="s", recorded_at=_TS, insight=_insight(), rejection_reason="dup"
        )


def test_audit_sink_is_append_only_snapshot() -> None:
    sink = InMemoryMarketInsightAuditSink()
    sink.record(MarketInsightAuditEntry(source_name="s", recorded_at=_TS, insight=_insight()))
    snap = sink.entries()
    sink.record(
        MarketInsightAuditEntry(source_name="s", recorded_at=_TS, rejection_reason="bad")
    )
    assert len(snap) == 1  # earlier snapshot is immutable to later appends
    assert len(sink) == 2


@pytest.mark.property
@given(reject=st.booleans())
def test_audit_entry_xor_invariant(reject: bool) -> None:
    # Exactly one of the two outcomes always constructs; this is the structural
    # guarantee behind "every signal becomes an insight OR an audited rejection".
    if reject:
        entry = MarketInsightAuditEntry(
            source_name="s", recorded_at=_TS, rejection_reason="r"
        )
        assert entry.insight is None and entry.rejection_reason == "r"
    else:
        entry = MarketInsightAuditEntry(source_name="s", recorded_at=_TS, insight=_insight())
        assert entry.insight is not None and entry.rejection_reason is None
