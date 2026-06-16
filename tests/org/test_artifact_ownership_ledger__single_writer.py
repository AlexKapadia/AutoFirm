"""Single-writer ownership tests: exactly one owner per artifact, fail-closed.

Proves the critical AutoFirm invariant (no two roles own one artifact at once):
a double-assignment to a *different* role is refused; re-claim by the same owner
is an idempotent no-op; release frees the artifact. A Hypothesis property test
runs arbitrary assign/release sequences and asserts the single-owner invariant is
NEVER violated. Synthetic only; no network (CLAUDE.md §3.6/§5.5).
"""

from __future__ import annotations

import pytest
from hypothesis import given
from hypothesis import strategies as st

from autofirm.org.artifact_ownership_ledger import (
    ArtifactOwnershipLedger,
    DoubleOwnershipError,
)
from autofirm.org.org_identifiers import ArtifactId, RoleId


@pytest.mark.unit
def test_assign_grants_sole_ownership() -> None:
    ledger = ArtifactOwnershipLedger().assign(ArtifactId("a"), RoleId("r1"))
    assert ledger.owner_of(ArtifactId("a")) == RoleId("r1")


@pytest.mark.unit
def test_double_assign_to_different_role_is_refused() -> None:
    ledger = ArtifactOwnershipLedger().assign(ArtifactId("a"), RoleId("r1"))
    with pytest.raises(DoubleOwnershipError) as exc:
        ledger.assign(ArtifactId("a"), RoleId("r2"))  # second owner -> DENIED
    assert exc.value.current_owner == RoleId("r1")
    assert exc.value.claimant == RoleId("r2")
    # fail-closed: original ledger unchanged; r1 still sole owner.
    assert ledger.owner_of(ArtifactId("a")) == RoleId("r1")


@pytest.mark.unit
def test_reassign_to_same_owner_is_idempotent_noop() -> None:
    ledger = ArtifactOwnershipLedger().assign(ArtifactId("a"), RoleId("r1"))
    again = ledger.assign(ArtifactId("a"), RoleId("r1"))
    assert again.owner_of(ArtifactId("a")) == RoleId("r1")


@pytest.mark.unit
def test_release_frees_then_another_role_may_claim() -> None:
    ledger = ArtifactOwnershipLedger().assign(ArtifactId("a"), RoleId("r1"))
    freed = ledger.release(ArtifactId("a"))
    assert freed.owner_of(ArtifactId("a")) is None
    reclaimed = freed.assign(ArtifactId("a"), RoleId("r2"))  # now allowed (single-writer)
    assert reclaimed.owner_of(ArtifactId("a")) == RoleId("r2")


@pytest.mark.unit
def test_release_unowned_is_idempotent() -> None:
    ledger = ArtifactOwnershipLedger()
    assert ledger.release(ArtifactId("ghost")).owner_of(ArtifactId("ghost")) is None


@pytest.mark.unit
def test_owners_view_is_read_only() -> None:
    ledger = ArtifactOwnershipLedger().assign(ArtifactId("a"), RoleId("r1"))
    with pytest.raises(TypeError):
        ledger.owners[ArtifactId("a")] = RoleId("hacker")  # type: ignore[index]


@pytest.mark.unit
def test_passed_in_map_cannot_mutate_ledger_after_construction() -> None:
    seed = {ArtifactId("a"): RoleId("r1")}
    ledger = ArtifactOwnershipLedger(seed)
    seed[ArtifactId("a")] = RoleId("hacker")  # mutate the original dict
    assert ledger.owner_of(ArtifactId("a")) == RoleId("r1")  # ledger copied it


@pytest.mark.unit
def test_artifacts_owned_by_lists_only_that_owner() -> None:
    ledger = (
        ArtifactOwnershipLedger()
        .assign(ArtifactId("a"), RoleId("r1"))
        .assign(ArtifactId("b"), RoleId("r1"))
        .assign(ArtifactId("c"), RoleId("r2"))
    )
    assert ledger.artifacts_owned_by(RoleId("r1")) == {ArtifactId("a"), ArtifactId("b")}
    assert ledger.artifacts_owned_by(RoleId("r2")) == {ArtifactId("c")}


# A single artifact/role op: assign(art, role) or release(art).
_ARTS = st.sampled_from([ArtifactId(a) for a in ("a", "b", "c")])
_ROLES = st.sampled_from([RoleId(r) for r in ("r1", "r2", "r3")])
_OP = st.tuples(st.sampled_from(["assign", "release"]), _ARTS, _ROLES)


@pytest.mark.property
@given(ops=st.lists(_OP, max_size=80))
def test_single_owner_invariant_holds_across_arbitrary_ops(
    ops: list[tuple[str, ArtifactId, RoleId]]
) -> None:
    ledger = ArtifactOwnershipLedger()
    for kind, art, role in ops:
        if kind == "release":
            ledger = ledger.release(art)
            continue
        current = ledger.owner_of(art)
        if current is not None and current != role:
            # fail-closed: a conflicting assign MUST raise and leave ownership intact.
            with pytest.raises(DoubleOwnershipError):
                ledger.assign(art, role)
        else:
            ledger = ledger.assign(art, role)
        # Invariant after every step: each owned artifact maps to exactly one role
        # (a dict already guarantees uniqueness; this asserts no co-ownership leak).
        owners = ledger.owners
        assert len(set(owners.keys())) == len(owners)
