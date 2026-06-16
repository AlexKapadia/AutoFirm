"""The fail-closed dynamic-org lifecycle engine: hire, fire, re-scope, auto-create.

What this does
--------------
Defines :class:`DynamicOrg`, the engine that applies the runtime org lifecycle as
**explicit, validated, audited transitions** over an immutable
:class:`~autofirm.org.org_state.OrgState`:

* **found** — seed a new org with a single root role (the apex manager);
* **hire** — spawn a role against a manager-authored charter;
* **rescope** — replace a role's charter (new responsibilities / scope / manager);
* **fire** — retire a role (refused while it has un-reassigned reports; releases
  its artifacts);
* **auto_create_on_gap** — the gap-detect -> role-spec -> spawn pipeline that
  automatically creates a role under a managing role when a gap is detected.

Each method validates fail-closed, audits the outcome (including refusals), and
returns a NEW :class:`DynamicOrg` wrapping the next state — the engine is immutable.

Why it exists / where it sits
-----------------------------
The top of ``autofirm.org``. It encodes the A1.5 lifecycle and the strict-hierarchy
invariants while staying decoupled from real CLI-session spawning (a separate
substrate task). Mechanism (audit/ownership/authorship) lives in
:mod:`autofirm.org.org_lifecycle_internals`; this module holds the *policy*.

Security / compliance invariants upheld
---------------------------------------
* **No-spawn-without-spec (fail-closed, §5.6):** every spawn goes through a fully
  validated :class:`RoleCharter`; no code path creates a role from less.
* **Manager-authored (§5.6 / A6):** a hired/auto-created role must be authored by
  its existing managing role — no self-authoring; refused fail-closed.
* **Acyclic + no-orphan hierarchy (§5.6):** spawns/re-scopes that would cycle,
  orphan a report, or fire a manager with live reports are refused before any
  state change.
* **Single-writer ownership (§5.6):** a hire/re-scope claims artifacts via the
  ledger, which refuses double-assignment.
* **Append-only audit (§5.6 / §3.8):** every accepted mutation and refusal is
  recorded on the gapless trail.
"""

from __future__ import annotations

from autofirm.org.artifact_ownership_ledger import ArtifactOwnershipLedger, DoubleOwnershipError
from autofirm.org.gap_detection_contract import OrgGap
from autofirm.org.org_hierarchy_state import HierarchyInvariantError, OrgHierarchy
from autofirm.org.org_identifiers import Clock, IdGenerator, RoleId
from autofirm.org.org_lifecycle_events import OrgAuditTrail, OrgEventKind
from autofirm.org.org_lifecycle_internals import (
    AuthorshipError,
    append_event,
    claim_artifacts,
    reassign_artifacts,
    refuse,
    reject_if_authorship_invalid,
)
from autofirm.org.org_state import OrgState
from autofirm.org.role_charter_contract import ROOT_AUTHOR, RoleCharter

__all__ = ["DynamicOrg", "OrgState", "RoleLifecycleError"]


class RoleLifecycleError(Exception):
    """Raised when a lifecycle transition is refused (fail-closed). Always audited.

    Carries :attr:`audited_state` — the org state *with* the ``MUTATION_REFUSED``
    event appended — so a caller catching the refusal can inspect the audit trail
    and prove the denial was recorded, without the engine itself being mutated (the
    original :class:`DynamicOrg` is left untouched, preserving immutability).
    """

    def __init__(self, reason: str, audited_state: OrgState | None = None) -> None:
        """Record the refusal reason and the post-refusal audited state (None at founding)."""
        super().__init__(reason)
        # None only for a founding-time refusal (no org/trail exists yet to audit
        # onto); every post-founding refusal carries the audited state.
        self.audited_state = audited_state


class DynamicOrg:
    """The fail-closed engine applying audited lifecycle transitions to an org.

    Holds the injected :class:`Clock` and :class:`IdGenerator` (determinism seams)
    and the current :class:`OrgState`. Every public method returns a NEW
    :class:`DynamicOrg` wrapping the next state; the engine is immutable.
    """

    __slots__ = ("_clock", "_ids", "_state")

    def __init__(self, state: OrgState, clock: Clock, ids: IdGenerator) -> None:
        """Wrap an org ``state`` with its injected determinism seams (clock, id-gen)."""
        self._state = state
        self._clock = clock
        self._ids = ids

    @classmethod
    def found(cls, root: RoleCharter, clock: Clock, ids: IdGenerator) -> DynamicOrg:
        """Found a new org seeded with a single root role (the apex manager).

        Fail-closed: the root must be authored by :data:`ROOT_AUTHOR` — the apex has
        no managing role above it, so a real-manager author would imply a parent.
        Its owned artifacts seed the single-writer ledger.
        """
        if root.authored_by != ROOT_AUTHOR:
            # fail-closed: only the founder sentinel may author the apex (no parent).
            raise RoleLifecycleError("root role must be authored by ROOT_AUTHOR")
        hierarchy = OrgHierarchy.with_root(root)
        ledger = claim_artifacts(ArtifactOwnershipLedger(), root)  # single-writer claim
        state = OrgState(hierarchy=hierarchy, ownership=ledger, trail=OrgAuditTrail())
        state = append_event(
            state, clock, OrgEventKind.ROLE_HIRED, root.role_id, "founded org root"
        )
        return cls(state, clock, ids)

    @property
    def state(self) -> OrgState:
        """The current immutable org state (hierarchy + ownership + trail)."""
        return self._state

    # --------------------------------------------------------------------- #
    # Lifecycle transitions                                                 #
    # --------------------------------------------------------------------- #

    def hire(self, charter: RoleCharter) -> DynamicOrg:
        """Spawn a role against a manager-authored charter (fail-closed, audited).

        Refuses (and audits the refusal) if: the charter is a root; the managing
        role does not exist; the spec was not authored by that manager; adding the
        role would break the tree invariant; or claiming its artifacts would
        violate single-writer ownership.
        """
        try:
            reject_if_authorship_invalid(self._state, charter)
            hierarchy = self._state.hierarchy.with_role(charter)  # re-validates the tree
            ownership = claim_artifacts(self._state.ownership, charter)  # single-writer
        except (AuthorshipError, HierarchyInvariantError, DoubleOwnershipError) as exc:
            raise self._refuse(charter.role_id, str(exc)) from exc  # audited fail-closed refusal
        return self._commit(hierarchy, ownership, OrgEventKind.ROLE_HIRED, charter.role_id, "hired")

    def auto_create_on_gap(self, gap: OrgGap, new_role: RoleCharter) -> DynamicOrg:
        """Automatic role-creation: a detected gap drives the manager to spawn a role.

        Fail-closed: the gap's ``detected_by`` manager must exist and must be the
        role that both manages and authored ``new_role`` — an agent cannot
        auto-create a role outside its own command (decision-gated, [09]). Reuses
        the full hire validation, then audits as ``ROLE_AUTO_CREATED`` with the gap
        rationale as the 'why'.
        """
        if gap.detected_by not in self._state.hierarchy:
            raise self._refuse(new_role.role_id, f"gap detector {gap.detected_by!r} not in org")
        if new_role.manager_id != gap.detected_by or new_role.authored_by != gap.detected_by:
            # fail-closed: the detecting manager must be the authoring manager of the
            # filling role — no auto-creation outside the detector's own sub-org.
            raise self._refuse(
                new_role.role_id, "auto-created role must be managed & authored by the gap detector"
            )
        try:
            reject_if_authorship_invalid(self._state, new_role)
            hierarchy = self._state.hierarchy.with_role(new_role)
            ownership = claim_artifacts(self._state.ownership, new_role)
        except (AuthorshipError, HierarchyInvariantError, DoubleOwnershipError) as exc:
            raise self._refuse(new_role.role_id, str(exc)) from exc
        detail = f"auto-created for {gap.kind.value}: {gap.rationale}"
        return self._commit(
            hierarchy, ownership, OrgEventKind.ROLE_AUTO_CREATED, new_role.role_id, detail
        )

    def rescope(self, new_charter: RoleCharter) -> DynamicOrg:
        """Replace an existing role's charter at runtime (re-scope, fail-closed).

        Refuses if: the role is unknown; the new charter flips the role's root-ness;
        re-parenting would create a cycle; authorship is invalid; or the artifact
        re-claim would violate single-writer ownership. Dropped artifacts are
        released; newly-owned ones are claimed.
        """
        role_id = new_charter.role_id
        if role_id not in self._state.hierarchy:
            raise self._refuse(role_id, "cannot rescope unknown role")
        old = self._state.hierarchy.charter(role_id)
        if old.is_root() != new_charter.is_root():
            # fail-closed: re-scope cannot promote a role to apex or demote the apex
            # (would create a second root or orphan the tree).
            raise self._refuse(role_id, "rescope cannot change a role's root-ness")
        if not new_charter.is_root() and self._state.hierarchy.would_create_cycle(
            role_id, new_charter.manager_id  # type: ignore[arg-type]
        ):
            # fail-closed: re-parenting under a descendant forms a reporting cycle.
            raise self._refuse(role_id, "rescope would create a reporting cycle")
        try:
            reject_if_authorship_invalid(self._state, new_charter)
            hierarchy = self._state.hierarchy.with_role(new_charter)
            ownership = reassign_artifacts(self._state.ownership, old, new_charter)
        except (AuthorshipError, HierarchyInvariantError, DoubleOwnershipError) as exc:
            raise self._refuse(role_id, str(exc)) from exc
        return self._commit(hierarchy, ownership, OrgEventKind.ROLE_RESCOPED, role_id, "rescoped")

    def fire(self, role_id: RoleId, reassign_reports_to: RoleId | None = None) -> DynamicOrg:
        """Retire a role, releasing its artifacts (fail-closed, audited).

        Refuses to fire the root or an unknown role. A manager with live reports is
        refused unless ``reassign_reports_to`` names an existing role to inherit
        them (no orphaned reports). Reports are re-parented first (each audited),
        then the role's artifacts are released, then the role is removed — so the
        resulting hierarchy is always a valid, orphan-free tree.
        """
        if role_id not in self._state.hierarchy:
            raise self._refuse(role_id, "cannot fire unknown role")
        if role_id == self._state.hierarchy.root_id():
            raise self._refuse(role_id, "cannot fire the root role")  # fail-closed: keep an apex
        engine = self._reassign_reports_before_fire(role_id, reassign_reports_to)
        # Release every artifact the fired role owned so no retired role holds a
        # dangling single-writer lock (artifacts can be re-claimed later).
        ownership = engine._state.ownership
        for artifact in sorted(ownership.artifacts_owned_by(role_id)):
            ownership = ownership.release(artifact)
        hierarchy = engine._state.hierarchy.without_role(role_id)  # re-validates: no orphans
        return engine._commit(hierarchy, ownership, OrgEventKind.ROLE_FIRED, role_id, "fired")

    # --------------------------------------------------------------------- #
    # Internal policy helpers (state-folding delegated to internals)        #
    # --------------------------------------------------------------------- #

    def _reassign_reports_before_fire(
        self, role_id: RoleId, reassign_to: RoleId | None
    ) -> DynamicOrg:
        """Re-parent a fired manager's direct reports, or refuse if none specified."""
        reports = self._state.hierarchy.direct_reports(role_id)
        if not reports:
            return self  # leaf role — nothing to reassign
        if reassign_to is None or reassign_to not in self._state.hierarchy:
            # fail-closed: firing a manager with live reports without a valid new
            # manager would orphan them — refuse (no-orphaned-reports invariant).
            raise self._refuse(role_id, "cannot fire a manager with reports without reassignment")
        engine = self
        for report in sorted(reports):  # sorted -> deterministic audit ordering
            moved = engine._state.hierarchy.charter(report).model_copy(
                update={"manager_id": reassign_to}
            )
            hierarchy = engine._state.hierarchy.with_role(moved)
            engine = engine._commit(
                hierarchy, engine._state.ownership, OrgEventKind.REPORTS_REASSIGNED, report,
                f"reassigned to {reassign_to}",
            )
        return engine

    def _commit(
        self, hierarchy: OrgHierarchy, ownership: ArtifactOwnershipLedger,
        kind: OrgEventKind, subject: RoleId, detail: str,
    ) -> DynamicOrg:
        """Build the next state, append one audit event, and return a new engine."""
        next_state = OrgState(hierarchy=hierarchy, ownership=ownership, trail=self._state.trail)
        next_state = append_event(next_state, self._clock, kind, subject, detail)
        return DynamicOrg(next_state, self._clock, self._ids)

    def _refuse(self, subject: RoleId, reason: str) -> RoleLifecycleError:
        """Build the audited-refusal state and RETURN the error for the caller to raise.

        The refusal is recorded as ``MUTATION_REFUSED`` in a NEW state carried on the
        error (``error.audited_state``), so the denial is provable WITHOUT mutating
        this engine — the original :class:`DynamicOrg` stays immutable even on a
        refused call (CLAUDE.md §5.6 denials-audited + §3.8 append-only/immutable).
        """
        audited = refuse(self._state, self._clock, subject, reason)  # denial audited (§5.6)
        return RoleLifecycleError(reason, audited)
