"""One advertised capability of the LIVE org, as a frozen, validated descriptor.

What this does
--------------
Defines :class:`CapabilityDescriptor` — the immutable record of a single thing the
org can do right now: its stable identity, its self-documenting name, the keyword
surface a router matches against, the single owning role, the clearance a requester
needs to reach it, why it exists (:class:`CapabilityProvenance`), and where it sits
in its lifecycle (``maturity``). It also defines the opaque :class:`CapabilityId`
identifier and :class:`CapabilityProvenance`. This descriptor is the unit the
growth log records and the live registry serves to the router.

Why it exists / where it sits
-----------------------------
Per ``docs/architecture/data-contracts.md`` §9, the registry replaces the
locked-in static capability list: a capability is data, derived from the org's
real roles, not a hard-coded enum. This is the lowest layer of
``autofirm.capabilities`` — the registry event and the growth log depend on it and
nothing here depends back on them.

Security / compliance invariants upheld
---------------------------------------
* **Deny-by-default clearance (least-privilege, CLAUDE.md §5.6):** ``required_clearance``
  has NO default — it must be set explicitly, and the deny-by-default sentinel
  :data:`UNSET_CLEARANCE` is the only value that means "not yet granted" (an
  unreachable label no real requester holds). An unset clearance is a refusal at
  the routing layer, never silently open.
* **Routable-or-refuse (fail-closed):** the keyword surface must be non-empty — an
  unroutable capability is a defect, not a default, so an empty keyword set is
  refused at construction.
* **PII-free provenance (audited 'why'):** the rationale is a deterministic,
  PII-free justification; an empty rationale is refused so every capability carries
  an auditable reason it exists.
* **Immutable:** frozen once built; a re-scope produces a NEW descriptor rather
  than mutating an existing one (append-only authorship).
"""

from __future__ import annotations

from typing import Literal, NewType

from pydantic import BaseModel, ConfigDict, field_validator

from autofirm.org.org_identifiers import RoleId

__all__ = [
    "UNSET_CLEARANCE",
    "CapabilityDescriptor",
    "CapabilityId",
    "CapabilityProvenance",
    "ProvenanceKind",
]

# Opaque, typed identity for a capability (a NewType over str: static separation,
# zero runtime cost). A capability id is stable across re-scopes/promotions of the
# same capability, so the growth log can track one capability's whole lifecycle.
CapabilityId = NewType("CapabilityId", str)

# The deny-by-default clearance sentinel. A capability whose clearance is this
# label is unreachable by any real requester — least-privilege / deny-by-default
# (§5.6). It is NEVER a silent default: a descriptor must name it explicitly to
# mark "no clearance granted yet", so "forgot to grant access" fails CLOSED.
UNSET_CLEARANCE = "__unset__"

# The provenance kinds: WHY a capability came into existence. Mirrors the org
# lifecycle actions that grow the registry (a hire, a promote, or a gap-driven
# auto-create), so every capability traces to a real org event (§9 invariant).
ProvenanceKind = Literal["hire", "promote", "auto_create"]


class CapabilityProvenance(BaseModel):
    """WHY a capability exists: the org action, the org-event link, and the reason.

    ``kind`` is the lifecycle action that created it (hire / promote / auto_create).
    ``org_event_seq`` is the gapless sequence number of the org-lifecycle event that
    caused the growth (the audited link back to the org trail). ``rationale`` is the
    deterministic, PII-FREE 'why' (the same reason the org event recorded).
    """

    model_config = ConfigDict(frozen=True)

    kind: ProvenanceKind  # the org action that created the capability (closed set)
    org_event_seq: int  # gapless seq of the causing org-lifecycle event (the link)
    rationale: str  # PII-free, deterministic 'why' (audited); refused if empty

    @field_validator("org_event_seq")
    @classmethod
    def _seq_non_negative(cls, value: int) -> int:
        # fail-closed: an org-event reference is a non-negative gapless seq; a
        # negative ref cannot name a real org event, so refuse it.
        if value < 0:
            raise ValueError("provenance org_event_seq must be >= 0")
        return value

    @field_validator("rationale")
    @classmethod
    def _rationale_non_empty(cls, value: str) -> str:
        # fail-closed: a capability with no stated reason is not auditable; refuse.
        if not value.strip():
            raise ValueError("provenance rationale must be non-empty (audited 'why')")
        return value


class CapabilityDescriptor(BaseModel):
    """One advertised capability of the live org (frozen, fail-closed validated).

    Construction refuses any under-specified capability: an empty id, name, or
    keyword surface; an unset-without-the-sentinel clearance; or an unknown
    maturity. A capability that cannot be routed (no keywords) or reached
    deterministically (no explicit clearance) is a defect, not a default (§5.6).
    """

    model_config = ConfigDict(frozen=True)

    capability_id: CapabilityId  # stable identity; refused if absent/empty
    name: str  # self-documenting ("own paid acquisition"); refused if empty
    keywords: frozenset[str]  # routing surface; refused if empty (unroutable defect)
    owning_role_id: RoleId  # single-writer link — exactly one owning role
    required_clearance: str  # least-privilege: explicit; UNSET_CLEARANCE == deny
    provenance: CapabilityProvenance  # WHY it exists (hire/promote/auto_create + ref)
    maturity: Literal["proposed", "active", "deprecated"]  # lifecycle; closed set

    @field_validator("capability_id", "name", "required_clearance")
    @classmethod
    def _required_text_non_empty(cls, value: str) -> str:
        # fail-closed: an empty id/name/clearance is an under-specified capability
        # (no identity, no description, or no clearance decision). Refuse it.
        if not value.strip():
            raise ValueError("capability id/name/clearance must be non-empty")
        return value

    @field_validator("keywords")
    @classmethod
    def _keywords_non_empty(cls, value: frozenset[str]) -> frozenset[str]:
        # fail-closed: an empty keyword surface is unroutable — the router could
        # never match it, so an un-keyworded capability is a defect, not a default.
        if not value:
            raise ValueError("capability keywords must be a non-empty set (routable-or-refuse)")
        if any(not k.strip() for k in value):
            raise ValueError("capability keywords must be non-empty tokens")
        return value

    def is_reachable(self) -> bool:
        """True iff a real clearance was granted (not the deny-by-default sentinel).

        A capability still carrying :data:`UNSET_CLEARANCE` is unreachable by any
        requester — deny-by-default. This is the explicit, self-justifying check
        the routing layer uses rather than guessing from omission (§5.6).
        """
        return self.required_clearance != UNSET_CLEARANCE
