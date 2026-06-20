"""Module entrypoint for the operator cockpit: ``python -m autofirm.cockpit``.

This is the cockpit's own runnable entry surface (the top-level ``autofirm`` console script
is owned elsewhere — cockpit-research/PLAN.md §3.2 / binding C0 override). It is intentionally
tiny: it delegates to :func:`autofirm.cockpit.transport.cockpit_cli.main` (which parses
``version`` / ``run`` / ``replay``, enforces the fail-closed operator auth gate, and prints the
read-only snapshots) and exits with that command's return code.
"""

from __future__ import annotations

from autofirm.cockpit.transport.cockpit_cli import main

if __name__ == "__main__":  # pragma: no cover - thin process-entry guard
    raise SystemExit(main())
