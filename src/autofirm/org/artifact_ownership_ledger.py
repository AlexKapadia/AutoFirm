"""The single-writer ownership ledger: exactly one owner per artifact, fail-closed.

What this does
--------------
Defines :class:`ArtifactOwnershipLedger`, the immutable map from an
:class:`ArtifactId` to the single :class:`RoleId` that currently owns it. It
enforces the **single-writer / single-accountable invariant** that is critical
to AutoFirm (per project memory: "no two agents own/edit the same artifact at
once"): assigning an artifact that is already owned by a *different* role is
**refused** (fail-closed). Releasing returns the artifact to the unowned pool so
it can be handed to another role (e.g. when a manager is fired).

Why it exists / where it sits
-----------------------------
Per ``docs/research/A1.5-auto-hiring-role-creation/SYNTHESIS.md`` §3 ("Exactly
one Accountable owner per artifact (single-writer)", sources [04][09]) and the
AutoFirm memory rule. The lifecycle engine consults and updates this ledger on
every hire (claim the charter's ``owned_artifacts``), re-scope (release old,
claim new), and fire (release all). The ledger is the data-layer enforcement of
single-writer — *not* a convention (CLAUDE.md §5.6 tenancy/isolation note: enforce
in the data layer, not by convention).

Security / compliance invariants upheld
---------------------------------------
* **Single-writer (fail-closed, CLAUDE.md §5.6):** :meth:`assign` raises
  :class:`DoubleOwnershipError` if the artifact is already owned by another role.
  A double-assignment is refused, never silently overwritten — the second writer
  is denied (deny-by-default at the ownership boundary).
* **Idempotent re-claim:** assigning an artifact to the role that *already* owns
  it is a no-op (returns the same logical ownership), so replay/re-onboarding is
  safe without weakening the single-writer guard.
* **Immutable:** every mutation returns a NEW ledger; the map is never edited in
  place, so concurrent readers always see a consistent snapshot.
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Mapping

from autofirm.org.org_identifiers import ArtifactId, RoleId

__all__ = ["ArtifactOwnershipLedger", "DoubleOwnershipError"]


class DoubleOwnershipError(Exception):
    """Raised when an artifact already owned by another role is re-assigned.

    This is the single-writer fail-closed signal: an artifact has exactly one
    owner, and a second claimant is refused rather than allowed to co-own or
    silently steal ownership.
    """

    def __init__(self, artifact_id: ArtifactId, current_owner: RoleId, claimant: RoleId) -> None:
        self.artifact_id = artifact_id
        self.current_owner = current_owner
        self.claimant = claimant
        super().__init__(
            f"artifact {artifact_id!r} already owned by {current_owner!r}; "
            f"refused second owner {claimant!r} (single-writer)"
        )


class ArtifactOwnershipLedger:
    """An immutable artifact -> single-owner map enforcing single-writer ownership.

    All mutators return a new ledger; the underlying map is exposed read-only
    (:class:`MappingProxyType`) so ownership cannot be edited by reaching past
    the API.
    """

    __slots__ = ("_owners",)

    def __init__(self, owners: Mapping[ArtifactId, RoleId] | None = None) -> None:
        # Copy into a private dict then expose read-only, so an external caller
        # cannot mutate ownership by holding a reference to the passed-in map.
        self._owners: dict[ArtifactId, RoleId] = dict(owners or {})

    @property
    def owners(self) -> Mapping[ArtifactId, RoleId]:
        """Read-only view of the current artifact -> owner map (no external mutation)."""
        return MappingProxyType(self._owners)

    def owner_of(self, artifact_id: ArtifactId) -> RoleId | None:
        """Return the current owner of ``artifact_id``, or None if unowned."""
        return self._owners.get(artifact_id)

    def assign(self, artifact_id: ArtifactId, owner: RoleId) -> ArtifactOwnershipLedger:
        """Return a NEW ledger granting ``owner`` sole ownership of ``artifact_id``.

        Fail-closed: if a *different* role already owns the artifact, raise
        :class:`DoubleOwnershipError` — single-writer refuses a second owner.
        Re-assigning to the *same* owner is an idempotent no-op (safe for replay).
        """
        current = self._owners.get(artifact_id)
        if current is not None and current != owner:
            # fail-closed: single-writer — exactly one accountable owner per
            # artifact ([04][09]). A second claimant is DENIED, not co-granted.
            raise DoubleOwnershipError(artifact_id, current, owner)
        if current == owner:
            return self  # idempotent re-claim by the same owner — no change
        updated = {**self._owners, artifact_id: owner}
        return ArtifactOwnershipLedger(updated)

    def release(self, artifact_id: ArtifactId) -> ArtifactOwnershipLedger:
        """Return a NEW ledger with ``artifact_id`` unowned (no-op if already unowned)."""
        if artifact_id not in self._owners:
            return self  # already unowned — releasing is idempotent
        updated = {k: v for k, v in self._owners.items() if k != artifact_id}
        return ArtifactOwnershipLedger(updated)

    def artifacts_owned_by(self, owner: RoleId) -> frozenset[ArtifactId]:
        """All artifacts currently owned by ``owner`` (for release-on-fire)."""
        return frozenset(a for a, r in self._owners.items() if r == owner)
