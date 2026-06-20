"""The cockpit-side read port for front-door provenance (the read seam we own).

What this does
--------------
Defines :class:`ProvenanceReadable` — a cockpit-owned read :class:`~typing.Protocol` exposing
``entries() -> Sequence[FrontDoorProvenanceEntry]``. The on-main
:class:`~autofirm.frontdoor.front_door_provenance_trail.FrontDoorProvenanceTrail` Protocol is
deliberately write-only (it has only ``record()``), so the cockpit declares its OWN read seam
here rather than widening the on-main contract. The concrete on-main
:class:`~autofirm.frontdoor.front_door_provenance_trail.InMemoryFrontDoorProvenanceTrail`
already has an ``entries()`` method, so it satisfies this port *structurally* — no on-main
change is needed.

Why it exists / where it sits
-----------------------------
Owning the read seam keeps the cockpit add-only: it observes the trail without forcing a
read method onto the on-main write Protocol. Sits in the adapters layer — the only cockpit
layer permitted to import on-main domain types — and is consumed by the front-door activity
adapter.

Security / compliance invariants upheld
---------------------------------------
* **Read-only observation (CLAUDE.md §3.2):** the port exposes only ``entries()``; the cockpit
  has no surface here to record into or mutate the on-main trail.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from autofirm.frontdoor.front_door_provenance_trail import FrontDoorProvenanceEntry

__all__ = ["ProvenanceReadable"]


class ProvenanceReadable(Protocol):
    """A read-only view over a front-door provenance trail (cockpit-owned read seam).

    Any object exposing ``entries()`` returning the recorded
    :class:`FrontDoorProvenanceEntry` rows satisfies this Protocol structurally — notably the
    on-main ``InMemoryFrontDoorProvenanceTrail``.
    """

    def entries(self) -> Sequence[FrontDoorProvenanceEntry]:
        """Return the recorded provenance entries (read-only, in append order)."""
        ...
