"""The requester clearance gate: least-privilege check before a role is reachable.

What this does
--------------
Defines :func:`requester_may_reach` — the single pure predicate deciding whether a given
:class:`~autofirm.frontdoor.human_request_contract.RequesterIdentity` is permitted to be
routed to a given :class:`~autofirm.frontdoor.role_capability_index.RoleCapability`. The
router calls this on EVERY candidate role before considering it a match, so a requester
can only ever reach roles they are cleared for.

Why it exists / where it sits
-----------------------------
Least-privilege (CLAUDE.md §5.6) is a routing concern distinct from capability matching:
a role might be the most *capable* handler yet be one the requester is not *permitted* to
reach. Separating the clearance gate from the capability scorer keeps each a single
responsibility (§5.7) and makes the security check independently testable and impossible
to accidentally bypass inside scoring.

Security / compliance invariants upheld
---------------------------------------
* **Deny by default / fail closed (§5.6):** the predicate returns True ONLY when the
  clearance is satisfied; every other path (unknown clearance, the unreachable sentinel,
  a requester missing the label) returns False. There is no "allow on ambiguity" branch.
* **Public is an explicit grant, not an absence:** a role requiring
  :data:`~autofirm.frontdoor.role_capability_index.PUBLIC_CLEARANCE` is reachable by any
  authenticated requester; a role whose required clearance is the unreachable sentinel is
  reachable by NO ONE (that is the deny-by-default outcome for un-granted roles).
* **Least privilege:** a requester reaches a non-public role only by explicitly holding
  its required clearance label — never by holding *more* clearances or by default.
"""

from __future__ import annotations

from autofirm.frontdoor.human_request_contract import RequesterIdentity
from autofirm.frontdoor.role_capability_index import (
    PUBLIC_CLEARANCE,
    UNREACHABLE_CLEARANCE,
    RoleCapability,
)

__all__ = ["requester_may_reach"]


def requester_may_reach(
    requester: RequesterIdentity, capability: RoleCapability
) -> bool:
    """Return True iff ``requester`` is permitted to be routed to ``capability``.

    Decision table (fail-closed — the ONLY True paths are the first two):

    * required clearance is the unreachable sentinel -> **False** (deny by default: the
      role was never granted reachability, so no one reaches it).
    * required clearance is PUBLIC -> **True** (any authenticated requester may reach it).
    * requester holds the exact required clearance label -> **True** (explicit grant).
    * otherwise -> **False** (least-privilege: more clearances or a near-miss do not
      open a role the requester was not explicitly granted).
    """
    required = capability.required_clearance
    if required == UNREACHABLE_CLEARANCE:
        # fail-closed: an un-granted role is unreachable, full stop (§5.6).
        return False
    if required == PUBLIC_CLEARANCE:
        return True  # public roles are reachable by any authenticated requester
    # Non-public role: reachable ONLY by a requester explicitly holding its clearance.
    return required in requester.clearances
