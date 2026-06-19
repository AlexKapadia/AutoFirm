"""The model-egress seam: a gateway-client Protocol + a deterministic fake double.

What this does
--------------
Abstracts the one impure act of the gateway — actually calling a model — behind a
narrow :class:`ModelGatewayClient` Protocol, so all orchestration logic (selection,
failover, quorum reconciliation) is deterministic and unit-testable without any
network. Two members:

* :class:`ModelGatewayClient` — the Protocol the orchestration layer depends on:
  ``invoke(request, candidate) -> ModelInvocationResponse``. A caller drives the
  call plan (from :mod:`model_selection_policy`) and asks the client for *one named
  candidate* at a time, so failover/quorum is the caller's deterministic loop, not
  hidden inside the client.
* :class:`FakeModelGatewayClient` — a process- and network-free double that returns
  canned per-candidate responses, records every ``(request, candidate)`` it was
  asked for, and can simulate a candidate OUTAGE (so a test exercises failover and
  quorum-with-a-down-member without a real provider).

Why it exists / where it sits
-----------------------------
ADR-003: the single impure seam is this Protocol; the only file touching HTTP is
:mod:`openai_compatible_gateway_client`. Dependency inversion (mirrors the
substrate's :class:`SessionLauncher`) lets the policy/reconciler tests inject the
fake and never start a network call (CLAUDE.md §5.5 no-network-in-unit-tests).

Security / compliance invariants upheld (CLAUDE.md §5.6)
-------------------------------------------------------
* **No network in unit tests (§5.5):** the fake never opens a socket; it serves
  from an injected canned map keyed by :class:`ModelRef`.
* **Outage is data, not an exception path to forget:** a candidate marked down
  raises :class:`CandidateUnavailable`, so a test can prove the caller fails over
  (or fails closed when no candidate answers) deterministically.
* **Candidacy echoed honestly:** the fake's canned responses set ``served_by`` to
  the requested candidate, so a test can detect a client that lies about who served.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from autofirm.modelgateway.model_invocation_contract import (
    ModelInvocationRequest,
    ModelInvocationResponse,
)
from autofirm.modelgateway.model_reference import ModelRef

__all__ = [
    "CandidateUnavailable",
    "FakeModelGatewayClient",
    "ModelGatewayClient",
]


class CandidateUnavailable(RuntimeError):
    """Raised when a specific candidate model could not be reached (outage/failover).

    Distinct from a kill-switch halt: this is a per-candidate failure the caller may
    recover from by failing over to the next candidate; a kill-switch halt is global.
    """


@runtime_checkable
class ModelGatewayClient(Protocol):
    """The narrow boundary the orchestration layer depends on to call one model.

    ``invoke`` calls exactly the named ``candidate`` (which the caller has already
    confirmed is in ``request.model_selector.candidates`` via the selection policy)
    and returns its response, or raises :class:`CandidateUnavailable` on a reachable-
    but-failed candidate. The caller owns the failover/quorum loop.
    """

    def invoke(
        self, request: ModelInvocationRequest, candidate: ModelRef
    ) -> ModelInvocationResponse:
        """Call ``candidate`` for ``request``; raise CandidateUnavailable on outage."""
        ...


class FakeModelGatewayClient:
    """A deterministic, network-free :class:`ModelGatewayClient` for tests.

    Serves canned responses from an injected ``ModelRef -> ModelInvocationResponse``
    map, records every ``(correlation_id, candidate)`` pair it was asked for, and
    treats any candidate in ``down`` as an outage (raising
    :class:`CandidateUnavailable`) so failover and quorum-with-a-down-member are
    exercised without a real provider.
    """

    def __init__(
        self,
        canned: dict[ModelRef, ModelInvocationResponse],
        down: frozenset[ModelRef] = frozenset(),
    ) -> None:
        """Bind canned per-candidate responses and the set of down (outage) candidates."""
        self._canned = dict(canned)
        self._down = frozenset(down)
        self._calls: list[tuple[str, ModelRef]] = []

    def invoke(
        self, request: ModelInvocationRequest, candidate: ModelRef
    ) -> ModelInvocationResponse:
        """Record the call and return the canned response, or simulate an outage."""
        self._calls.append((str(request.correlation_id), candidate))
        # Simulated outage: a reachable-but-failed candidate — the caller must fail
        # over (or fail closed if none answer), never silently produce no result.
        if candidate in self._down:
            raise CandidateUnavailable(f"simulated outage for candidate {candidate!r}")
        if candidate not in self._canned:
            # A test asked for a candidate with no canned answer — surface it loudly
            # rather than return an empty/garbage response.
            raise CandidateUnavailable(f"no canned response for candidate {candidate!r}")
        return self._canned[candidate]

    def calls(self) -> tuple[tuple[str, ModelRef], ...]:
        """Return every (correlation_id, candidate) this fake was asked for (snapshot)."""
        return tuple(self._calls)
