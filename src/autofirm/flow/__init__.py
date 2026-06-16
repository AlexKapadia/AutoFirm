"""Flow plane: work moves through the org as audited, traceable handoffs.

What this package does
----------------------
Implements AutoFirm's first-class *flow* primitive — the typed
:class:`~autofirm.flow.work_item.WorkItem` that moves through the org as a
deterministic state machine (created -> assigned -> in-progress ->
handed-off -> done/blocked) where **every transition is recorded in an
append-only, gapless flow trail** with full provenance (from-role, to-role,
reason, injected timestamp). It is the operational realisation of the AutoFirm
ethos line "everything flows" and rides on the same fail-closed, append-only,
determinism-by-injected-clock discipline the org / comms / audit planes use.

Where it sits
-------------
Conceptually a flow rides the comms bus (a handoff is a message) and emits into
the audit log; this package depends only on its own typed contracts so it can be
unit-tested in isolation, and the orchestrator wires the trail to the real Merkle
audit sink at the composition root (same seam pattern as
``autofirm.comms.append_only_audit_sink``).
"""

from __future__ import annotations

from autofirm.flow.flow_state_machine import (
    ALLOWED_TRANSITIONS,
    TERMINAL_STATES,
    WorkState,
    is_allowed_transition,
    is_terminal,
)
from autofirm.flow.work_item import WorkItem
from autofirm.flow.work_item_flow_trail import FlowTrail, FlowTransition

__all__ = [
    "ALLOWED_TRANSITIONS",
    "TERMINAL_STATES",
    "FlowTrail",
    "FlowTransition",
    "WorkItem",
    "WorkState",
    "is_allowed_transition",
    "is_terminal",
]
