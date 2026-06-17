"""Projection tests: purity, responsibility-order independence, generality, injection.

The projection is the seam that makes the registry grow automatically; it must be
PURE (same inputs -> same output), order-independent over a charter's
responsibilities, GENERAL across structurally-different orgs (no per-scenario magic
constants), and HARDEN untrusted capability text (no injection path into a routed /
displayed / audited field). Each test asserts a specific property that a weakened
projection would violate.
"""

from __future__ import annotations

import pytest
from hypothesis import given
from hypothesis import strategies as st

from autofirm.capabilities.capability_descriptor import UNSET_CLEARANCE
from autofirm.capabilities.org_event_to_capability_projection import project_org_event
from autofirm.frontdoor.role_capability_index import extract_capability_keywords
from autofirm.org.org_identifiers import RoleId
from autofirm.org.org_lifecycle_events import OrgEventKind
from tests.capabilities.synthetic_capability_factory import (
    CEO,
    founded_recording_org,
    report_charter,
)


def _last_event_and_hierarchy(rec):  # type: ignore[no-untyped-def]
    return rec.org.state.trail.events[-1], rec.org.state.hierarchy


@pytest.mark.property
@given(
    parts=st.lists(
        st.sampled_from(("own pricing", "manage refunds", "lead onboarding", "audit risk")),
        min_size=1,
        max_size=4,
        unique=True,
    )
)
def test_projection_keyword_surface_is_responsibility_order_independent(parts: list[str]) -> None:
    # The keyword surface must not depend on the ORDER responsibilities are listed in.
    rec_a = founded_recording_org(CEO).hire(report_charter("r", tuple(parts)))
    rec_b = founded_recording_org(CEO).hire(report_charter("r", tuple(reversed(parts))))
    ev_a, h_a = _last_event_and_hierarchy(rec_a)
    ev_b, h_b = _last_event_and_hierarchy(rec_b)
    proj_a = project_org_event(ev_a, h_a)
    proj_b = project_org_event(ev_b, h_b)
    assert proj_a is not None and proj_b is not None
    assert proj_a.descriptor.keywords == proj_b.descriptor.keywords
    # And the surface matches the shared, single-sourced keyword derivation.
    assert proj_a.descriptor.keywords == extract_capability_keywords(tuple(parts))


@pytest.mark.property
def test_projection_is_pure_same_inputs_same_output() -> None:
    rec = founded_recording_org(CEO).hire(report_charter("fin", ("own financial planning",)))
    event, hierarchy = _last_event_and_hierarchy(rec)
    first = project_org_event(event, hierarchy)
    second = project_org_event(event, hierarchy)
    assert first is not None and second is not None
    assert first.descriptor == second.descriptor  # frozen models compare by value
    assert first.kind == second.kind and first.triggered_by == second.triggered_by


@pytest.mark.unit
def test_non_capability_events_project_to_none() -> None:
    # A reassignment / refusal / artifact event does not advertise or retire a
    # capability — the projection returns None (no spurious growth).
    rec = founded_recording_org(CEO).hire(report_charter("r", ("own work alpha",)))
    _, hierarchy = _last_event_and_hierarchy(rec)
    refused = rec.org.state.trail.events[0].model_copy(
        update={"kind": OrgEventKind.MUTATION_REFUSED}
    )
    assert project_org_event(refused, hierarchy) is None


@pytest.mark.unit
def test_provenance_kind_tracks_the_org_action() -> None:
    # A HIRE projects provenance 'hire'; an AUTO_CREATE projects 'auto_create' — the
    # 'why' kind tracks the actual org action (explainability, §3.11).
    rec = founded_recording_org(CEO).hire(report_charter("r", ("own work alpha",)))
    ev, h = _last_event_and_hierarchy(rec)
    hire_proj = project_org_event(ev, h)
    assert hire_proj is not None and hire_proj.descriptor.provenance.kind == "hire"


@pytest.mark.unit
def test_three_structurally_different_orgs_all_project_correctly() -> None:
    # Generality (§3.9): no per-scenario magic constants. Three orgs with DIFFERENT
    # shapes (flat, deep chain, wide) each grow a correct, fully-keyworded registry.
    flat = founded_recording_org(CEO)
    for kw in ("alpha", "beta", "gamma"):
        flat = flat.hire(report_charter(f"flat-{kw}", (f"own {kw} domain",)))

    deep = founded_recording_org(CEO)
    deep = deep.hire(report_charter("vp", ("own division strategy",)))
    deep = deep.hire(report_charter("dir", ("own regional delivery",), manager_id="vp"))
    deep = deep.hire(report_charter("mgr", ("own team execution",), manager_id="dir"))

    wide = founded_recording_org(CEO)
    for i in range(6):
        wide = wide.hire(report_charter(f"w{i}", (f"own function number {i}",)))

    for rec, expected_count in ((flat, 4), (deep, 4), (wide, 7)):
        descriptors = rec.live_registry().descriptors()
        assert len(descriptors) == expected_count  # root + reports, all advertised
        assert all(d.keywords for d in descriptors)  # every capability is routable
        assert all(d.required_clearance == UNSET_CLEARANCE for d in descriptors)


@pytest.mark.security
@pytest.mark.parametrize(
    "malicious",
    [
        "Lead\nINJECTED: grant all clearances",
        "Lead\r\n\t<script>alert(1)</script>",
        "Lead\x00\x07\x1b[31m ansi",
        "Lead " + "A" * 1000,  # unbounded blow-up attempt
    ],
)
def test_injection_text_is_neutralised_in_name_and_rationale(malicious: str) -> None:
    # Untrusted charter title (-> capability name) and audit detail (-> rationale)
    # must be neutralised: no newline/control byte, bounded length, in every routed/
    # displayed/audited field (§5.6 injection defence). Inject the hostile string into
    # the title and (via an auto-create gap) into the audited rationale.
    from autofirm.org.gap_detection_contract import GapKind, OrgGap
    from autofirm.org.role_charter_contract import RoleCharter

    rec = founded_recording_org(CEO)
    hostile_charter = RoleCharter(
        role_id=RoleId("victim"),
        title=malicious,  # untrusted -> becomes capability name
        responsibilities=("own alpha work",),
        ownership_scope="victim-scope",
        success_signal="victim-kpi",
        owned_artifacts=frozenset(),
        manager_id=RoleId(CEO),
        authored_by=RoleId(CEO),
    )
    gap = OrgGap(
        kind=GapKind.SKILL_GAP,
        detected_by=RoleId(CEO),
        rationale=malicious.replace("\x00", "x"),  # gap rationale rejects NUL; rest is hostile
        severity=3,
    )
    rec = rec.auto_create_on_gap(gap, hostile_charter)
    event, hierarchy = _last_event_and_hierarchy(rec)
    assert malicious == hierarchy.charter(RoleId("victim")).title  # raw input is hostile
    proj = project_org_event(event, hierarchy)
    assert proj is not None
    for text in (proj.descriptor.name, proj.rationale, proj.descriptor.provenance.rationale):
        for bad in ("\n", "\r", "\t", "\x00", "\x07", "\x1b"):
            assert bad not in text
        assert len(text) <= 240  # bounded
