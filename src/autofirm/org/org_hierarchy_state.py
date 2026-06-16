"""The immutable org hierarchy: a single-rooted, acyclic tree of role charters.

What this does
--------------
Defines :class:`OrgHierarchy`, the immutable snapshot of the org's shape: the map
of every live :class:`RoleId` to its :class:`RoleCharter`, indexed so the engine
can answer the structural questions the invariants need — who manages whom, who
reports to whom, and whether a proposed reporting edge would create a cycle. The
hierarchy is *pure structure*: it validates and answers questions but does not
itself decide policy (that is the lifecycle engine's job) — keeping the cycle/
acyclicity maths here, written once, is what every invariant test exercises.

Why it exists / where it sits
-----------------------------
A strict, audited hierarchy is the core requirement (roles-as-data tree where
every manager owns its direct reports' specs, A1.5 §2). This module is the
acyclic-tree data structure underneath the engine; it depends only on the
charter contract and the identifiers, and the engine depends on it.

Security / compliance invariants upheld
---------------------------------------
* **Single-rooted, acyclic (fail-closed, CLAUDE.md §5.6):** construction refuses
  a hierarchy with no root, >1 root, a dangling manager reference, or any cycle —
  an org graph that is not a valid tree is rejected, never half-built. A role
  cannot end up reporting (transitively) to itself.
* **Manager-authored / no-orphan structure:** every non-root role names an
  existing ``manager_id``; a role whose manager is absent is refused (no orphan).
* **Immutable:** :meth:`with_role` / :meth:`without_role` return new hierarchies;
  the maps are never edited in place, so every mutation is a fresh, validated
  snapshot.
"""

from __future__ import annotations

from autofirm.org.org_identifiers import RoleId
from autofirm.org.role_charter_contract import RoleCharter

__all__ = ["HierarchyInvariantError", "OrgHierarchy"]


class HierarchyInvariantError(Exception):
    """Raised when a hierarchy would violate the single-rooted acyclic-tree invariant."""


class OrgHierarchy:
    """An immutable, single-rooted, acyclic tree of role charters.

    Construction validates the full tree invariant (exactly one root, every
    manager exists, no cycles). All mutators return a new, re-validated
    hierarchy, so an invalid org graph can never be observed.
    """

    __slots__ = ("_roles",)

    def __init__(self, roles: dict[RoleId, RoleCharter]) -> None:
        """Build and fully validate a hierarchy from a role-id -> charter map."""
        self._roles = dict(roles)
        self._validate()  # fail-closed: a malformed tree is refused at construction

    # --------------------------------------------------------------------- #
    # Construction / validation                                             #
    # --------------------------------------------------------------------- #

    @classmethod
    def with_root(cls, root: RoleCharter) -> OrgHierarchy:
        """Create a new hierarchy seeded with a single root role.

        Fail-closed: the seed must actually be a root (``manager_id is None``);
        seeding with a non-root charter would leave a dangling manager reference.
        """
        if not root.is_root():
            raise HierarchyInvariantError("with_root requires a root charter (manager_id=None)")
        return cls({root.role_id: root})

    def _validate(self) -> None:
        """Assert the single-rooted, acyclic, no-orphan tree invariant (fail-closed)."""
        roots = [r for r in self._roles.values() if r.is_root()]
        if len(roots) != 1:
            # fail-closed: an org must have exactly one apex; 0 roots = no founder,
            # >1 roots = a forest, neither is a valid single-rooted hierarchy.
            raise HierarchyInvariantError(
                f"hierarchy must have exactly one root, found {len(roots)}"
            )
        for charter in self._roles.values():
            mgr = charter.manager_id
            if mgr is None:
                continue
            if mgr not in self._roles:
                # fail-closed: a non-root role pointing at an absent manager is an
                # orphan — refuse rather than leave a dangling reference.
                raise HierarchyInvariantError(
                    f"role {charter.role_id!r} reports to unknown manager {mgr!r}"
                )
        self._assert_acyclic()

    def _assert_acyclic(self) -> None:
        """Walk every role to its root; a revisited node on the path is a cycle."""
        for start in self._roles:
            seen: set[RoleId] = set()
            node: RoleId | None = start
            while node is not None:
                if node in seen:
                    # fail-closed: a role reachable from itself via manager edges
                    # means a reporting cycle — refuse it (a tree has no cycles).
                    raise HierarchyInvariantError(f"reporting cycle detected at {node!r}")
                seen.add(node)
                node = self._roles[node].manager_id

    # --------------------------------------------------------------------- #
    # Queries                                                               #
    # --------------------------------------------------------------------- #

    def __contains__(self, role_id: RoleId) -> bool:
        """Return True if ``role_id`` is a live role in this hierarchy."""
        return role_id in self._roles

    def charter(self, role_id: RoleId) -> RoleCharter:
        """Return the charter for ``role_id`` (KeyError if absent — fail loud)."""
        return self._roles[role_id]

    def role_ids(self) -> frozenset[RoleId]:
        """The set of all live role ids."""
        return frozenset(self._roles)

    def root_id(self) -> RoleId:
        """The single root role's id (validated to exist exactly once)."""
        return next(r.role_id for r in self._roles.values() if r.is_root())

    def direct_reports(self, manager_id: RoleId) -> frozenset[RoleId]:
        """The set of roles whose ``manager_id`` is ``manager_id`` (its direct reports)."""
        return frozenset(r.role_id for r in self._roles.values() if r.manager_id == manager_id)

    def would_create_cycle(self, role_id: RoleId, new_manager_id: RoleId) -> bool:
        """True if making ``role_id`` report to ``new_manager_id`` would form a cycle.

        Used pre-emptively by re-scope: a manager that is ``role_id`` itself or one
        of its (transitive) descendants cannot become its parent without forming a
        loop. Walking up from ``new_manager_id`` must never reach ``role_id``.
        """
        node: RoleId | None = new_manager_id
        while node is not None:
            if node == role_id:
                return True  # new manager is below the role -> cycle
            node = self._roles[node].manager_id if node in self._roles else None
        return False

    # --------------------------------------------------------------------- #
    # Immutable mutators (each returns a fresh, re-validated hierarchy)      #
    # --------------------------------------------------------------------- #

    def with_role(self, charter: RoleCharter) -> OrgHierarchy:
        """Return a NEW hierarchy with ``charter`` added or replaced (re-validated)."""
        updated = {**self._roles, charter.role_id: charter}
        return OrgHierarchy(updated)

    def without_role(self, role_id: RoleId) -> OrgHierarchy:
        """Return a NEW hierarchy with ``role_id`` removed (re-validated).

        Fail-closed via re-validation: removing a manager that still has reports
        would orphan them and the new hierarchy's construction would raise — so
        the engine must reassign reports first.
        """
        updated = {k: v for k, v in self._roles.items() if k != role_id}
        return OrgHierarchy(updated)
