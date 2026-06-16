"""The sensing sweep: fetch signals, sanitize, structure into audited insights.

What this does
--------------
Defines :class:`MarketSensingSweep`, the engine that runs ONE sensing pass over
its injected :class:`~autofirm.market_intel.market_signal_source.MarketSignalSource`
feeds. For every raw signal fetched it:

1. sanitizes the UNTRUSTED observation at the boundary (``sanitize_untrusted_signal``),
2. on success, builds a typed :class:`MarketInsight` (injected-clock timestamp) and
   records it in the append-only audit sink,
3. on a fail-closed rejection, records a rejection entry (with the reason) in the
   same sink — **never silently dropping the signal**,

then **flows the accepted insights to the owning team** as a single audited
``WorkItem`` handoff (sense → act). It returns a :class:`SweepResult` summarising
what was accepted, what was rejected, and the work item raised for the team.

Why it exists / where it sits
-----------------------------
This is the heart of "sense → decide → act": it is the only place raw feed content
crosses the trust boundary into structured insights, and it is driven by the daily
heartbeat beat (``daily_sensing_heartbeat``). It builds *on* the existing planes —
the audit sink mirrors ``autofirm.comms``, the team handoff is an
``autofirm.flow.WorkItem`` — rather than re-implementing them.

Security / compliance invariants upheld
---------------------------------------
* **Every signal accounted for (§3.8 / §5.6):** exactly one audit entry per raw
  signal (accept XOR reject) — the audit trail length equals signals fetched, so
  nothing is silently dropped.
* **Untrusted at the boundary (§5.6):** sanitisation happens here, before any
  insight is built; an adversarial fragment is rejected fail-closed.
* **Determinism (§3.11):** a pure function of (source batch, injected clock).
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from autofirm.flow.injected_flow_clock import FlowClock
from autofirm.flow.work_item import WorkItem
from autofirm.market_intel.market_insight_audit_sink import (
    MarketInsightAuditEntry,
    MarketInsightAuditSink,
)
from autofirm.market_intel.market_insight_contract import MarketInsight
from autofirm.market_intel.market_signal_source import MarketSignalSource
from autofirm.market_intel.untrusted_signal_sanitizer import (
    SignalRejectedError,
    sanitize_untrusted_signal,
)

__all__ = ["MarketSensingSweep", "SweepResult"]

# Confidence floor applied when a feed supplies no explicit per-signal confidence.
# A conservative mid value: present-but-unverified. The gate's threshold, not this
# constant, decides go/no-go, so this is a neutral prior, not a magic tuning knob.
_DEFAULT_CONFIDENCE = 0.5


class SweepResult(BaseModel):
    """The immutable outcome of one sensing sweep.

    ``insights`` are the accepted, structured insights (in fetch order);
    ``rejections`` pairs each refused signal's source with its rejection reason;
    ``team_work_item`` is the flow handoff raised to the owning team IFF at least
    one insight was accepted (``None`` when the sweep produced nothing to act on).
    """

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    insights: tuple[MarketInsight, ...]
    rejections: tuple[tuple[str, str], ...]  # (source_name, reason) per rejected signal
    team_work_item: WorkItem | None


class MarketSensingSweep:
    """Runs one fetch → sanitize → structure → audit → flow pass over its feeds.

    All collaborators are injected (sources, audit sink, clock, owning-team role),
    so the sweep is fully deterministic and unit-testable with no network and no
    wall-clock.
    """

    __slots__ = ("_audit_sink", "_clock", "_known_roles", "_owning_team", "_sources")

    def __init__(
        self,
        *,
        sources: tuple[MarketSignalSource, ...],
        audit_sink: MarketInsightAuditSink,
        clock: FlowClock,
        owning_team: str,
        known_roles: frozenset[str],
    ) -> None:
        """Wire the sweep to its feeds, audit sink, clock, and owning team.

        Fail-closed: ``owning_team`` must be a known role, otherwise the eventual
        flow handoff could never be delivered — refuse the mis-wiring up front.
        """
        if owning_team not in known_roles:
            # fail-closed (§5.6): an insight must flow to a *known* team; a sweep
            # wired to route into the unknown is refused at construction.
            raise ValueError("owning_team must be one of known_roles")
        self._sources = sources
        self._audit_sink = audit_sink
        self._clock = clock
        self._owning_team = owning_team
        self._known_roles = known_roles

    def run(self) -> SweepResult:
        """Execute one sensing pass; return the accepted insights and rejections.

        Each raw signal yields exactly one audit entry (accept XOR reject), so the
        sink grows by the number of signals fetched — the "never silently dropped"
        invariant is structural, not a comment.
        """
        now = self._clock.now()
        insights: list[MarketInsight] = []
        rejections: list[tuple[str, str]] = []
        for source in self._sources:
            for raw in source.fetch():
                try:
                    # Trust boundary: sanitize the UNTRUSTED observation here. A
                    # failure raises and is caught below — fail-closed (§5.6).
                    clean = sanitize_untrusted_signal(raw.observation)
                except SignalRejectedError as exc:
                    # Rejected: record WHY in the append-only sink (never dropped).
                    self._audit_sink.record(
                        MarketInsightAuditEntry(
                            source_name=raw.source_name,
                            recorded_at=now,
                            rejection_reason=exc.reason,
                        )
                    )
                    rejections.append((raw.source_name, exc.reason))
                    continue
                insight = MarketInsight(
                    source_name=raw.source_name,
                    observation=clean,  # only ever the sanitized text
                    category=raw.proposed_category,
                    confidence=_DEFAULT_CONFIDENCE,
                    sensed_at=now,
                )
                # Accepted: record the structured insight (append-only audit).
                self._audit_sink.record(
                    MarketInsightAuditEntry(
                        source_name=raw.source_name,
                        recorded_at=now,
                        insight=insight,
                    )
                )
                insights.append(insight)
        team_work_item = self._flow_to_team(insights)
        return SweepResult(
            insights=tuple(insights),
            rejections=tuple(rejections),
            team_work_item=team_work_item,
        )

    def _flow_to_team(self, insights: list[MarketInsight]) -> WorkItem | None:
        """Raise an audited flow handoff of the accepted insights to the team.

        Returns ``None`` when nothing was accepted — there is no work to act on, so
        no spurious work item is created (sense produced no act).
        """
        if not insights:
            return None
        # The work item rides the existing flow plane: create → assign to the
        # owning team → start. Every step is recorded in the flow trail with the
        # injected clock, so the handoff is fully audited and deterministic.
        item = WorkItem.create(
            work_id=f"market-intel-sweep-{self._clock.now().isoformat()}",
            clock=self._clock,
            known_roles=self._known_roles,
        )
        item = item.assign_to(
            self._owning_team,
            reason=f"{len(insights)} market insight(s) sensed for review",
        )
        return item.start(reason="owning team begins acting on sensed insights")
