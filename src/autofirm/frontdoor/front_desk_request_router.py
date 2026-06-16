"""The front-desk request router: classify a human request and resolve its handler.

What this does
--------------
Defines :class:`FrontDeskRequestRouter` — the deterministic core that takes a validated
:class:`~autofirm.frontdoor.human_request_contract.HumanRequest` and produces exactly one
:class:`~autofirm.frontdoor.routing_decision_contract.RoutingDecision`. It (1) asks the
injected classifier for the request's intent terms, (2) scores every non-triage
capability by keyword overlap, (3) drops candidates the requester is not cleared to reach
(least-privilege), and (4) routes to the single best capable+permitted role — or, if none
qualifies, fails closed to the one triage role with the precise cause.

Why it exists / where it sits
-----------------------------
This is the brain of the human->company front door, sitting between the typed request
boundary and the response/audit dispatch. The human does NOT need to know the org chart:
the router resolves the right role from capabilities derived from the live org. Every
decision is a pure function of (request, capability index, classifier), so routing is
reproducible and never depends on wall-clock or hidden state — only the decision's
timestamp comes from the injected clock.

Security / compliance invariants upheld
---------------------------------------
* **No request lost, no mis-route (fail-closed, CLAUDE.md §5.6):** the method ALWAYS
  returns a decision; a request with no capable+permitted role goes to the single triage
  role, never to an incapable role and never nowhere. A role only counts as a match if it
  shares >= 1 intent term AND the requester is cleared for it.
* **Least privilege (§5.6):** a not-cleared role is removed from contention via the
  clearance gate BEFORE selection, so a requester can never be routed to a role they may
  not reach — even if it is the most capable.
* **Determinism (§3.11):** scoring and tie-breaking are total and order-independent
  (best score, then lowest role-id), so the same inputs yield the same chosen role every
  run; only ``decided_at`` varies, and only via the injected clock.
* **Explain every decision (§3.11):** the decision records the matched terms (capable
  route) or the exact fail-closed cause (triage), so it is self-justifying.
"""

from __future__ import annotations

from autofirm.frontdoor.human_request_contract import HumanRequest
from autofirm.frontdoor.request_intent_classifier import RequestIntentClassifier
from autofirm.frontdoor.requester_clearance_gate import requester_may_reach
from autofirm.frontdoor.role_capability_index import RoleCapability, RoleCapabilityIndex
from autofirm.frontdoor.routing_decision_contract import RoutingDecision, RoutingOutcome
from autofirm.org.org_identifiers import Clock

__all__ = ["FrontDeskRequestRouter"]


class FrontDeskRequestRouter:
    """Resolves the correct handling role for a human request, or fails closed to triage.

    Stateless across calls apart from its injected collaborators (capability index,
    classifier, clock), all supplied at construction — no hidden global state, so the
    router is trivially reproducible and testable.
    """

    __slots__ = ("_classifier", "_clock", "_index")

    def __init__(
        self,
        *,
        capability_index: RoleCapabilityIndex,
        classifier: RequestIntentClassifier,
        clock: Clock,
    ) -> None:
        """Wire the router from its collaborators (dependency injection, fail-closed).

        All three are mandatory (no defaults): the router refuses to exist without a
        routing target space (the index), a way to read intent (the classifier), and a
        deterministic time source (the clock) — fail-closed configuration (§5.6).
        """
        self._index = capability_index
        self._classifier = classifier
        self._clock = clock

    def route(self, request: HumanRequest) -> RoutingDecision:
        """Resolve ``request`` to exactly one role, returning an explainable decision.

        Always returns a decision (a request is never lost). The flow is:
        classify -> score capable candidates -> apply clearance gate -> select best, or
        fail closed to triage with the precise cause.
        """
        terms = self._classifier.intent_terms(request)
        # A capable candidate shares >= 1 intent term with the request. We compute the
        # overlap once per role so both selection and the explanation use the same set.
        capable = self._capable_candidates(terms)
        if not capable:
            # fail-closed: nothing in the org can capably handle this -> the single
            # triage role, with the distinct "no capable role" cause (§5.6).
            return self._triage(
                request, RoutingOutcome.TRIAGED_NO_CAPABLE_ROLE, frozenset()
            )

        # Least-privilege: keep only candidates the requester is actually cleared to
        # reach. A capable-but-forbidden role must NEVER be chosen (§5.6).
        permitted = [
            (capability, overlap)
            for capability, overlap in capable
            if requester_may_reach(request.requester, capability)
        ]
        if not permitted:
            # fail-closed: a capable role existed but the requester is not cleared for
            # any -> triage, with the distinct "no permitted role" cause (so the audit
            # trail shows this was an access decision, not a capability gap).
            return self._triage(
                request, RoutingOutcome.TRIAGED_NO_PERMITTED_ROLE, frozenset()
            )

        chosen, overlap = self._select_best(permitted)
        return RoutingDecision(
            correlation_id=request.correlation_id,
            requester_id=request.requester.requester_id,
            outcome=RoutingOutcome.ROUTED_TO_CAPABLE_ROLE,
            chosen_role_id=chosen.role_id,
            chosen_role_title=chosen.title,
            matched_terms=overlap,
            reason=(
                f"routed to {chosen.title!r}: capability matched intent terms "
                f"{sorted(overlap)}"
            ),
            decided_at=self._clock.now(),  # injected clock, never the wall clock
        )

    def _capable_candidates(
        self, terms: frozenset[str]
    ) -> list[tuple[RoleCapability, frozenset[str]]]:
        """Every non-triage role sharing >= 1 intent term, with its matched-term set.

        Pure derivation from the index and the request terms; the triage role is never a
        scored candidate (it is reserved as the explicit fail-closed destination).
        """
        candidates: list[tuple[RoleCapability, frozenset[str]]] = []
        for capability in self._index.non_triage_capabilities():
            overlap = terms & capability.keywords
            if overlap:
                candidates.append((capability, overlap))
        return candidates

    @staticmethod
    def _select_best(
        permitted: list[tuple[RoleCapability, frozenset[str]]],
    ) -> tuple[RoleCapability, frozenset[str]]:
        """Pick the single best candidate: most matched terms, then lowest role-id.

        Total and deterministic (§3.11): the primary key is the match count (more matched
        intent terms == better handler); ties are broken by the LOWEST role-id, a total
        order, so selection never depends on iteration order and is identical every run.
        """
        best_score = max(len(overlap) for _, overlap in permitted)
        top = [item for item in permitted if len(item[1]) == best_score]
        # Deterministic tie-break: among equal-scoring candidates, the smallest role-id
        # wins. role_id is a total order, so this is reproducible across runs (§3.11).
        return min(top, key=lambda item: item[0].role_id)

    def _triage(
        self,
        request: HumanRequest,
        outcome: RoutingOutcome,
        matched_terms: frozenset[str],
    ) -> RoutingDecision:
        """Build the fail-closed decision routing ``request`` to the single triage role."""
        triage = self._index.triage_capability()
        cause = (
            "no role in the org capably handles this request"
            if outcome is RoutingOutcome.TRIAGED_NO_CAPABLE_ROLE
            else "a capable role exists but the requester lacks the clearance to reach it"
        )
        return RoutingDecision(
            correlation_id=request.correlation_id,
            requester_id=request.requester.requester_id,
            outcome=outcome,
            chosen_role_id=triage.role_id,  # fail-closed: the one triage destination
            chosen_role_title=triage.title,
            matched_terms=matched_terms,
            reason=f"fail-closed to triage {triage.title!r}: {cause}",
            decided_at=self._clock.now(),  # injected clock, never the wall clock
        )
