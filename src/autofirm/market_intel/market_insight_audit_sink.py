"""Append-only audit sink for every sensed insight AND every rejected signal.

What this does
--------------
Defines :class:`MarketInsightAuditEntry` — one immutable row recording either an
accepted :class:`~autofirm.market_intel.market_insight_contract.MarketInsight`
(``rejection_reason is None``) OR a fail-closed-rejected raw signal
(``rejection_reason`` set, ``insight is None``) — plus the
:class:`MarketInsightAuditSink` protocol the sweep records into and an in-memory
reference implementation.

Why it exists / where it sits
-----------------------------
The market-intel invariant is **every sensed signal becomes an auditable insight
OR is fail-closed-rejected — never silently dropped**. This sink is where that
invariant is made provable: the sweep records exactly one entry per raw signal, so
the trail length equals the number of signals fetched, and a rejection is surfaced
with its reason (explain-every-decision, §3.11). It mirrors the append-only sink
pattern in ``autofirm.comms.append_only_audit_sink``; production swaps the
in-memory list for the RFC 6962 Merkle log behind the same protocol.

Security / compliance invariants upheld
---------------------------------------
* **Append-only (§3.8 / §5.6):** the protocol exposes only ``record`` + read; no
  update/delete. The in-memory impl appends to a list it never rewrites.
* **Records denials too (§5.6):** rejected signals are logged with their reason —
  the log proves what the system refused, not just what it accepted.
"""

from __future__ import annotations

from datetime import datetime
from typing import Protocol

from pydantic import BaseModel, ConfigDict, model_validator

from autofirm.market_intel.market_insight_contract import MarketInsight

__all__ = [
    "InMemoryMarketInsightAuditSink",
    "MarketInsightAuditEntry",
    "MarketInsightAuditSink",
]


class MarketInsightAuditEntry(BaseModel):
    """One immutable audit row: an accepted insight XOR a rejected raw signal.

    Exactly one of ``insight`` / ``rejection_reason`` is set — this is the
    structural proof that every sensed signal is accounted for either way (never
    silently dropped). ``source_name`` and ``recorded_at`` are always present so
    even a rejection is fully attributed and timestamped.
    """

    model_config = ConfigDict(frozen=True)

    source_name: str  # the feed the signal came from (always attributed)
    recorded_at: datetime  # injected-clock instant the entry was recorded
    insight: MarketInsight | None = None  # set IFF the signal was accepted
    rejection_reason: str | None = None  # set IFF the signal was fail-closed-rejected

    @model_validator(mode="after")
    def _exactly_one_outcome(self) -> MarketInsightAuditEntry:
        # fail-closed: an entry that is neither an accepted insight nor a recorded
        # rejection (or claims to be both) would break the "every signal accounted
        # for" invariant — refuse the ambiguous row.
        has_insight = self.insight is not None
        has_rejection = self.rejection_reason is not None
        if has_insight == has_rejection:
            raise ValueError(
                "audit entry must record exactly one of insight / rejection_reason"
            )
        return self


class MarketInsightAuditSink(Protocol):
    """Append-only audit interface the sweep records every signal outcome into.

    Implementations MUST be append-only (no update/delete). This is the seam to
    the RFC 6962 Merkle audit log; the sweep knows only this protocol.
    """

    def record(self, entry: MarketInsightAuditEntry) -> None:
        """Append one audit entry (must never mutate prior entries)."""
        ...


class InMemoryMarketInsightAuditSink:
    """Reference append-only sink backed by an in-memory list.

    Suitable for tests and single-process use; production wiring replaces it with
    the Merkle-tree-backed sink behind the same protocol.
    """

    def __init__(self) -> None:
        """Create an empty append-only audit log."""
        self._entries: list[MarketInsightAuditEntry] = []

    def record(self, entry: MarketInsightAuditEntry) -> None:
        """Append ``entry``; the existing log is never rewritten (append-only)."""
        self._entries.append(entry)

    def entries(self) -> tuple[MarketInsightAuditEntry, ...]:
        """Return the full append-only trail as an immutable snapshot."""
        return tuple(self._entries)

    def __len__(self) -> int:
        """Number of audit entries recorded so far."""
        return len(self._entries)
