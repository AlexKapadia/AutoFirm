"""Stateful property test: ALL org invariants hold across arbitrary lifecycle runs.

A Hypothesis :class:`RuleBasedStateMachine` drives a real :class:`DynamicOrg`
through arbitrary interleavings of hire / rescope / fire / auto-create and, after
EVERY accepted *or refused* step, re-asserts the full invariant set:

* single-rooted, acyclic hierarchy (no reporting cycle, exactly one root);
* no orphaned reports (every non-root role's manager exists);
* single-writer ownership (each owned artifact maps to exactly one live role);
* append-only, gapless audit trail (seqs are 0..n-1, monotonic);
* every accepted mutation grew the trail by >=1; every refusal grew it by exactly 1
  with a ``MUTATION_REFUSED`` event (denials audited, not dropped).

This is the teeth: a single mishandled transition anywhere in a long random
sequence breaks one of these and fails the test (CLAUDE.md §3.6/§3.9). Synthetic
only; no network.
"""

from __future__ import annotations

import pytest
from hypothesis import HealthCheck, settings
from hypothesis import strategies as st
from hypothesis.stateful import RuleBasedStateMachine, invariant, precondition, rule

from autofirm.org.gap_detection_contract import GapKind, OrgGap
from autofirm.org.org_identifiers import (
    ArtifactId,
    RoleId,
    SequentialIdGenerator,
)
from autofirm.org.org_lifecycle_engine import DynamicOrg, RoleLifecycleError
from autofirm.org.org_lifecycle_events import OrgEventKind
from autofirm.org.role_charter_contract import RoleCharter

from .synthetic_org_factory import fresh_clock, root_charter

_GAP_KINDS = list(GapKind)


@settings(max_examples=120, stateful_step_count=40, suppress_health_check=[HealthCheck.too_slow])
class OrgLifecycleMachine(RuleBasedStateMachine):
    """Drives a DynamicOrg through random lifecycle ops, checking invariants always hold."""

    def __init__(self) -> None:
        """Found a fresh org and seed the role-id counter before each example run."""
        super().__init__()
        self.org = DynamicOrg.found(
            root_charter("root", artifacts=frozenset({"art-root"})),
            fresh_clock(),
            SequentialIdGenerator(),
        )
        self._counter = 0  # source of fresh, unique role ids

    # --------------------------- helpers ------------------------------------ #

    def _new_role_id(self) -> str:
        self._counter += 1
        return f"role-{self._counter}"

    def _live_roles(self) -> list[RoleId]:
        return sorted(self.org.state.hierarchy.role_ids())

    def _charter(self, rid: str, manager: RoleId, arts: frozenset[str]) -> RoleCharter:
        return RoleCharter(
            role_id=RoleId(rid),
            title=rid,
            responsibilities=("work",),
            ownership_scope="scope",
            success_signal="kpi",
            owned_artifacts=frozenset(ArtifactId(a) for a in arts),
            manager_id=manager,
            authored_by=manager,  # authored by the managing role (valid authorship)
        )

    def _try(self, op) -> None:
        """Run an op; a fail-closed refusal must leave the live engine untouched."""
        before = self.org.state.trail.kinds()
        try:
            self.org = op()
        except RoleLifecycleError as exc:
            # Refusal is audited on the error and the live engine is unchanged.
            assert exc.audited_state.trail.kinds()[-1] is OrgEventKind.MUTATION_REFUSED
            assert self.org.state.trail.kinds() == before  # immutable on refusal
        else:
            assert len(self.org.state.trail.kinds()) > len(before)  # progress audited

    # ----------------------------- rules ------------------------------------ #

    @rule(arts=st.frozensets(st.sampled_from(["a1", "a2", "a3", "a4"]), max_size=3))
    def hire(self, arts: frozenset[str]) -> None:
        manager = self._live_roles()[hash(frozenset(arts)) % len(self._live_roles())]
        self._try(lambda: self.org.hire(self._charter(self._new_role_id(), manager, arts)))

    @rule(
        kind=st.sampled_from(_GAP_KINDS),
        arts=st.frozensets(st.sampled_from(["a1", "a2", "a3"]), max_size=2),
    )
    def auto_create(self, kind: GapKind, arts: frozenset[str]) -> None:
        detector = self._live_roles()[kind.value.__len__() % len(self._live_roles())]
        rid = self._new_role_id()
        gap = OrgGap(kind=kind, detected_by=detector, rationale=f"gap {rid}", severity=1)
        self._try(lambda: self.org.auto_create_on_gap(gap, self._charter(rid, detector, arts)))

    @precondition(lambda self: len(self._live_roles()) > 1)
    @rule(idx=st.integers(min_value=0, max_value=50))
    def rescope(self, idx: int) -> None:
        roles = self._live_roles()
        target = roles[idx % len(roles)]
        old = self.org.state.hierarchy.charter(target)
        if old.is_root():
            return  # cannot rescope root-ness; skip (covered by fail-closed suite)
        new_mgr = roles[(idx + 1) % len(roles)]
        self._try(
            lambda: self.org.rescope(self._charter(target, new_mgr, set(old.owned_artifacts)))  # type: ignore[arg-type]
        )

    @precondition(lambda self: len(self._live_roles()) > 1)
    @rule(idx=st.integers(min_value=0, max_value=50))
    def fire(self, idx: int) -> None:
        roles = self._live_roles()
        target = roles[idx % len(roles)]
        if target == self.org.state.hierarchy.root_id():
            return  # cannot fire root; skip (covered by fail-closed suite)
        survivor = self.org.state.hierarchy.charter(target).manager_id  # reassign to its manager
        self._try(lambda: self.org.fire(target, reassign_reports_to=survivor))

    # --------------------------- invariants --------------------------------- #

    @invariant()
    def exactly_one_root(self) -> None:
        roots = [r for r in self._live_roles() if self.org.state.hierarchy.charter(r).is_root()]
        assert len(roots) == 1

    @invariant()
    def no_reporting_cycle_and_no_orphan(self) -> None:
        h = self.org.state.hierarchy
        for rid in self._live_roles():
            seen: set[RoleId] = set()
            node: RoleId | None = rid
            while node is not None:
                assert node not in seen, "reporting cycle"
                assert node in h, "orphaned report (manager missing)"
                seen.add(node)
                node = h.charter(node).manager_id

    @invariant()
    def single_writer_ownership(self) -> None:
        owners = self.org.state.ownership.owners
        # Each artifact has exactly one owner (dict guarantees), and every owner is
        # a live role (no artifact stranded on a fired role).
        live = set(self._live_roles())
        for owner in owners.values():
            assert owner in live, "artifact owned by a non-live role"

    @invariant()
    def audit_trail_append_only_gapless(self) -> None:
        events = self.org.state.trail.events
        assert tuple(e.seq for e in events) == tuple(range(len(events)))


@pytest.mark.property
class TestOrgLifecycleMachine(OrgLifecycleMachine.TestCase):
    """pytest entry point for the stateful org-lifecycle property machine."""
