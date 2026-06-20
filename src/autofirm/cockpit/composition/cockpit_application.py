"""The assembled cockpit application: read-only snapshots + an append-only event recorder.

What this does
--------------
Defines :class:`CockpitApplication`, the frozen value the C4 TUI/CLI drives. It binds the
four C2 read adapters to their sources and the append-only event writer to the configured log,
exposing read-only accessors — :meth:`org_snapshot`, :meth:`spend_snapshot`,
:meth:`front_door_activity`, :meth:`kill_switch_epoch` — plus :meth:`record_event` (stamps the
injected clock and writes one durable event) and :meth:`recorded_events` (replays the log via
the read seam). It holds its :attr:`config` and :attr:`clock`.

Why it exists / where it sits
-----------------------------
This is the single object the UI layer talks to, so the UI never imports an adapter, the event
log, or an on-main type — it asks the application for a view. Sits in the composition layer
(the impure edge), so it is allowed to import the adapters, the event log, and on-main domain
types; the layers below it stay pure. Built only by :mod:`cockpit_composer`.

Security / compliance invariants upheld
---------------------------------------
* **Read-only projection (CLAUDE.md §3.2):** every snapshot accessor only reads its source and
  returns an immutable view; the application exposes no mutate/trip surface onto on-main state.
* **Deterministic, append-only recording (§3.11 / §5.6):** :meth:`record_event` stamps the
  INJECTED clock (never ambient time) and writes through the append-only writer, so every
  recorded event is durable and time-deterministic under a pinned clock.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from autofirm.cockpit.adapters.front_door_activity_adapter import build_front_door_activity_view
from autofirm.cockpit.adapters.kill_switch_source import KillSwitchSource
from autofirm.cockpit.adapters.org_snapshot_adapter import build_org_snapshot_view
from autofirm.cockpit.adapters.provenance_read_port import ProvenanceReadable
from autofirm.cockpit.adapters.spend_adapter import build_spend_snapshot_view
from autofirm.cockpit.composition.cockpit_config import CockpitConfig
from autofirm.cockpit.eventlog.append_only_event_writer import AppendOnlyEventWriter
from autofirm.cockpit.eventlog.cockpit_event_contract import CockpitEvent, CockpitEventKind
from autofirm.cockpit.eventlog.event_log_reader import read_all
from autofirm.cockpit.readmodels.front_door_activity_view import FrontDoorActivityView
from autofirm.cockpit.readmodels.org_snapshot_view import OrgSnapshotView
from autofirm.cockpit.readmodels.spend_snapshot_view import SpendSnapshotView
from autofirm.costledger.append_only_cost_ledger import AppendOnlyCostLedger
from autofirm.modelgateway.kill_switch_epoch import KillSwitchEpoch
from autofirm.org.org_identifiers import Clock
from autofirm.org.org_state import OrgState

__all__ = ["CockpitApplication"]


@dataclass(frozen=True, slots=True)
class CockpitApplication:
    """The assembled, read-only cockpit the UI drives (snapshots + event recorder).

    Attributes:
        config: The frozen :class:`CockpitConfig` this cockpit was assembled from.
        clock: The injected clock every recorded event is stamped with.
        front_door_trail: The provenance source the front-door activity view reads.
        org_state: The org state the org-snapshot view walks.
        cost_ledger: The cost ledger the spend view rolls up.
        kill_switch: The observe-only source of the current kill-switch epoch.
        event_writer: The append-only writer events are recorded through.
    """

    config: CockpitConfig
    clock: Clock
    front_door_trail: ProvenanceReadable
    org_state: OrgState
    cost_ledger: AppendOnlyCostLedger
    kill_switch: KillSwitchSource
    event_writer: AppendOnlyEventWriter

    def org_snapshot(self) -> OrgSnapshotView:
        """Project the current org state into an immutable :class:`OrgSnapshotView`."""
        return build_org_snapshot_view(self.org_state)

    def spend_snapshot(self) -> SpendSnapshotView:
        """Project the cost ledger into a :class:`SpendSnapshotView` (config currency/budget).

        Threads :attr:`config.currency` and :attr:`config.budget` through the spend adapter
        verbatim, so the band is classified only when a strictly-positive budget is configured.
        """
        return build_spend_snapshot_view(
            self.cost_ledger, currency=self.config.currency, budget=self.config.budget
        )

    def front_door_activity(self) -> FrontDoorActivityView:
        """Project the provenance trail into an immutable :class:`FrontDoorActivityView`."""
        return build_front_door_activity_view(self.front_door_trail)

    def kill_switch_epoch(self) -> KillSwitchEpoch:
        """Return the current observed :class:`KillSwitchEpoch` (observe-only, never flips it)."""
        return self.kill_switch.current()

    def record_event(
        self, kind: CockpitEventKind, source: str, payload: Mapping[str, str]
    ) -> CockpitEvent:
        """Record one cockpit event, stamped with the injected clock (durable, append-only).

        Args:
            kind: The :class:`CockpitEventKind` to record.
            source: A non-blank provenance string (validated by the event contract).
            payload: A string→string mapping of non-secret summary fields.

        Returns:
            The recorded :class:`CockpitEvent`, carrying its assigned monotonic ``seq``.
        """
        return self.event_writer.append(kind, source, payload, now=self.clock.now())

    def recorded_events(self) -> tuple[CockpitEvent, ...]:
        """Replay every recorded event in order (the replay/audit read path).

        Reads from :attr:`config.replay_source_path` when one is configured (e.g. an archived
        log), otherwise from the live :attr:`config.event_log_path`. A missing file replays as
        an empty history; a corrupt line fails closed in the reader (never silently skipped).
        """
        source_path = self.config.replay_source_path or self.config.event_log_path
        return read_all(source_path)
