"""Pure fail-closed helpers behind the lifecycle engine: audit, refuse, ownership.

What this does
--------------
Holds the small, pure helper functions the :class:`~autofirm.org.org_lifecycle_engine.DynamicOrg`
engine composes: appending one audit event, recording a fail-closed refusal,
validating that a charter was authored by its existing managing role, and the
single-writer artifact claim/reassign operations. Splitting these out keeps the
engine module under the 300-line responsibility limit (CLAUDE.md §5.7) while
keeping the *policy* (what is refused and why) in the engine and the *mechanism*
(how state is folded) here.

Why it exists / where it sits
-----------------------------
Imported only by :mod:`autofirm.org.org_lifecycle_engine`. Every function is pure:
it takes a current :class:`OrgState` (and the inputs) and returns a NEW
:class:`OrgState` — no in-place mutation — so the engine stays a deterministic
fold and refusals are themselves recorded on the append-only trail.

Security / compliance invariants upheld
---------------------------------------
* **Append-only audit (§5.6 / §3.8):** :func:`append_event` only ever extends the
  trail at the next gapless seq.
* **Refusals are audited, not dropped (§5.6):** :func:`refuse` records a
  ``MUTATION_REFUSED`` event and returns the next state + the error, so a denial is
  always provable.
* **Manager-authored (§5.6 / A6):** :func:`reject_if_authorship_invalid` refuses a
  non-root charter whose ``authored_by`` is not its existing managing role.
* **Single-writer (§5.6):** :func:`claim_artifacts` / :func:`reassign_artifacts`
  go through the ledger, which refuses any double-assignment.
"""

from __future__ import annotations

from autofirm.org.artifact_ownership_ledger import ArtifactOwnershipLedger
from autofirm.org.org_identifiers import Clock, RoleId
from autofirm.org.org_lifecycle_events import OrgEvent, OrgEventKind
from autofirm.org.org_state import OrgState
from autofirm.org.role_charter_contract import RoleCharter

__all__ = [
    "AuthorshipError",
    "append_event",
    "claim_artifacts",
    "reassign_artifacts",
    "refuse",
    "reject_if_authorship_invalid",
]


class AuthorshipError(Exception):
    """Internal signal that a charter's authorship/manager is invalid (fail-closed)."""


def append_event(
    state: OrgState, clock: Clock, kind: OrgEventKind, subject: RoleId, detail: str
) -> OrgState:
    """Return a NEW state with one audit event appended (gapless, append-only).

    The event's seq is the trail's next seq (== current length), so the log is
    strictly ordered and cannot be rewritten; the timestamp comes from the
    injected clock (deterministic).
    """
    event = OrgEvent(
        seq=state.trail.next_seq,  # gapless: position == seq (append-only, §5.6)
        kind=kind,
        subject_role_id=str(subject),
        detail=detail,
        timestamp=clock.now(),  # injected clock -> deterministic timestamp
    )
    return OrgState(
        hierarchy=state.hierarchy,
        ownership=state.ownership,
        trail=state.trail.append(event),
    )


def refuse(state: OrgState, clock: Clock, subject: RoleId, reason: str) -> OrgState:
    """Audit a fail-closed refusal and return the next state (denial recorded, not dropped).

    A ``MUTATION_REFUSED`` event is appended so the trail proves the system refused
    rather than silently ignoring the request (CLAUDE.md §5.6). The caller raises
    :class:`~autofirm.org.org_lifecycle_engine.RoleLifecycleError` after recording.
    """
    return append_event(state, clock, OrgEventKind.MUTATION_REFUSED, subject, reason)


def reject_if_authorship_invalid(state: OrgState, charter: RoleCharter) -> None:
    """Raise :class:`AuthorshipError` unless ``charter`` is authored by its existing manager.

    Fail-closed (§5.6): a non-root charter must (a) not be a root, (b) name a
    manager that exists, and (c) be authored by that same managing role — no
    self-authoring and no authoring by an absent or unrelated role ([09], A6).
    """
    if charter.is_root():
        raise AuthorshipError("only found() may create a root role")
    mgr = charter.manager_id
    if mgr is None or mgr not in state.hierarchy:
        # fail-closed: cannot report to a manager that does not exist (no orphan).
        # (is_root() above already implies mgr is not None; the explicit check
        # narrows the Optional type and is defence-in-depth against a future edit.)
        raise AuthorshipError(f"manager {mgr!r} does not exist")
    if charter.authored_by != mgr:
        # fail-closed: a role's spec is OWNED & AUTHORED by its managing role.
        raise AuthorshipError("spec must be authored by the managing role")


def claim_artifacts(
    ownership: ArtifactOwnershipLedger, charter: RoleCharter
) -> ArtifactOwnershipLedger:
    """Claim every artifact in ``charter`` for its role (single-writer, fail-closed).

    Iterates in sorted order for deterministic claim sequencing; the ledger refuses
    any artifact already owned by a different role (single-writer, §5.6).
    """
    for artifact in sorted(charter.owned_artifacts):
        ownership = ownership.assign(artifact, charter.role_id)  # refuses double-assign
    return ownership


def reassign_artifacts(
    ownership: ArtifactOwnershipLedger, old: RoleCharter, new: RoleCharter
) -> ArtifactOwnershipLedger:
    """Release artifacts dropped by a re-scope, then claim the newly-owned ones."""
    for dropped in sorted(old.owned_artifacts - new.owned_artifacts):
        ownership = ownership.release(dropped)
    for artifact in sorted(new.owned_artifacts):
        ownership = ownership.assign(artifact, new.role_id)  # single-writer still enforced
    return ownership
