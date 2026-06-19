"""AutoFirm operator cockpit: the terminal control plane for the agent company.

This package is the human operator's live window onto a running AutoFirm: it asks the
company questions, watches the org/fleet tree, tracks spend against budget, drives the
global kill-switch and autonomy dial, and works an approval queue — all over a shared
append-only event log (cockpit-research/PLAN.md §1). It is an **add-only consumer**: it
binds the verified public interfaces of the platform (e.g.
:class:`~autofirm.frontdoor.front_door_request_dispatcher.FrontDoorRequestDispatcher`)
exactly as they are and never modifies an existing domain module.

Layering (flow order, low -> high; cockpit-research/PLAN.md §1):
* :mod:`~autofirm.cockpit.core` — PURE, side-effect-free decision logic (the mutation
  target): tree projection, spend math, budget thresholds, risk scoring, command parsing.
* :mod:`~autofirm.cockpit.eventlog` — the shared append-only NDJSON event log.
* :mod:`~autofirm.cockpit.adapters` — bind existing in-memory / ``Protocol`` backend seams.
* :mod:`~autofirm.cockpit.composition` — the cockpit-scoped dependency-injection wiring.
* :mod:`~autofirm.cockpit.transport` — operator auth + CLI launch surface.
* :mod:`~autofirm.cockpit.tui` — Textual widgets that render core outputs (no logic).

Security invariant: the pure core never performs I/O; egress and side effects live in the
adapter/transport layers behind fail-closed gates. This module exports nothing impure.

Status: C0 bootstrap — only the package skeleton and one pure module exist; real behaviour
lands in later gates (cockpit-research/PLAN.md §7, gates C1-C7).
"""

from __future__ import annotations
