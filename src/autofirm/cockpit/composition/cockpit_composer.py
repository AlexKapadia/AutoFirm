"""The cockpit composition root: assemble a runnable :class:`CockpitApplication` from config.

What this does
--------------
Defines :func:`assemble_cockpit`, the single function that wires a cockpit together: it binds
the append-only event writer to ``config.event_log_path`` and the four C2 read adapters to
their sources, then returns the frozen :class:`CockpitApplication` the UI drives. Dependency
injection is keyword-only — ``clock`` defaults to the production :class:`SystemClock` and
``sources`` defaults to the in-memory fakes, so a real run needs only a ``CockpitConfig`` while
a test injects a ``FrozenClock`` and synthetic sources for a fully-deterministic cockpit.

Why it exists / where it sits
-----------------------------
This is the cockpit-scoped composition root (deliberately NOT a second platform-wide
activation root — that is W3's; cockpit-research/PLAN.md §8 R1). It is the one place that
reaches across every cockpit layer to assemble the object graph, keeping every other module
unaware of how its collaborators are built. Sits at the top of the composition layer.

Security / compliance invariants upheld
---------------------------------------
* **Read-only wiring (CLAUDE.md §3.2):** it wires only read adapters and an append-only
  writer; the assembled application has no surface that mutates on-main domain state.
* **No secret threaded here (§5.6):** the composer takes a ``CockpitConfig`` (which carries no
  token) — the operator secret is handled only at the transport auth boundary, never wired in.
"""

from __future__ import annotations

from autofirm.cockpit.composition.cockpit_application import CockpitApplication
from autofirm.cockpit.composition.cockpit_config import CockpitConfig
from autofirm.cockpit.composition.in_memory_sources import (
    CockpitSources,
    default_in_memory_sources,
)
from autofirm.cockpit.composition.system_clock import SystemClock
from autofirm.cockpit.eventlog.append_only_event_writer import AppendOnlyEventWriter
from autofirm.org.org_identifiers import Clock

__all__ = ["assemble_cockpit"]


def assemble_cockpit(
    config: CockpitConfig,
    *,
    clock: Clock | None = None,
    sources: CockpitSources | None = None,
) -> CockpitApplication:
    """Assemble a runnable :class:`CockpitApplication` from ``config`` (keyword-only DI).

    Args:
        config: The frozen cockpit configuration (event-log path, currency, optional budget,
            optional replay source, optional kill-switch seed).
        clock: The clock to stamp recorded events with; defaults to the production
            :class:`SystemClock`. Tests inject a ``FrozenClock`` for deterministic timestamps.
        sources: The read sources to project; defaults to the in-memory fakes seeded with the
            same ``clock`` (and ``config.kill_switch_epoch``). Tests inject synthetic sources.

    Returns:
        A wired :class:`CockpitApplication` exposing the read-only snapshots and the
        append-only event recorder.
    """
    resolved_clock: Clock = SystemClock() if clock is None else clock
    resolved_sources = (
        default_in_memory_sources(resolved_clock, kill_switch_epoch=config.kill_switch_epoch)
        if sources is None
        else sources
    )
    writer = AppendOnlyEventWriter(config.event_log_path)
    return CockpitApplication(
        config=config,
        clock=resolved_clock,
        front_door_trail=resolved_sources.front_door_trail,
        org_state=resolved_sources.org_state,
        cost_ledger=resolved_sources.cost_ledger,
        kill_switch=resolved_sources.kill_switch,
        event_writer=writer,
    )
