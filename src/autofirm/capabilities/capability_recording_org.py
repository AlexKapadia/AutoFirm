"""The org wrapper that GROWS the capability log automatically on each transition.

What this does
--------------
Defines :class:`CapabilityRecordingOrg` — a thin, immutable wrapper around the
:class:`~autofirm.org.org_lifecycle_engine.DynamicOrg` engine that, after every
SUCCESSFUL lifecycle transition (hire / auto-create / re-scope / fire), projects
the org event onto its capability-growth event and seals it onto an append-only,
RFC-6962-chained :class:`~autofirm.capabilities.capability_growth_log.CapabilityGrowthLog`.
This is what makes the capability registry grow AUTOMATICALLY as the org evolves —
the charter is in hand at the moment of the transition, so the keyword surface is
captured exactly (no charter-less trail reconstruction).

Why it exists / where it sits
-----------------------------
Per ``docs/architecture/data-contracts.md`` §9 ("every add traces to an org
event"), capability growth is recorded at the point the org mutates. The wrapper
keeps the org engine untouched (single responsibility) and the projection pure;
it owns only the orchestration: apply the transition, then record what changed.
Refusals propagate from the underlying engine unchanged — a refused mutation grows
neither the org nor the capability log (fail-closed: no phantom capability).

Security / compliance invariants upheld
---------------------------------------
* **Append-only, tamper-evident growth (§5.6 / §3.8):** every recorded change is a
  chained, gapless growth-log event; the log is never edited in place.
* **No capability without an org event:** a capability is only ever sealed in
  response to a real, accepted org transition — there is no path to advertise a
  capability the org did not actually grow.
* **Immutable:** each transition returns a NEW wrapper (new engine + new log); a
  refused transition raises and leaves both untouched.
"""

from __future__ import annotations

from autofirm.capabilities.capability_descriptor import CapabilityId
from autofirm.capabilities.capability_growth_log import CapabilityGrowthLog
from autofirm.capabilities.capability_registry_event import RegistryEventKind
from autofirm.capabilities.live_capability_registry import LiveCapabilityRegistry
from autofirm.capabilities.org_event_to_capability_projection import project_org_event
from autofirm.org.gap_detection_contract import OrgGap
from autofirm.org.org_identifiers import Clock, IdGenerator, RoleId
from autofirm.org.org_lifecycle_engine import DynamicOrg
from autofirm.org.org_lifecycle_events import OrgEvent, OrgEventKind
from autofirm.org.role_charter_contract import RoleCharter

__all__ = ["CapabilityRecordingOrg"]

# The org-event kinds that DEPRECATE a capability (the fired role is gone from the
# post-transition hierarchy, so its surface is reused from the log built so far).
_DEPRECATION_KINDS = frozenset({OrgEventKind.ROLE_FIRED})


class CapabilityRecordingOrg:
    """A DynamicOrg wrapped so capability growth is recorded on every transition.

    Holds the wrapped engine, the injected determinism seams (clock for growth-event
    timestamps), and the growth log grown so far. Every public transition mirrors
    :class:`DynamicOrg`'s and returns a NEW recording org.
    """

    __slots__ = ("_clock", "_log", "_org")

    def __init__(self, org: DynamicOrg, log: CapabilityGrowthLog, clock: Clock) -> None:
        """Wrap ``org`` with its grown-so-far capability ``log`` and growth clock."""
        self._org = org
        self._log = log
        self._clock = clock

    @classmethod
    def found(
        cls, root: RoleCharter, clock: Clock, ids: IdGenerator, growth_clock: Clock
    ) -> CapabilityRecordingOrg:
        """Found an org and record the root's capability as the first growth event.

        The org's own clock/id-generator drive the lifecycle; ``growth_clock`` is a
        separate injected seam stamping the growth-log events (kept distinct so the
        two timelines do not share mutable state).
        """
        org = DynamicOrg.found(root, clock, ids)
        recording = cls(org, CapabilityGrowthLog(), growth_clock)
        return recording._record_last_event()

    @property
    def org(self) -> DynamicOrg:
        """The wrapped org engine (its immutable state is the live org snapshot)."""
        return self._org

    @property
    def growth_log(self) -> CapabilityGrowthLog:
        """The append-only, RFC-6962-chained capability growth log grown so far."""
        return self._log

    def live_registry(self) -> LiveCapabilityRegistry:
        """The CURRENT capability set, derived by pure replay of the growth log."""
        return LiveCapabilityRegistry.from_growth_log(self._log)

    def hire(self, charter: RoleCharter) -> CapabilityRecordingOrg:
        """Hire a role (DynamicOrg.hire), then record its added capability."""
        return self._after(self._org.hire(charter))

    def auto_create_on_gap(
        self, gap: OrgGap, new_role: RoleCharter
    ) -> CapabilityRecordingOrg:
        """Auto-create a role on a gap, then record its added capability."""
        return self._after(self._org.auto_create_on_gap(gap, new_role))

    def rescope(self, new_charter: RoleCharter) -> CapabilityRecordingOrg:
        """Re-scope a role (new charter), then record its re-stated capability."""
        return self._after(self._org.rescope(new_charter))

    def fire(
        self, role_id: RoleId, reassign_reports_to: RoleId | None = None
    ) -> CapabilityRecordingOrg:
        """Fire a role, then record the deprecation of its capability."""
        return self._after(self._org.fire(role_id, reassign_reports_to))

    def _after(self, next_org: DynamicOrg) -> CapabilityRecordingOrg:
        """Wrap the post-transition engine and record the event it just appended."""
        return CapabilityRecordingOrg(next_org, self._log, self._clock)._record_last_event()

    def _record_last_event(self) -> CapabilityRecordingOrg:
        """Seal the growth implied by the org's most recent audit event, if any.

        Reads the last trail event (the transition that just succeeded). A FIRE
        deprecates the last-known descriptor; any other capability-changing event is
        projected against the post-transition hierarchy. Events that change no
        capability (artifact locks, reassignments, refusals) seal nothing.
        """
        if not self._org.state.trail.events:  # pragma: no cover - defensive: a
            # founded org always carries >=1 audit event, so this guard is never
            # taken in practice; it exists so the recorder is safe on any state.
            return self
        event = self._org.state.trail.events[-1]
        if event.kind in _DEPRECATION_KINDS:
            return self._seal_deprecation(event)
        projected = project_org_event(event, self._org.state.hierarchy)
        if projected is None:
            return self  # no capability change for this event kind
        sealed = self._log.seal(
            kind=projected.kind,
            descriptor=projected.descriptor,
            triggered_by=projected.triggered_by,
            org_event_ref=projected.org_event_ref,
            rationale=projected.rationale,
            occurred_at=self._clock.now(),
        )
        return CapabilityRecordingOrg(self._org, self._log.append(sealed), self._clock)

    def _seal_deprecation(self, event: OrgEvent) -> CapabilityRecordingOrg:
        """Seal a DEPRECATE for a fired role using its last-known recorded descriptor.

        The fired role is absent from the post-fire hierarchy, so the deprecation
        reuses the descriptor already in the live registry (replayed from the log so
        far), flipping its maturity to ``deprecated``. Firing a never-advertised role
        is a no-op (nothing to deprecate) — fail-safe, not a spurious event.
        """
        cid = CapabilityId(event.subject_role_id)
        live = self.live_registry().descriptor_for(cid)
        if live is None:
            return self  # never advertised -> nothing to deprecate
        deprecated = live.model_copy(update={"maturity": "deprecated"})
        kind: RegistryEventKind = "CAPABILITY_DEPRECATED"
        sealed = self._log.seal(
            kind=kind,
            descriptor=deprecated,
            triggered_by=live.owning_role_id,
            org_event_ref=event.seq,
            rationale=deprecated.provenance.rationale,
            occurred_at=self._clock.now(),
        )
        return CapabilityRecordingOrg(self._org, self._log.append(sealed), self._clock)
