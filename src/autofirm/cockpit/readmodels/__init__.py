"""Cockpit read-models: the immutable boundary DTOs the cockpit presents to the operator.

These are the *output* shapes the cockpit hands to its UI / transport layers: a snapshot of
recent front-door activity, the org tree, and spend against budget. They are PURE value
types — frozen, side-effect-free, and free of any on-main domain import (a view never
reaches back into ``autofirm.frontdoor`` / ``autofirm.org`` / ``autofirm.costledger`` /
``autofirm.modelgateway``; the :mod:`~autofirm.cockpit.adapters` layer does the reading and
hands these views out). They depend only on the foundation ``Money`` primitive, the pure
cockpit-core :class:`~autofirm.cockpit.core.budget_threshold_state.BudgetBand`, and stdlib.

Why it exists / where it sits
-----------------------------
Separating the *presented shape* from the *reading adapter* keeps the read seam testable in
isolation and lets the UI bind a stable DTO that never changes when an on-main contract is
re-wired. Sits above the pure core and below the adapters (cockpit-research/PLAN.md §1, §3).

Security / compliance invariants upheld
---------------------------------------
* **Read-only projection (CLAUDE.md §3.2):** a view is an immutable snapshot; it carries no
  handle that could mutate an on-main domain object.
* **Immutable:** every view is frozen; mapping fields are wrapped read-only so a presented
  snapshot cannot be edited after construction.
"""

from __future__ import annotations
