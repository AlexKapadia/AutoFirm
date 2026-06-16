"""The typed, structured market insight: a sanitized observation with provenance.

What this does
--------------
Defines :class:`InsightCategory` (the closed taxonomy a signal is classified into
— competitor move, market trend, customer demand, regulatory, pricing) and
:class:`MarketInsight`, the immutable structured record the sensing sweep produces
from a sanitized signal: its source, the clean observation text, the category, a
bounded confidence in [0, 1], and the injected-clock timestamp it was sensed at.

Why it exists / where it sits
-----------------------------
This is the typed boundary between *raw sensing* and *decision-making*: the sweep
emits these, the audit sink stores them, the flow plane carries them to the owning
team, and the green-light gate consumes them. Keeping it a frozen pydantic model
with validated fields means a malformed insight (blank text, out-of-range
confidence, naive timestamp) can never enter the decision path.

Security / compliance invariants upheld
---------------------------------------
* **Bounded confidence (§3.11):** confidence is validated to [0, 1]; a score
  outside the unit interval is meaningless for a gate threshold and is refused.
* **Non-empty sanitized text (§5.6):** ``observation`` must be non-empty — the
  sweep only ever builds one from already-sanitized content.
* **Tz-aware timestamp (§3.11):** a naive ``sensed_at`` is refused so every
  ordering/threshold comparison is unambiguous.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, field_validator

__all__ = ["InsightCategory", "MarketInsight"]


class InsightCategory(str, Enum):
    """The closed taxonomy a sensed signal is classified into.

    A closed enum (not free text) keeps the green-light gate's category-weighting
    deterministic and total — every insight maps to exactly one known category.
    """

    COMPETITOR_MOVE = "competitor_move"  # a competitor launch / pricing / hire
    MARKET_TREND = "market_trend"  # a directional shift in the wider market
    CUSTOMER_DEMAND = "customer_demand"  # observed demand / intent signal
    REGULATORY = "regulatory"  # a legal / compliance / policy change
    PRICING = "pricing"  # a pricing-specific signal (ours or a rival's)


class MarketInsight(BaseModel):
    """One immutable, structured insight derived from a sanitized signal.

    Built only by the sensing sweep from already-sanitized content, so every
    instance is safe to store, flow, and feed into the green-light gate.
    """

    model_config = ConfigDict(frozen=True)

    source_name: str  # which feed this came from (provenance)
    observation: str  # the SANITIZED, single-line observation text (trusted)
    category: InsightCategory
    confidence: float  # bounded [0, 1] — how strongly the feed/sweep trusts it
    sensed_at: datetime  # from the injected clock — deterministic (§3.11)

    @field_validator("source_name", "observation")
    @classmethod
    def _text_non_empty(cls, value: str) -> str:
        # fail-closed: an unattributed or empty insight is meaningless downstream.
        if not value.strip():
            raise ValueError("source_name and observation must be non-empty")
        return value

    @field_validator("confidence")
    @classmethod
    def _confidence_in_unit_interval(cls, value: float) -> float:
        # fail-closed: confidence outside [0, 1] cannot be compared against a
        # gate threshold meaningfully — refuse it (§3.11 exactness).
        if not 0.0 <= value <= 1.0:
            raise ValueError("confidence must be within [0.0, 1.0]")
        return value

    @field_validator("sensed_at")
    @classmethod
    def _timestamp_tz_aware(cls, value: datetime) -> datetime:
        # fail-closed: a naive timestamp makes ordering ambiguous — require tz.
        if value.tzinfo is None:
            raise ValueError("sensed_at must be timezone-aware (unambiguous ordering)")
        return value
