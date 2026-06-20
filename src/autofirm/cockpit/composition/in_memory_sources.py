"""In-memory cockpit sources: real on-main fakes wired for a runnable pre-live cockpit.

What this does
--------------
Defines :class:`CockpitSources` — the small frozen bundle of the four read sources the
cockpit projects (a front-door provenance trail, an org state, a cost ledger, and a
kill-switch source) — and :func:`default_in_memory_sources`, which builds that bundle from
the REAL on-main in-memory fakes/builders: an empty
:class:`~autofirm.frontdoor.front_door_provenance_trail.InMemoryFrontDoorProvenanceTrail`,
a single-root org founded via :meth:`~autofirm.org.org_lifecycle_engine.DynamicOrg.found`,
an empty :class:`~autofirm.costledger.append_only_cost_ledger.AppendOnlyCostLedger`, and the
adapters' :class:`~autofirm.cockpit.adapters.kill_switch_source.InMemoryKillSwitchSource`.

Why it exists / where it sits
-----------------------------
No live platform process is wired to the cockpit yet (that lands in C4+). These fakes let the
cockpit assemble and run end-to-end TODAY against real-shaped domain objects, and they are the
single seam C4 will swap for live sources behind the same :class:`CockpitSources` bundle. Sits
in the composition layer (permitted to import on-main domain packages and the cockpit adapters).

Security / compliance invariants upheld
---------------------------------------
* **Read-only sources (CLAUDE.md §3.2):** every source is an observe-only fake; the cockpit
  never gains a mutate/trip surface through them (the kill-switch source has no trip method).
* **Deterministic founding (§3.11):** the org is founded with the injected clock, so the
  same clock yields the same audit trail — no ambient time enters here.
"""

from __future__ import annotations

from dataclasses import dataclass

from autofirm.cockpit.adapters.kill_switch_source import (
    InMemoryKillSwitchSource,
    KillSwitchSource,
)
from autofirm.cockpit.adapters.provenance_read_port import ProvenanceReadable
from autofirm.costledger.append_only_cost_ledger import AppendOnlyCostLedger
from autofirm.frontdoor.front_door_provenance_trail import InMemoryFrontDoorProvenanceTrail
from autofirm.modelgateway.kill_switch_epoch import KillSwitchEpoch
from autofirm.org.org_identifiers import Clock, RoleId, SequentialIdGenerator
from autofirm.org.org_lifecycle_engine import DynamicOrg
from autofirm.org.org_state import OrgState
from autofirm.org.role_charter_contract import ROOT_AUTHOR, RoleCharter

__all__ = ["CockpitSources", "default_in_memory_sources"]

# The synthetic root role the in-memory org is founded with. A neutral, fully-specified
# charter (it satisfies the JCM completeness gate) so founding never fails closed.
_ROOT_ROLE_ID = "cockpit-root"
_ROOT_TITLE = "Founder"


@dataclass(frozen=True, slots=True)
class CockpitSources:
    """The frozen bundle of the four read sources the cockpit projects.

    Attributes:
        front_door_trail: The provenance trail the front-door activity view reads.
        org_state: The org state the org-snapshot view walks.
        cost_ledger: The cost ledger the spend view rolls up.
        kill_switch: The observe-only source of the current kill-switch epoch.
    """

    front_door_trail: ProvenanceReadable
    org_state: OrgState
    cost_ledger: AppendOnlyCostLedger
    kill_switch: KillSwitchSource


def default_in_memory_sources(
    clock: Clock, *, kill_switch_epoch: KillSwitchEpoch | None = None
) -> CockpitSources:
    """Build the default in-memory :class:`CockpitSources` from real on-main fakes.

    Args:
        clock: The clock used to found the in-memory org deterministically (the same clock
            the rest of the cockpit is wired with).
        kill_switch_epoch: The epoch the in-memory kill-switch source reports; when ``None``
            an untripped version-0 epoch is seeded (egress permitted, nothing halted).

    Returns:
        A :class:`CockpitSources` bundle: an empty provenance trail, a single-root org state,
        an empty cost ledger, and an in-memory kill-switch source over the resolved epoch.
    """
    epoch = KillSwitchEpoch(version=0) if kill_switch_epoch is None else kill_switch_epoch
    org_state = DynamicOrg.found(_root_charter(), clock, SequentialIdGenerator()).state
    return CockpitSources(
        front_door_trail=InMemoryFrontDoorProvenanceTrail(),
        org_state=org_state,
        cost_ledger=AppendOnlyCostLedger(),
        kill_switch=InMemoryKillSwitchSource(epoch),
    )


def _root_charter() -> RoleCharter:
    """Build the synthetic, fully-specified root charter the in-memory org is founded on."""
    return RoleCharter(
        role_id=RoleId(_ROOT_ROLE_ID),
        title=_ROOT_TITLE,
        responsibilities=("operate the company",),
        ownership_scope="the whole company",
        success_signal="the company runs",
        owned_artifacts=frozenset(),
        manager_id=None,  # root has no managing role above it
        authored_by=ROOT_AUTHOR,  # only the founder sentinel may author the apex
    )
