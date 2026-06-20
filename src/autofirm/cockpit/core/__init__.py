"""Cockpit pure core: side-effect-free decision logic, the mutation-testing target.

Every cockpit decision (fleet-tree projection, spend roll-up math, budget-threshold
classification, approval risk scoring, autonomy-tier transitions, command parsing,
waterfall geometry, citation round-trips) is a pure function over frozen value types
(cockpit-research/PLAN.md §1.1). Purity is enforced, not merely intended: the
``cockpit-core-must-be-pure`` import-linter contract forbids this package from importing
the UI (:mod:`~autofirm.cockpit.tui`), the transport, or the backend adapters — which is
what lets the core be exhaustively mutation-tested and the UI be replaced without touching
logic.

Status: C0 bootstrap — only :mod:`~autofirm.cockpit.core.cockpit_version` exists; the real
decision modules land in gate C1.
"""

from __future__ import annotations
