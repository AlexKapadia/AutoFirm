"""Cockpit TUI: Textual widgets that render pure-core outputs and dispatch commands.

The widgets hold **no business logic** (cockpit-research/PLAN.md §1.1): they render the
value types produced by :mod:`~autofirm.cockpit.core` into Textual views and translate
keypresses into core ``Command`` objects. They are proven with Textual ``Pilot`` state
tests and one home-screen snapshot, and are deliberately excluded from the mutation gate
(pixels, not logic). The refresh model is a fixed ~2s synchronized tick fed by a coalesced,
bounded event queue — never a repaint per event — so a busy log never floods the UI.

Status: C0 bootstrap — the Textual app and widgets land in gates C4-C5.
"""

from __future__ import annotations
