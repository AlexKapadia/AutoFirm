"""Module entrypoint for the operator cockpit: ``python -m autofirm.cockpit``.

This is the cockpit's own runnable entry surface (the top-level ``autofirm`` console script
is owned elsewhere — cockpit-research/PLAN.md §3.2 / binding C0 override). At C0 it is a
genuine, runnable stub: it prints a single status line and exits 0, proving the build /
import / run loop end-to-end. The real launch path (argument parsing for ``run`` /
``replay`` / ``version``, the fail-closed operator auth gate, and the Textual app) lands in
gate C3+ behind :mod:`~autofirm.cockpit.transport`.

Output is written via the UTF-8-safe stream below so the status line cannot crash on a
cp1252 console (a Windows trap noted in the build playbook); printing must never be the
thing that fails.
"""

from __future__ import annotations

import sys

from autofirm.cockpit.core.cockpit_version import cockpit_version

# C0 status line: the cockpit is scaffolded but not yet wired to a backend (gates C1-C7).
_C0_STATUS_LINE = "AutoFirm cockpit {version} — not yet wired (C0 skeleton)"


def main() -> int:
    """Print the C0 status line and exit successfully.

    Returns:
        ``0`` always — the C0 stub has no failure path; it exists to prove the
        ``python -m autofirm.cockpit`` run loop works before real behaviour is wired.
    """
    # Reconfigure to UTF-8 so the status line renders identically on a cp1252 Windows
    # console and on Linux CI (the em dash would otherwise raise UnicodeEncodeError).
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print(_C0_STATUS_LINE.format(version=cockpit_version()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
