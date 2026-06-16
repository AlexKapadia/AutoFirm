"""Market-intelligence plane: sense the market, structure insights, decide go/no-go.

What this package does
----------------------
Implements AutoFirm's always-on (heartbeat-driven) **market & competitive
intelligence + modern-marketing** capability. It senses the market / competitors
/ trends through pluggable :class:`MarketSignalSource` feeds, turns every sensed
signal into a typed, audited :class:`MarketInsight` (or fail-closed-rejects it —
never silently dropped), flows those insights to the owning team via the flow
primitive, and feeds a fail-closed **green-light (go/no-go) gate** whose verdict
carries an explainable rationale (exactly which signals drove it). A daily
heartbeat beat drives the sensing sweep deterministically via an injected clock.
A focused modern/social-marketing campaign model rounds out the sense→decide→act
loop.

Where it sits
-------------
Builds *on* the existing planes rather than duplicating them: the daily sweep is
a beat on ``autofirm.heartbeat``; insights flow to teams as
``autofirm.flow.WorkItem`` handoffs; every fetched byte is treated as UNTRUSTED
(injection defence, validated/sanitized at the boundary — CLAUDE.md §5.6); and
insights are written to an append-only audit sink mirroring
``autofirm.comms.append_only_audit_sink``.

Security / compliance invariants upheld
---------------------------------------
* **Untrusted input at the boundary (§5.6):** all fetched content is sanitized and
  bounded before it becomes an insight; oversized / injection-laden / malformed
  content is rejected fail-closed, never silently dropped.
* **Determinism (§3.11):** sensing and the green-light verdict are pure functions
  of (signals, injected clock); two runs over the same inputs are identical.
* **Append-only audit (§3.8):** every insight and every rejection is recorded.
"""

from __future__ import annotations

from autofirm.market_intel.daily_sensing_heartbeat import (
    DAILY_INTERVAL_SECONDS,
    register_daily_sensing_beat,
)
from autofirm.market_intel.green_light_decision_contract import (
    GreenLightConfig,
    GreenLightDecision,
    GreenLightVerdict,
    SignalContribution,
)
from autofirm.market_intel.green_light_decision_gate import decide_green_light
from autofirm.market_intel.market_insight_audit_sink import (
    InMemoryMarketInsightAuditSink,
    MarketInsightAuditEntry,
    MarketInsightAuditSink,
)
from autofirm.market_intel.market_insight_contract import (
    InsightCategory,
    MarketInsight,
)
from autofirm.market_intel.market_sensing_sweep import (
    MarketSensingSweep,
    SweepResult,
)
from autofirm.market_intel.market_signal_source import (
    InMemoryMarketSignalSource,
    MarketSignalSource,
    RawMarketSignal,
)
from autofirm.market_intel.modern_marketing_campaign_model import (
    Channel,
    ChannelKind,
    MarketingCampaign,
)
from autofirm.market_intel.untrusted_signal_sanitizer import (
    SignalRejectedError,
    sanitize_untrusted_signal,
)

__all__ = [
    "DAILY_INTERVAL_SECONDS",
    "Channel",
    "ChannelKind",
    "GreenLightConfig",
    "GreenLightDecision",
    "GreenLightVerdict",
    "InMemoryMarketInsightAuditSink",
    "InMemoryMarketSignalSource",
    "InsightCategory",
    "MarketInsight",
    "MarketInsightAuditEntry",
    "MarketInsightAuditSink",
    "MarketSensingSweep",
    "MarketSignalSource",
    "MarketingCampaign",
    "RawMarketSignal",
    "SignalContribution",
    "SignalRejectedError",
    "SweepResult",
    "register_daily_sensing_beat",
    "decide_green_light",
    "sanitize_untrusted_signal",
]
