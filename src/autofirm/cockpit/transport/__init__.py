"""Cockpit transport: the operator entry surface and fail-closed auth gate.

Hosts the cockpit's launch path — argument parsing for ``run`` / ``replay`` / ``version``
and the fail-closed operator auth gate (cockpit-research/PLAN.md §3.2-§3.3). The operator
token is read from the environment (``AUTOFIRM_COCKPIT_TOKEN``) or a secret manager only —
never hard-coded, never logged, never placed in events or the audit trail; no token means
refuse to launch (deny by default). The user-facing module entrypoint is
:mod:`autofirm.cockpit.__main__` (``python -m autofirm.cockpit``); the top-level
``autofirm`` console script is owned elsewhere and intentionally not registered here.

Status: C0 bootstrap — the CLI entrypoint and operator auth gate land in gate C3.
"""

from __future__ import annotations
