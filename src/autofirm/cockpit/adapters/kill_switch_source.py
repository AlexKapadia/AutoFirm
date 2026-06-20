"""The cockpit-side kill-switch observation seam (observe-only; no trip/re-arm surface).

What this does
--------------
Defines :class:`KillSwitchSource` — a read :class:`~typing.Protocol` exposing
``current() -> KillSwitchEpoch`` — and :class:`InMemoryKillSwitchSource`, a tiny fake holding
one :class:`~autofirm.modelgateway.kill_switch_epoch.KillSwitchEpoch` for tests and local
wiring. The cockpit OBSERVES the global kill-switch epoch (is egress halted? which version?);
it deliberately offers NO trip or re-arm method, because no such write surface exists on main
and the cockpit must not add one.

Why it exists / where it sits
-----------------------------
The operator's kill-switch panel reads the live epoch through this seam. The REAL source is a
C3 composition seam — composition will inject the gateway's authoritative epoch provider; this
module only defines the read contract and an in-memory stand-in. Sits in the adapters layer —
the only cockpit layer permitted to import on-main domain types.

Security / compliance invariants upheld
---------------------------------------
* **Observe-only, fail-closed posture (CLAUDE.md §3.2 / §5.6):** the cockpit can read the
  epoch but cannot flip it from here; tripping/re-arming stays with the authoritative
  gateway control, never a cockpit-side mutation.
"""

from __future__ import annotations

from typing import Protocol

from autofirm.modelgateway.kill_switch_epoch import KillSwitchEpoch

__all__ = ["InMemoryKillSwitchSource", "KillSwitchSource"]


class KillSwitchSource(Protocol):
    """A read-only source of the current global kill-switch epoch (observe-only).

    Implementations expose only :meth:`current`; there is intentionally no trip/re-arm
    method, mirroring the absence of such a write surface on main.
    """

    def current(self) -> KillSwitchEpoch:
        """Return the current :class:`KillSwitchEpoch` (version + tripped flag)."""
        ...


class InMemoryKillSwitchSource:
    """An in-memory :class:`KillSwitchSource` holding one epoch (tests + local wiring).

    Production wiring (C3 composition) replaces this with the gateway's authoritative epoch
    provider behind the same Protocol; this stand-in simply returns the epoch it was given.
    """

    __slots__ = ("_epoch",)

    def __init__(self, epoch: KillSwitchEpoch) -> None:
        """Hold ``epoch`` as the single observable kill-switch state."""
        self._epoch = epoch

    def current(self) -> KillSwitchEpoch:
        """Return the held :class:`KillSwitchEpoch` unchanged (observe-only)."""
        return self._epoch
