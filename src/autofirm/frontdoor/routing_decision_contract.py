"""The routing decision: the explainable, provenance-carrying result of front-desk routing.

What this does
--------------
Defines :class:`RoutingOutcome` (the closed set of what can happen to a request) and
:class:`RoutingDecision` — the immutable record the front desk produces for EVERY
request, capturing which role was chosen, WHY it was chosen (the matched terms or the
fail-closed reason), the requester and correlation id it belongs to, and the injected
decision time. This is the provenance object: it is what gets audited and what is handed
back to the requester so an answer can say exactly which role handled it and why it was
routed there.

Why it exists / where it sits
-----------------------------
The front door must be "auditable end-to-end" with provenance (which role handled it,
when, why). Making the decision a typed value (rather than a tuple or dict the router
returns ad hoc) means every outcome — a clean route, a no-capable-role triage, a
no-clearance triage — carries the same complete provenance shape, so the audit trail can
NEVER be partial. A decision is always produced; a request is never lost.

Security / compliance invariants upheld
---------------------------------------
* **No request lost (fail-closed completeness, CLAUDE.md §5.6):** every routing call
  yields exactly one :class:`RoutingDecision` with a non-None ``chosen_role_id`` — either
  a capable role or the triage fallback. There is no "no decision" / dropped path.
* **Explain every decision (§3.11):** ``reason`` names precisely why this role was
  chosen (the matched terms, or the specific fail-closed cause), so the routing is
  self-justifying and an auditor can retrace it without re-running the router.
* **Immutability:** frozen — the audited decision is exactly the decision that drove
  delivery; it cannot be edited after the fact.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from autofirm.org.org_identifiers import RoleId

__all__ = ["RoutingDecision", "RoutingOutcome"]


class RoutingOutcome(StrEnum):
    """Closed set of routing outcomes — exactly one applies to every decision.

    A closed set keeps the decision auditable and lets verification reason about every
    path. ``ROUTED_TO_CAPABLE_ROLE`` is the success path; the two ``TRIAGED_*`` outcomes
    are the fail-closed paths — distinct so the audit trail shows WHY a request fell back
    to triage (no capable role vs. no clearance for the capable role).
    """

    ROUTED_TO_CAPABLE_ROLE = "routed_to_capable_role"  # a permitted, capable role matched
    TRIAGED_NO_CAPABLE_ROLE = "triaged_no_capable_role"  # nothing matched -> fallback
    TRIAGED_NO_PERMITTED_ROLE = "triaged_no_permitted_role"  # matched but not cleared


class RoutingDecision:
    """The immutable, provenance-carrying outcome of routing one human request.

    Always names a ``chosen_role_id`` (a capable role OR the triage fallback) so a
    request is never lost. ``reason`` is the human-readable justification (matched terms
    or fail-closed cause). ``matched_terms`` records exactly which intent terms drove a
    capable match (empty for a triage outcome), so the explanation is checkable against
    the request and the role's capability surface.
    """

    __slots__ = (
        "_chosen_role_id",
        "_chosen_role_title",
        "_correlation_id",
        "_decided_at",
        "_matched_terms",
        "_outcome",
        "_reason",
        "_requester_id",
    )

    def __init__(  # noqa: PLR0913 -- a provenance record is intrinsically wide; every
        # field is load-bearing for the audit trail and all are immutable.
        self,
        *,
        correlation_id: str,
        requester_id: str,
        outcome: RoutingOutcome,
        chosen_role_id: RoleId,
        chosen_role_title: str,
        matched_terms: frozenset[str],
        reason: str,
        decided_at: datetime,
    ) -> None:
        """Construct an immutable routing decision (all fields keyword-only)."""
        self._correlation_id = correlation_id
        self._requester_id = requester_id
        self._outcome = outcome
        self._chosen_role_id = chosen_role_id
        self._chosen_role_title = chosen_role_title
        self._matched_terms = matched_terms
        self._reason = reason
        self._decided_at = decided_at

    @property
    def correlation_id(self) -> str:
        """The request's correlation id (threads request -> decision -> response)."""
        return self._correlation_id

    @property
    def requester_id(self) -> str:
        """The id of the requester this decision belongs to."""
        return self._requester_id

    @property
    def outcome(self) -> RoutingOutcome:
        """Which of the closed outcomes applied (routed vs. one of the triage causes)."""
        return self._outcome

    @property
    def chosen_role_id(self) -> RoleId:
        """The role the request was routed to (a capable role OR triage — never None)."""
        return self._chosen_role_id

    @property
    def chosen_role_title(self) -> str:
        """The chosen role's human-readable title (for provenance readability)."""
        return self._chosen_role_title

    @property
    def matched_terms(self) -> frozenset[str]:
        """The intent terms that drove a capable match (empty for a triage outcome)."""
        return self._matched_terms

    @property
    def reason(self) -> str:
        """The human-readable justification for this routing decision (explain-everything)."""
        return self._reason

    @property
    def decided_at(self) -> datetime:
        """When the decision was made (injected clock, never the wall clock)."""
        return self._decided_at

    @property
    def is_triaged(self) -> bool:
        """True iff this request fell back to triage (either fail-closed cause)."""
        return self._outcome is not RoutingOutcome.ROUTED_TO_CAPABLE_ROLE
