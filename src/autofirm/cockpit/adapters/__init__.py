"""Cockpit adapters: bind the verified public backend seams; consume, never modify.

Each adapter wraps an existing AutoFirm interface — the front-door dispatcher and its
provenance trail, the dynamic org and capability registry, the cost ledger, the
kill-switch epoch, the saga runner, the session lifecycle engine — exactly as published
(verified constructor signatures in cockpit-research/PLAN.md §3.5) and presents a
cockpit-facing snapshot. Adapters are the *only* layer permitted to reach the platform's
domain modules; the pure core stays free of them (``cockpit-core-must-be-pure`` contract).
Egress-bearing adapters (kill-switch, session spawn) are fail-closed by default.

Status: C0 bootstrap — the concrete adapters land in gate C2.
"""

from __future__ import annotations
