"""The live capability registry: the CURRENT capability set, derived by pure replay.

What this does
--------------
Defines :class:`LiveCapabilityRegistry`, which derives the org's CURRENT advertised
capability set from a :class:`~autofirm.capabilities.capability_growth_log.CapabilityGrowthLog`
by a PURE replay. This REPLACES the static capability enumeration: the routable
set is now data, grown automatically (by
:class:`~autofirm.capabilities.capability_recording_org.CapabilityRecordingOrg`) as
the org is hired / auto-created / re-scoped / fired, and read back here.

Why it exists / where it sits
-----------------------------
Per ``docs/architecture/data-contracts.md`` §9, the growth log is the source of
truth for the evolution and the live registry derives the current set from "the
gapless log + live ``OrgState``". The front-door index
(:mod:`autofirm.frontdoor.role_capability_index`) is re-pointed to read this
registry, retiring the locked-in static tuples without a graveyard.

Security / compliance invariants upheld
---------------------------------------
* **Verification-before-load (fail-closed, §5.6):** :meth:`from_growth_log` REFUSES
  a log whose RFC-6962 chain does not verify — it raises, never quarantine-opens or
  serves a tampered/partial history. A corrupted registry fails closed.
* **Pure replay / no drift:** the current set is a deterministic fold of the log
  alone — the same log always yields the same set, and the set can never drift from
  the recorded history (§3.11).
* **Deprecation removes from the live set:** a ``CAPABILITY_DEPRECATED`` event drops
  the capability from the current set, so a fired role is no longer routable —
  capability follows the live org exactly.
"""

from __future__ import annotations

from collections.abc import Mapping

from autofirm.capabilities.capability_descriptor import (
    CapabilityDescriptor,
    CapabilityId,
)
from autofirm.capabilities.capability_growth_log import CapabilityGrowthLog, GrowthLogError
from autofirm.capabilities.capability_registry_event import CapabilityRegistryEvent

__all__ = ["LiveCapabilityRegistry"]


class LiveCapabilityRegistry:
    """The CURRENT advertised capability set, derived by pure replay of the log.

    Immutable: built once from a verified growth log; a changed log produces a NEW
    registry via :meth:`from_growth_log`, never an in-place edit.
    """

    __slots__ = ("_by_id",)

    def __init__(self, capabilities: tuple[CapabilityDescriptor, ...]) -> None:
        """Wrap the replayed current capabilities, indexed by capability id."""
        self._by_id: dict[CapabilityId, CapabilityDescriptor] = {
            c.capability_id: c for c in capabilities
        }

    @classmethod
    def from_growth_log(cls, log: CapabilityGrowthLog) -> LiveCapabilityRegistry:
        """Derive the current set by PURE replay of ``log`` (verification-before-load).

        Fail-closed: the log's RFC-6962 chain MUST verify before replay; an
        unverifiable log is refused (never served), so a tampered history can never
        produce a live registry. Replay applies each event in seq order: ADD /
        PROMOTE / RESCOPE upsert the descriptor; DEPRECATE removes it from the
        current set (a deprecated capability is no longer live/routable).
        """
        if not log.verify():
            # fail-closed: refuse to load an unverifiable log (no quarantine-open).
            raise GrowthLogError("cannot build registry from an unverifiable growth log")
        current: dict[CapabilityId, CapabilityDescriptor] = {}
        for event in log.events():
            cls._apply(current, event)
        return cls(tuple(current[cid] for cid in sorted(current)))

    @staticmethod
    def _apply(
        current: dict[CapabilityId, CapabilityDescriptor],
        event: CapabilityRegistryEvent,
    ) -> None:
        """Fold one event into the current-set accumulator (the replay step)."""
        cid = event.descriptor.capability_id
        if event.kind == "CAPABILITY_DEPRECATED":
            current.pop(cid, None)  # deprecated -> dropped from the live set
        else:
            current[cid] = event.descriptor  # add/promote/rescope -> upsert latest

    def descriptors(self) -> tuple[CapabilityDescriptor, ...]:
        """The current capabilities in deterministic capability-id order."""
        return tuple(self._by_id[cid] for cid in sorted(self._by_id))

    def descriptor_for(self, capability_id: CapabilityId) -> CapabilityDescriptor | None:
        """The current descriptor for ``capability_id``, or None if not live."""
        return self._by_id.get(capability_id)

    def with_clearances(
        self, required_clearances: Mapping[str, str]
    ) -> tuple[CapabilityDescriptor, ...]:
        """The current descriptors with explicit clearances applied (deny-by-default).

        A capability whose owning role is absent from ``required_clearances`` keeps
        its deny-by-default sentinel and stays unreachable — least-privilege, never
        open by omission (§5.6). Returns NEW descriptors (immutability preserved).
        """
        granted: list[CapabilityDescriptor] = []
        for descriptor in self.descriptors():
            clearance = required_clearances.get(str(descriptor.owning_role_id))
            if clearance is None:
                granted.append(descriptor)  # keep deny-by-default sentinel
            else:
                granted.append(descriptor.model_copy(update={"required_clearance": clearance}))
        return tuple(granted)
