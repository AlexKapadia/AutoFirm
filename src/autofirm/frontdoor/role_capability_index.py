"""The role-capability index: what each org role can handle, derived from the org.

What this does
--------------
Defines :class:`RoleCapability` (one role's advertised handling capability — the
keywords it covers, the clearance a requester needs to reach it, and whether it is the
designated triage fallback) and :class:`RoleCapabilityIndex`, an immutable lookup that
turns the live :class:`~autofirm.org.org_state.OrgState` into the routing target space.
The index is the ONLY thing the router consults to decide who handles a request; the
human never sees it.

Why it exists / where it sits
-----------------------------
The org engine models roles-as-data (each :class:`~autofirm.org.role_charter_contract.RoleCharter`
declares ``responsibilities`` and a ``title``). Capabilities are derived from those
responsibilities — a role's responsibility phrases ARE its capability surface — so the
routable space cannot drift from the real org chart. Clearance requirements are supplied
explicitly at build time (a routing-policy concern, not something a charter declares), so
least-privilege is configured where it is owned, not guessed from free text.

Security / compliance invariants upheld
---------------------------------------
* **Least privilege (CLAUDE.md §5.6):** every capability carries an explicit
  ``required_clearance``. A role with no entry in the supplied clearance map defaults to
  the most restrictive sentinel (unreachable without an explicit grant) — deny by
  default, never open by omission.
* **Single triage fallback (fail-closed routing seam):** exactly one capability is the
  designated triage target; construction REFUSES an index with zero or many triage
  roles, so the router always has exactly one place to fail-closed to (never a guess,
  never nowhere).
* **Determinism (§3.11):** capabilities and their keyword sets are derived by a pure,
  order-independent function of the charter text, so the same org yields the same index
  every run.
* **Immutability:** the index is frozen; a changed org produces a NEW index via
  :meth:`from_org_state`, never an in-place edit.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass

from autofirm.org.org_identifiers import RoleId
from autofirm.org.org_state import OrgState

__all__ = [
    "PUBLIC_CLEARANCE",
    "UNREACHABLE_CLEARANCE",
    "RoleCapability",
    "RoleCapabilityIndex",
    "extract_capability_keywords",
]

# The clearance a member of the public holds implicitly. A role requiring this is
# reachable by anyone whose request authenticates at all (see the permission policy).
PUBLIC_CLEARANCE = "public"

# The sentinel required-clearance for any role NOT given an explicit clearance in the
# build-time map. No real requester ever holds this label, so an un-mapped role is
# unreachable by default — deny-by-default / least-privilege (§5.6). This is what makes
# "forgot to grant access" fail CLOSED (unreachable) rather than OPEN (everyone).
UNREACHABLE_CLEARANCE = "__unreachable__"

# Word-character tokeniser. Capability keywords are lowercased word tokens of length >= 3
# extracted from a role's responsibilities; short tokens ("to", "of", "a") carry no
# routing signal and are dropped so they cannot cause spurious matches.
_MIN_KEYWORD_LEN = 3
_WORD_RE = re.compile(r"[a-z0-9]+")


def extract_capability_keywords(phrases: tuple[str, ...]) -> frozenset[str]:
    """Derive the lowercased keyword set a role covers from its responsibility phrases.

    Pure and order-independent: tokenises each phrase into word tokens, lowercases them,
    and keeps tokens of length >= ``_MIN_KEYWORD_LEN``. Two roles with the same
    responsibilities (in any order) yield the same keyword set (determinism, §3.11).
    """
    keywords: set[str] = set()
    for phrase in phrases:
        for token in _WORD_RE.findall(phrase.lower()):
            if len(token) >= _MIN_KEYWORD_LEN:
                keywords.add(token)
    return frozenset(keywords)


@dataclass(frozen=True, slots=True)
class RoleCapability:
    """One role's advertised handling capability — a routing target.

    ``keywords`` is the capability surface matched against a request's intent terms.
    ``required_clearance`` is the single clearance label a requester must hold to reach
    this role (least-privilege). ``is_triage`` marks the one designated fallback role
    that fields anything no other role can capably handle (fail-closed target).
    """

    role_id: RoleId  # the org role this capability belongs to
    title: str  # human-readable title (for provenance: "handled by FP&A Lead")
    keywords: frozenset[str]  # the responsibility-derived capability surface
    required_clearance: str  # the single clearance needed to reach this role (§5.6)
    is_triage: bool  # True for the one designated fail-closed fallback role


class RoleCapabilityIndex:
    """Immutable map of role-id -> :class:`RoleCapability`, with one triage fallback.

    Built from an :class:`OrgState` plus an explicit clearance map and a nominated triage
    role. Construction validates that exactly one capability is the triage fallback so
    the router always has precisely one fail-closed destination.
    """

    __slots__ = ("_by_role", "_triage_role_id")

    def __init__(self, capabilities: tuple[RoleCapability, ...]) -> None:
        """Build the index from capabilities; validate exactly one triage fallback."""
        triage = tuple(c for c in capabilities if c.is_triage)
        if len(triage) != 1:
            # fail-closed: with zero triage roles the router would have nowhere to send
            # an unmatched request (silent drop); with many it would have to guess. The
            # whole fail-closed guarantee rests on there being exactly one. (§5.6)
            raise ValueError(
                f"index must have exactly one triage role, found {len(triage)}"
            )
        self._by_role: dict[RoleId, RoleCapability] = {c.role_id: c for c in capabilities}
        self._triage_role_id: RoleId = triage[0].role_id

    @classmethod
    def from_org_state(
        cls,
        state: OrgState,
        *,
        triage_role_id: RoleId,
        required_clearances: Mapping[RoleId, str],
    ) -> RoleCapabilityIndex:
        """Derive a capability index from a live org snapshot (deny-by-default clearances).

        Each live role becomes a :class:`RoleCapability` whose keywords come from its
        charter responsibilities. ``triage_role_id`` names the single fallback role.
        ``required_clearances`` grants each role its required clearance; a role absent
        from the map gets :data:`UNREACHABLE_CLEARANCE` — least-privilege, deny by
        default (§5.6). Fail-closed: the triage role must actually exist in the org.
        """
        if triage_role_id not in state.hierarchy:
            # fail-closed: a triage target that is not a live role would leave unmatched
            # requests routed to a non-existent handler — refuse to build such an index.
            raise ValueError(f"triage role {triage_role_id!r} is not a live org role")
        capabilities: list[RoleCapability] = []
        for role_id in sorted(state.hierarchy.role_ids()):  # sorted -> deterministic order
            charter = state.hierarchy.charter(role_id)
            capabilities.append(
                RoleCapability(
                    role_id=role_id,
                    title=charter.title,
                    keywords=extract_capability_keywords(charter.responsibilities),
                    # deny-by-default: un-granted roles become unreachable, not public.
                    required_clearance=required_clearances.get(
                        role_id, UNREACHABLE_CLEARANCE
                    ),
                    is_triage=(role_id == triage_role_id),
                )
            )
        return cls(tuple(capabilities))

    def triage_capability(self) -> RoleCapability:
        """The single designated triage fallback capability (always present)."""
        return self._by_role[self._triage_role_id]

    def capability_for(self, role_id: RoleId) -> RoleCapability | None:
        """The capability for ``role_id``, or None if it is not a routing target."""
        return self._by_role.get(role_id)

    def non_triage_capabilities(self) -> tuple[RoleCapability, ...]:
        """Every capability except the triage fallback, in deterministic role-id order.

        The router scores these to find a capable handler; triage is reserved as the
        explicit no-match destination, never a scored candidate.
        """
        return tuple(
            self._by_role[rid]
            for rid in sorted(self._by_role)
            if rid != self._triage_role_id
        )
