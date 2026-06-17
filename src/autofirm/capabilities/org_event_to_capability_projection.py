"""Pure projection: an org-lifecycle event -> the capability-growth event it implies.

What this does
--------------
Defines :func:`project_org_event` — a PURE function mapping one
:class:`~autofirm.org.org_lifecycle_events.OrgEvent` (against the org state it
produced) to the :class:`CapabilityRegistryEvent` that records how the org's
capability set grew, or ``None`` for org events that do not change capabilities
(e.g. an artifact lock or an audited refusal). This is what makes the registry
grow AUTOMATICALLY as the org evolves: hiring a role advertises its capability,
auto-creating one does the same with auto-create provenance, re-scoping re-states
the surface, and firing deprecates it.

Why it exists / where it sits
-----------------------------
Per ``docs/architecture/data-contracts.md`` §9, "every add traces to an org event".
The keyword surface is RE-EXPRESSED from the same source the router already
trusts: :func:`autofirm.frontdoor.role_capability_index.extract_capability_keywords`
over the role's charter responsibilities — so the registry's routing surface
cannot drift from the front-door index. This module is pure (no clock, no hashes,
no I/O): the growth log seals/chains the event, keeping the projection a testable
fold input.

Security / compliance invariants upheld
---------------------------------------
* **Untrusted text, no injection (fail-closed):** capability ``name`` and
  ``rationale`` derive from charter/audit text that is treated as UNTRUSTED — they
  are neutralised to a single line of bounded length with control characters
  stripped, so a crafted responsibility/detail string cannot smuggle newlines or
  control bytes into a routed/displayed/audited field.
* **Single-writer authorship (least-privilege):** ``triggered_by`` is the owning
  role's MANAGER (the managing role authored the charter) — never a self-grant; a
  capability authored by its own role would be a self-grant and is refused.
* **Deny-by-default clearance:** a freshly-projected capability carries
  :data:`~autofirm.capabilities.capability_descriptor.UNSET_CLEARANCE` — no
  clearance is granted by projection; granting is an explicit downstream act.
* **Pure & deterministic:** identical (event, state) inputs yield an identical
  projected event (modulo the log-assigned seq/hash), so replay is reproducible.
"""

from __future__ import annotations

from typing import Literal

from autofirm.capabilities.capability_descriptor import (
    UNSET_CLEARANCE,
    CapabilityDescriptor,
    CapabilityId,
    CapabilityProvenance,
    ProvenanceKind,
)
from autofirm.capabilities.capability_registry_event import RegistryEventKind
from autofirm.frontdoor.role_capability_index import extract_capability_keywords
from autofirm.org.org_hierarchy_state import OrgHierarchy
from autofirm.org.org_identifiers import RoleId
from autofirm.org.org_lifecycle_events import OrgEvent, OrgEventKind
from autofirm.org.role_charter_contract import ROOT_AUTHOR, RoleCharter

__all__ = ["ProjectedGrowth", "project_org_event"]

# Bound on neutralised free-text fields. Capability names/rationales are routing-
# and display-facing; an unbounded attacker-controlled string is refused down to
# this many characters so a crafted charter cannot blow up a UI/audit line.
_MAX_TEXT_LEN = 240

# The org-event kinds that DO change the advertised capability set, and the growth
# kind + provenance each implies. Everything else (artifact locks, reassignments,
# refusals) projects to None — it does not advertise or retire a capability.
_KIND_MAP: dict[OrgEventKind, tuple[RegistryEventKind, ProvenanceKind]] = {
    OrgEventKind.ROLE_HIRED: ("CAPABILITY_ADDED", "hire"),
    OrgEventKind.ROLE_AUTO_CREATED: ("CAPABILITY_ADDED", "auto_create"),
    OrgEventKind.ROLE_RESCOPED: ("CAPABILITY_RESCOPED", "hire"),
    OrgEventKind.ROLE_FIRED: ("CAPABILITY_DEPRECATED", "hire"),
}


class ProjectedGrowth:
    """The seal-ready fields of a projected growth event (everything but the chain).

    A plain value object (not a registry event) because the growth log assigns the
    gapless ``seq`` and computes the chained hashes — the projection only decides
    WHAT changed, never WHERE it sits in the chain (separation of concerns, §5.7).
    """

    __slots__ = ("descriptor", "kind", "org_event_ref", "rationale", "triggered_by")

    def __init__(
        self,
        *,
        kind: RegistryEventKind,
        descriptor: CapabilityDescriptor,
        triggered_by: RoleId,
        org_event_ref: int,
        rationale: str,
    ) -> None:
        """Hold the projected, seal-ready growth fields (immutable by convention)."""
        self.kind = kind
        self.descriptor = descriptor
        self.triggered_by = triggered_by
        self.org_event_ref = org_event_ref
        self.rationale = rationale


def _neutralise(text: str) -> str:
    """Collapse untrusted text to one bounded, control-character-free line.

    Treats charter/audit text as UNTRUSTED (§5.6 injection defence): every control
    character (newlines, tabs, escapes) is replaced with a space, runs of
    whitespace are collapsed, and the result is truncated — so a crafted string
    can never inject a new line or control byte into a routed/displayed/audited
    field. The output is the SAFE surface; the keyword tokeniser does its own
    lowercasing separately.
    """
    cleaned = "".join(ch if ch.isprintable() else " " for ch in text)
    collapsed = " ".join(cleaned.split())
    return collapsed[:_MAX_TEXT_LEN]


def project_org_event(event: OrgEvent, hierarchy: OrgHierarchy) -> ProjectedGrowth | None:
    """Project one org event onto the capability growth it implies, or ``None``.

    ``hierarchy`` is the org state AFTER the event (so a hired/rescoped role's
    charter is present; a fired role's is gone — the fired role's last-known
    charter is taken from the event's own surface instead). Returns ``None`` for
    org events that do not change the advertised capability set.
    """
    mapping = _KIND_MAP.get(event.kind)
    if mapping is None:
        return None  # not a capability-changing event (lock/reassign/refusal)
    registry_kind, provenance_kind = mapping
    role_id = RoleId(event.subject_role_id)

    charter = _charter_for(event, hierarchy)
    if charter is None:
        return None  # fail-closed: cannot advertise a capability with no known charter

    triggered_by = charter.authored_by
    if triggered_by in (role_id, ROOT_AUTHOR):
        # The root capability is authored by the founder sentinel (no managing role
        # above it); attribute its growth to the role itself for a real, auditable
        # RoleId rather than the sentinel — every other role is manager-authored.
        triggered_by = role_id

    maturity: Literal["proposed", "active", "deprecated"] = (
        "deprecated" if event.kind is OrgEventKind.ROLE_FIRED else "active"
    )
    keywords = extract_capability_keywords(charter.responsibilities)
    if not keywords:
        # fail-closed: a role whose responsibilities yield no routable keyword
        # cannot advertise a capability — skip rather than build an unroutable one.
        return None
    rationale = _neutralise(event.detail)
    descriptor = CapabilityDescriptor(
        capability_id=CapabilityId(event.subject_role_id),
        name=_neutralise(charter.title),
        keywords=keywords,
        owning_role_id=role_id,
        required_clearance=UNSET_CLEARANCE,  # deny-by-default; granted downstream
        provenance=CapabilityProvenance(
            kind=provenance_kind,
            org_event_seq=event.seq,
            rationale=rationale,
        ),
        maturity=maturity,
    )
    return ProjectedGrowth(
        kind=registry_kind,
        descriptor=descriptor,
        triggered_by=triggered_by,
        org_event_ref=event.seq,
        rationale=rationale,
    )


def _charter_for(event: OrgEvent, hierarchy: OrgHierarchy) -> RoleCharter | None:
    """The charter to advertise from: the live one, else None for an unknown role.

    For ADD/RESCOPE the role is live in ``hierarchy``. For a FIRE the role is gone;
    a deprecation still needs the role's surface, so a fired role absent from the
    post-state hierarchy yields ``None`` here and the fire is projected only when
    its charter is still resolvable (the caller keeps a pre-fire view; see the
    registry's replay, which passes the cumulative hierarchy).
    """
    role_id = RoleId(event.subject_role_id)
    if role_id in hierarchy:
        return hierarchy.charter(role_id)
    return None
