"""The work-item flow primitive: audited, role-authorised handoffs through the org.

What this does
--------------
Defines :class:`WorkItem`, the typed unit of work that moves through the org as a
deterministic state machine (see :mod:`autofirm.flow.flow_state_machine`). Every
move is performed through one of the explicit verbs (:meth:`assign_to`,
:meth:`start`, :meth:`hand_off`, :meth:`complete`, :meth:`block`,
:meth:`resume`), and each verb:

1. checks the edge is legal in the state machine (no skipped/illegal states),
2. checks the receiving role is in the caller-supplied set of *known* roles
   (fail-closed: a handoff to an unknown/unauthorised role is refused), then
3. records a complete :class:`~autofirm.flow.work_item_flow_trail.FlowTransition`
   (from-role, to-role, reason, injected timestamp) in the append-only trail.

The item is immutable: each verb returns a NEW :class:`WorkItem` carrying the
extended trail, so the history is append-only and a rejected move leaves the prior
item untouched.

Why it exists / where it sits
-----------------------------
This is the public face of the flow plane — "everything flows" made concrete. It
depends only on the state machine, the trail, and the injected clock, so it is
unit-testable in isolation; the orchestrator supplies the live set of org roles
(from ``autofirm.org``) and mirrors the trail into the audit log at the wiring
root.

Security / compliance invariants upheld
---------------------------------------
* **Fail-closed authorisation (CLAUDE.md §5.6):** a handoff/assignment to a role
  not present in ``known_roles`` is refused — the flow denies by default rather
  than routing work to an unknown destination.
* **No illegal/skipped transitions:** every verb consults the state machine; an
  edge not in the legal table raises, so a work item can never jump states.
* **Gapless, complete trail (§3.8):** every accepted move appends exactly one
  fully-populated transition at the next seq; the trail is the complete
  provenance of the item's flow.
"""

from __future__ import annotations

from autofirm.flow.flow_state_machine import WorkState, is_allowed_transition
from autofirm.flow.injected_flow_clock import FlowClock
from autofirm.flow.work_item_flow_trail import FlowTrail, FlowTransition

__all__ = ["IllegalTransitionError", "UnknownRoleError", "WorkItem"]


class IllegalTransitionError(Exception):
    """Raised when a verb would drive an edge the state machine forbids."""


class UnknownRoleError(Exception):
    """Raised when work is routed to a role outside the known/authorised set."""


class WorkItem:
    """An immutable unit of work flowing through the org via audited handoffs.

    Construct via :meth:`create`; never instantiate a partially-built item. Each
    transition verb returns a NEW :class:`WorkItem` whose trail has grown by
    exactly one transition (append-only, no in-place mutation).
    """

    __slots__ = ("_clock", "_known_roles", "_owner", "_state", "_trail", "_work_id")

    def __init__(  # noqa: PLR0913 — private full-state snapshot ctor; public path is create()
        self,
        *,
        work_id: str,
        state: WorkState,
        owner: str | None,
        trail: FlowTrail,
        clock: FlowClock,
        known_roles: frozenset[str],
    ) -> None:
        """Build a work item from a fully-validated snapshot (use :meth:`create`)."""
        self._work_id = work_id
        self._state = state
        self._owner = owner  # the role currently owning the item (None when CREATED)
        self._trail = trail
        self._clock = clock
        self._known_roles = known_roles

    # ------------------------------------------------------------------ #
    # Construction                                                       #
    # ------------------------------------------------------------------ #

    @classmethod
    def create(
        cls,
        *,
        work_id: str,
        clock: FlowClock,
        known_roles: frozenset[str],
    ) -> WorkItem:
        """Create a brand-new work item in the CREATED state with an empty trail.

        Fail-closed: ``work_id`` must be non-empty and ``known_roles`` must be
        non-empty — a flow with no traceable id, or one that can never legally be
        assigned to any role, is mis-specified and refused at creation.
        """
        if not work_id.strip():
            raise ValueError("work_id must be non-empty (traceable flow id)")  # fail-closed
        if not known_roles:
            # fail-closed: with no known roles every assignment would be refused,
            # so the item could never legally leave CREATED — reject up front.
            raise ValueError("known_roles must be non-empty (no destination otherwise)")
        return cls(
            work_id=work_id,
            state=WorkState.CREATED,
            owner=None,
            trail=FlowTrail(),
            clock=clock,
            known_roles=known_roles,
        )

    # ------------------------------------------------------------------ #
    # Read-only views                                                    #
    # ------------------------------------------------------------------ #

    @property
    def work_id(self) -> str:
        """The stable, traceable identity of this unit of work."""
        return self._work_id

    @property
    def state(self) -> WorkState:
        """The current lifecycle state."""
        return self._state

    @property
    def owner(self) -> str | None:
        """The role currently owning the item (``None`` only while CREATED)."""
        return self._owner

    @property
    def trail(self) -> FlowTrail:
        """The append-only provenance trail of every transition so far."""
        return self._trail

    # ------------------------------------------------------------------ #
    # Transition verbs (each returns a NEW, validated WorkItem)          #
    # ------------------------------------------------------------------ #

    def assign_to(self, role: str, reason: str) -> WorkItem:
        """Assign a freshly-created item to its first owning ``role``.

        Legal only from CREATED (the state machine enforces this). Fail-closed if
        ``role`` is unknown. ``from_role`` on the recorded transition is ``None``
        (a created item had no prior owner).
        """
        return self._transition(WorkState.ASSIGNED, new_owner=role, to_role=role, reason=reason)

    def start(self, reason: str) -> WorkItem:
        """Move an ASSIGNED item to IN_PROGRESS under its current owner.

        The owner does not change; the item stays with the role that owns it.
        """
        return self._transition(
            WorkState.IN_PROGRESS,
            new_owner=self._owner,
            to_role=self._require_owner(),
            reason=reason,
        )

    def hand_off(self, to_role: str, reason: str) -> WorkItem:
        """Transfer an IN_PROGRESS item to ``to_role`` (an audited handoff).

        Fail-closed if ``to_role`` is unknown. Records the relinquishing owner as
        ``from_role`` and lands the item in HANDED_OFF; call :meth:`receive` to
        re-assign it under the new owner.
        """
        return self._transition(
            WorkState.HANDED_OFF, new_owner=to_role, to_role=to_role, reason=reason
        )

    def receive(self, reason: str) -> WorkItem:
        """Re-assign a HANDED_OFF item under its new owner (HANDED_OFF -> ASSIGNED)."""
        return self._transition(
            WorkState.ASSIGNED,
            new_owner=self._owner,
            to_role=self._require_owner(),
            reason=reason,
        )

    def block(self, reason: str) -> WorkItem:
        """Mark the item BLOCKED on a dependency (recoverable via :meth:`resume`)."""
        return self._transition(
            WorkState.BLOCKED,
            new_owner=self._owner,
            to_role=self._require_owner(),
            reason=reason,
        )

    def resume(self, reason: str) -> WorkItem:
        """Resume a BLOCKED item back to IN_PROGRESS under its current owner."""
        return self._transition(
            WorkState.IN_PROGRESS,
            new_owner=self._owner,
            to_role=self._require_owner(),
            reason=reason,
        )

    def complete(self, reason: str) -> WorkItem:
        """Complete an IN_PROGRESS item (IN_PROGRESS -> DONE, a terminal sink)."""
        return self._transition(
            WorkState.DONE,
            new_owner=self._owner,
            to_role=self._require_owner(),
            reason=reason,
        )

    # ------------------------------------------------------------------ #
    # Internal transition engine                                         #
    # ------------------------------------------------------------------ #

    def _require_owner(self) -> str:
        """Return the current owner, refusing a verb that needs one when unowned."""
        if self._owner is None:
            # fail-closed: start/hand_off/etc. require an owning role; a CREATED
            # item has none, so the only legal first move is assign_to.
            raise IllegalTransitionError("item has no owner yet; assign it first")
        return self._owner

    def _transition(
        self, target: WorkState, *, new_owner: str | None, to_role: str, reason: str
    ) -> WorkItem:
        """Validate, authorise, and record one transition; return the new item.

        The order is deliberate: legality first (no illegal/skipped state), then
        authorisation (no unknown role), then the append. A failure at any step
        raises and leaves ``self`` untouched (immutability / append-only).
        """
        if not is_allowed_transition(self._state, target):
            # fail-closed: an edge absent from the legal table is forbidden.
            raise IllegalTransitionError(
                f"illegal transition {self._state} -> {target}"
            )
        if to_role not in self._known_roles:
            # fail-closed (§5.6): never route work to a role outside the known/
            # authorised set — refuse rather than hand off into the unknown.
            raise UnknownRoleError(f"unknown/unauthorised role {to_role!r}")
        transition = FlowTransition(
            seq=self._trail.next_seq,  # gapless: exactly the next position
            from_state=self._state,
            to_state=target,
            from_role=self._owner,  # the relinquishing owner (None on first assign)
            to_role=to_role,
            reason=reason,
            timestamp=self._clock.now(),  # injected clock — deterministic (§3.11)
        )
        return WorkItem(
            work_id=self._work_id,
            state=target,
            owner=new_owner,
            trail=self._trail.append(transition),  # append-only growth
            clock=self._clock,
            known_roles=self._known_roles,
        )
