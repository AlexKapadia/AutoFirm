"""The append-only audit trail of org mutations (roles-as-data transition log).

What this does
--------------
Defines the typed, immutable :class:`OrgEvent` records — one per org mutation
(hire, fire, re-scope, automatic role-creation, artifact assignment/release) —
and the :class:`OrgAuditTrail` that holds them as a strictly append-only,
gapless, sequence-numbered log. Every state change the lifecycle engine makes is
recorded here *before or atomically with* the state change, so the trail is a
complete, replayable history of how the org reached its current shape.

Why it exists / where it sits
-----------------------------
Per ``docs/research/A1.5-auto-hiring-role-creation/SYNTHESIS.md`` §2 ("every
stage is append-only audited (roles-as-data trail, ties A6.1/A6.2)") and
CLAUDE.md §5.6 ("immutable, append-only audit log of every sensitive action").
This mirrors the append-only discipline already on ``main`` (the Merkle audit
log): the trail only ever grows, sequence numbers are gapless and monotonic, and
no API exposes update or delete.

Security / compliance invariants upheld
---------------------------------------
* **Append-only (CLAUDE.md §5.6 / §3.8):** :meth:`OrgAuditTrail.append` returns a
  NEW trail with the event added; there is no mutate/delete path. Re-appending an
  out-of-order sequence is refused (fail-closed) so the log can never be
  retroactively rewritten.
* **Gapless monotonic seq:** each event's ``seq`` is exactly ``len(events)``;
  a gap or duplicate is refused at append time, so a dropped/duplicated mutation
  is detectable.
* **Denials are recorded, not dropped:** a refused mutation is appended as a
  :class:`OrgEventKind.MUTATION_REFUSED` event — the log proves the system
  fail-closed rather than silently ignoring the request (§5.6).
* **Immutable events:** each :class:`OrgEvent` is frozen.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, field_validator

__all__ = ["OrgAuditTrail", "OrgEvent", "OrgEventKind"]


class OrgEventKind(StrEnum):
    """The exhaustive set of audited org-mutation kinds (deterministic menu)."""

    ROLE_HIRED = "ROLE_HIRED"  # a role spawned against a manager-authored charter
    ROLE_FIRED = "ROLE_FIRED"  # a role retired (after reports/artifacts handled)
    ROLE_RESCOPED = "ROLE_RESCOPED"  # a role's charter replaced with a new one
    ROLE_AUTO_CREATED = "ROLE_AUTO_CREATED"  # gap-detected -> manager authored a new role
    ARTIFACT_ASSIGNED = "ARTIFACT_ASSIGNED"  # single-owner lock granted
    ARTIFACT_RELEASED = "ARTIFACT_RELEASED"  # single-owner lock released
    REPORTS_REASSIGNED = "REPORTS_REASSIGNED"  # a fired manager's reports moved
    MUTATION_REFUSED = "MUTATION_REFUSED"  # a fail-closed refusal (audited, not dropped)


class OrgEvent(BaseModel):
    """One immutable, sequence-numbered org-mutation record.

    ``seq`` is gapless and monotonic (enforced by :class:`OrgAuditTrail`).
    ``detail`` carries a short, deterministic, PII-free description of the change
    (e.g. the role id and the reason), never raw sensitive content.
    """

    model_config = ConfigDict(frozen=True)

    seq: int  # gapless monotonic counter (== position in the trail)
    kind: OrgEventKind
    subject_role_id: str  # the role the event is primarily about
    detail: str  # deterministic, PII-free description of the mutation
    timestamp: datetime  # from the injected Clock (deterministic)

    @field_validator("seq")
    @classmethod
    def _seq_non_negative(cls, value: int) -> int:
        # fail-closed: sequence numbers are non-negative monotonic counters.
        if value < 0:
            raise ValueError("seq must be >= 0")
        return value


class OrgAuditTrail(BaseModel):
    """An append-only, gapless log of :class:`OrgEvent` records.

    Immutable: :meth:`append` returns a new trail; there is no update or delete
    API (append-only, CLAUDE.md §5.6 / §3.8). This is the single source of truth
    for *how* the org reached its current state.
    """

    model_config = ConfigDict(frozen=True)

    events: tuple[OrgEvent, ...] = ()

    def append(self, event: OrgEvent) -> OrgAuditTrail:
        """Return a NEW trail with ``event`` appended (append-only).

        Fail-closed: the event's ``seq`` must equal the current length, so the
        log is gapless and strictly ordered — a caller cannot insert, skip, or
        overwrite a sequence number (which would let history be rewritten).
        """
        if event.seq != len(self.events):
            # fail-closed: a non-consecutive seq would create a gap or overwrite,
            # breaking the append-only / gapless invariant (§5.6). Refuse it.
            raise ValueError(
                f"non-consecutive audit seq: expected {len(self.events)}, got {event.seq}"
            )
        return OrgAuditTrail(events=(*self.events, event))

    @property
    def next_seq(self) -> int:
        """The seq the next appended event must carry (== current length)."""
        return len(self.events)

    def kinds(self) -> tuple[OrgEventKind, ...]:
        """The ordered tuple of event kinds — a compact view of the history."""
        return tuple(e.kind for e in self.events)
