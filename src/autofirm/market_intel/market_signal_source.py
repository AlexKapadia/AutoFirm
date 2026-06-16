"""Pluggable market-signal feeds: the source Protocol + a deterministic fake.

What this does
--------------
Defines :class:`RawMarketSignal` — one immutable, UNTRUSTED fragment as fetched
from a feed (source name, the raw observation text, and a proposed category) —
and :class:`MarketSignalSource`, the Protocol any competitor / market / trend feed
implements. Ships :class:`InMemoryMarketSignalSource`, a deterministic, no-network
reference source for tests and replay: it returns a fixed, ordered batch and never
touches the network, so a unit test fully controls what is "sensed".

Why it exists / where it sits
-----------------------------
The sensing sweep depends only on the Protocol, so a real HTTP/RSS feed and the
in-memory fake are interchangeable behind one seam (the same dependency-injection
pattern the comms bus uses for its audit sink). The raw signal's text is
DELIBERATELY untrusted here — it is sanitized only later, at the sweep boundary
(``untrusted_signal_sanitizer``) — so this layer never has to be trusted.

Security / compliance invariants upheld
---------------------------------------
* **No network in the reference source (§5.5):** the in-memory source is pure
  in-process data; unit tests never reach out.
* **Untrusted by construction (§5.6):** ``observation`` is raw feed text; the
  contract carries it verbatim and the sweep sanitizes it at the boundary.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, field_validator

from autofirm.market_intel.market_insight_contract import InsightCategory

__all__ = [
    "InMemoryMarketSignalSource",
    "MarketSignalSource",
    "RawMarketSignal",
]


class RawMarketSignal(BaseModel):
    """One immutable, UNTRUSTED signal fragment as fetched from a feed.

    ``observation`` is raw external text and must be treated as untrusted until it
    passes the sanitizer at the sweep boundary. ``proposed_category`` is the feed's
    hint of what kind of signal this is; the sweep re-checks it.
    """

    model_config = ConfigDict(frozen=True)

    source_name: str  # which feed produced this (e.g. "competitor-pricing-page")
    observation: str  # UNTRUSTED raw text — sanitized only at the sweep boundary
    proposed_category: InsightCategory  # the feed's category hint

    @field_validator("source_name")
    @classmethod
    def _source_name_non_empty(cls, value: str) -> str:
        # fail-closed: an unattributed signal breaks provenance — refuse it.
        if not value.strip():
            raise ValueError("source_name must be non-empty (signal provenance)")
        return value


@runtime_checkable
class MarketSignalSource(Protocol):
    """A pluggable feed of raw market signals (competitor / market / trend).

    Implementations may hit the network in production, but MUST be injectable so
    unit tests can swap in :class:`InMemoryMarketSignalSource`. The sweep calls
    :meth:`fetch` once per sensing run and treats every returned fragment as
    untrusted.
    """

    @property
    def source_name(self) -> str:
        """Stable identifier of this feed (for provenance/audit)."""
        ...

    def fetch(self) -> tuple[RawMarketSignal, ...]:
        """Return the current batch of raw signals (untrusted; may be empty)."""
        ...


class InMemoryMarketSignalSource:
    """Deterministic, no-network reference source returning a fixed batch.

    The whole point is reproducibility: :meth:`fetch` returns exactly the signals
    it was constructed with, in order, every call — so a test controls precisely
    what is sensed and two runs are identical. It never touches the network.
    """

    def __init__(self, source_name: str, signals: tuple[RawMarketSignal, ...]) -> None:
        """Create a source named ``source_name`` that always yields ``signals``."""
        if not source_name.strip():
            raise ValueError("source_name must be non-empty")  # fail-closed provenance
        self._source_name = source_name
        self._signals = signals

    @property
    def source_name(self) -> str:
        """Stable identifier of this feed."""
        return self._source_name

    def fetch(self) -> tuple[RawMarketSignal, ...]:
        """Return the fixed batch (deterministic; no network)."""
        return self._signals
