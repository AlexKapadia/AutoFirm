"""Cockpit composition: the cockpit-scoped dependency-injection wiring root.

Builds the cockpit's collaborators (front-door dispatcher, org snapshot source, cost
ledger, kill-switch holder, event sink, clock, id generator) from a frozen
``CockpitConfig`` using keyword-only DI, matching the codebase convention
(cockpit-research/PLAN.md §3.1). This is a **cockpit-scoped** root, deliberately NOT a
second platform-wide system-activation root — that is W3's responsibility, and the
collision risk is logged as PLAN §8 R1. When W3's root lands the cockpit consumes it; in
the interim it wires the public interfaces with the in-memory fakes from PLAN §3.5. Config
secrets are read from the environment only, never hard-coded.

Status: C0 bootstrap — the dependency graph, config contract, and in-memory fixtures land
in gate C3.
"""

from __future__ import annotations
