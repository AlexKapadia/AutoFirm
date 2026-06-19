"""The ONLY HTTP file: an OpenAI-compatible gateway client (verbatim provider usage).

What this does
--------------
Implements :class:`ModelGatewayClient` against a self-hosted, OpenAI-compatible
model-egress gateway (LiteLLM-style; ADR-003). For one ``(request, candidate)`` it:

1. refuses fail-closed if the kill-switch epoch is tripped (C7) — before any egress;
2. resolves the per-session virtual key at point-of-use from an injected resolver
   (reuse of the access-layer credential broker / secret source pattern) — never
   stored on the client, never logged, never placed in a URL;
3. POSTs an OpenAI-shaped chat-completion to the gateway through an injected HTTP
   transport seam (so unit tests mock HTTP and never open a socket);
4. parses the response, taking the provider's ``usage`` object VERBATIM into
   :class:`TokenUsage` (NO local tokenizer — provider usage is ground truth, W5);
5. refuses fail-closed if the model that served is NOT one of the request's
   candidates (a gateway that served an off-policy model is rejected, not trusted).

A reachable-but-failed candidate (non-2xx / transport error) raises
:class:`CandidateUnavailable` so the caller's failover/quorum loop can proceed
deterministically.

Why it exists / where it sits
-----------------------------
ADR-003: this is the single file that touches the network; everything else in the
gateway is pure or a Protocol. The HTTP act is behind the injected
:class:`HttpTransport` seam (dependency inversion, mirrors the substrate launcher),
so unit tests inject a fake transport and stay network-free (CLAUDE.md §5.5).

Security / compliance invariants upheld (CLAUDE.md §5.6)
-------------------------------------------------------
* **Kill-switch fail-closed (C7):** a tripped epoch refuses egress before any call.
* **Secret at point-of-use only:** the virtual key is resolved per call and passed
  in an Authorization header to the transport; it is never stored, logged, or URL-ed.
  A missing key is a refusal (fail-closed), never a blank-auth call.
* **Provider usage is ground truth (W5):** ``usage`` is parsed verbatim; a malformed
  or absent usage object is refused, never replaced by a local estimate.
* **No off-policy served_by:** a response whose model is not a request candidate is
  refused — the gateway can never substitute an un-asked-for model silently.
* **Correlation integrity:** the response is stamped with the request's correlation id.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Protocol, runtime_checkable

from autofirm.modelgateway.model_egress_client_protocol import CandidateUnavailable
from autofirm.modelgateway.model_invocation_contract import (
    ModelInvocationRequest,
    ModelInvocationResponse,
)
from autofirm.modelgateway.model_reference import ModelProvider, ModelRef
from autofirm.modelgateway.openai_response_parsing import (
    GatewayResponseMalformed,
    parse_openai_chat_completion,
)

__all__ = [
    "GatewayConfigError",
    "HttpResponse",
    "HttpTransport",
    "OpenAiCompatibleGatewayClient",
    "VirtualKeyResolver",
]

# The 2xx success band: a status in [200, 300) is a successful completion; anything
# else is a reachable-but-failed candidate the caller should fail over from.
_HTTP_OK_MIN = 200
_HTTP_OK_MAX_EXCLUSIVE = 300


class GatewayConfigError(RuntimeError):
    """Raised when the gateway cannot be called for a config/secret reason (fail-closed).

    A missing virtual key or an empty gateway URL is refused here rather than sent as
    a blank-auth / no-host call — an ambiguous config is a refusal, not a best-effort.
    """


@runtime_checkable
class HttpResponse(Protocol):
    """The minimal HTTP response shape the client reads (status + parsed JSON body)."""

    @property
    def status_code(self) -> int:
        """The HTTP status code (2xx => success; anything else => candidate outage)."""
        ...

    def json(self) -> dict[str, Any]:
        """Return the parsed JSON body (the OpenAI-compatible completion envelope)."""
        ...


@runtime_checkable
class HttpTransport(Protocol):
    """The injected HTTP seam — the ONE place a real socket is opened (production).

    A test injects a fake transport returning canned :class:`HttpResponse` objects,
    so the client is exercised with mocked HTTP only (no network, CLAUDE.md §5.5).
    """

    def post_json(
        self, url: str, *, headers: dict[str, str], body: dict[str, Any]
    ) -> HttpResponse:
        """POST ``body`` as JSON to ``url`` with ``headers``; return the response."""
        ...


@runtime_checkable
class VirtualKeyResolver(Protocol):
    """Resolves the per-session virtual key AT POINT OF USE (reuse of the broker).

    Mirrors the substrate launcher's ``SecretResolver``: returns the raw key string
    for the request's credential reference, or ``None`` if none is available (the
    client then fails closed). The key is never stored on the client.
    """

    def resolve_virtual_key(self, request: ModelInvocationRequest) -> str | None:
        """Return the per-session virtual key for ``request``, or ``None`` if absent."""
        ...


class OpenAiCompatibleGatewayClient:
    """A :class:`ModelGatewayClient` over an OpenAI-compatible self-hosted gateway.

    Constructed with its three seams — the gateway base URL, an injected
    :class:`HttpTransport` (the only socket), an injected :class:`VirtualKeyResolver`
    (point-of-use key), and an injected clock — so it holds no ambient state and is
    fully deterministic under test with mocked HTTP.
    """

    def __init__(
        self,
        gateway_base_url: str,
        transport: HttpTransport,
        key_resolver: VirtualKeyResolver,
        clock_now: object,
    ) -> None:
        """Bind the client to its base URL, HTTP transport, key resolver, and clock.

        ``clock_now`` is a zero-arg callable returning a timezone-aware ``datetime``
        (the injected ``Clock.now``), so ``served_at`` is deterministic, never wall-clock.
        """
        # fail-closed: an empty gateway URL is an un-callable config — refuse early.
        if not gateway_base_url or not gateway_base_url.strip():
            raise GatewayConfigError("gateway_base_url must be non-empty")
        self._base_url = gateway_base_url.rstrip("/")
        self._transport = transport
        self._key_resolver = key_resolver
        self._clock_now = clock_now

    def invoke(
        self, request: ModelInvocationRequest, candidate: ModelRef
    ) -> ModelInvocationResponse:
        """Call ``candidate`` via the gateway; fail closed / fail over per the rules."""
        # fail-closed FIRST (C7): never egress while the kill-switch is engaged.
        request.kill_switch_token.require_egress_permitted()

        # secret at point-of-use: resolve the per-session virtual key now; a missing
        # key is a refusal, never a blank-auth call (mirrors the launcher).
        virtual_key = self._key_resolver.resolve_virtual_key(request)
        if not virtual_key:
            raise GatewayConfigError(
                "no per-session virtual key available; refusing to call the gateway"
            )

        url = f"{self._base_url}/chat/completions"
        # secrets-never-logged / never-in-URL: the key goes ONLY in the Authorization
        # header passed to the transport; it is never placed in the URL or any log here.
        headers = {
            "Authorization": f"Bearer {virtual_key}",
            "Content-Type": "application/json",
        }
        body = _build_chat_completion_body(request, candidate)

        try:
            http_response = self._transport.post_json(url, headers=headers, body=body)
        except Exception as exc:  # transport-level failure => candidate outage, fail over
            raise CandidateUnavailable(
                f"transport error calling candidate {candidate!r}"
            ) from exc

        # A non-2xx is a reachable-but-failed candidate: raise so the caller fails over
        # (it is NOT a malformed-response refusal — the gateway answered, just not OK).
        if (
            http_response.status_code < _HTTP_OK_MIN
            or http_response.status_code >= _HTTP_OK_MAX_EXCLUSIVE
        ):
            raise CandidateUnavailable(
                f"gateway returned status {http_response.status_code} for {candidate!r}"
            )

        served_at = self._now()
        try:
            return parse_openai_chat_completion(
                payload=http_response.json(),
                request=request,
                served_at=served_at,
            )
        except GatewayResponseMalformed:
            # fail-closed: a malformed/partial body is refused, never coerced into a
            # blank/garbage usage or an off-policy served_by — re-raise unchanged.
            raise

    def _now(self) -> datetime:
        """Return the injected clock's current instant (deterministic-testable)."""
        now = self._clock_now()  # type: ignore[operator]
        if not isinstance(now, datetime):
            raise GatewayConfigError("injected clock did not return a datetime")
        return now


def _build_chat_completion_body(
    request: ModelInvocationRequest, candidate: ModelRef
) -> dict[str, Any]:
    """Build the OpenAI-compatible request body for ``candidate`` (pure, no I/O).

    The gateway routes by the ``model`` field; ``candidate`` is always one of the
    request's selector candidates (the caller guarantees this via the call plan).
    Temperature/max-tokens carry the request's bounded, deterministic settings.
    """
    return {
        "model": _gateway_model_name(candidate),
        "messages": [
            {"role": message.role, "content": message.content}
            for message in request.messages
        ],
        "max_tokens": request.max_output_tokens,
        "temperature": float(request.temperature),
    }


def _gateway_model_name(candidate: ModelRef) -> str:
    """Return the gateway routing name for ``candidate`` (provider/model, OpenAI-style).

    The self-hosted gateway namespaces models by provider (e.g. ``anthropic/claude``,
    ``openai/gpt``), so the routing name is ``<provider>/<model_name>`` — Anthropic
    gets the same treatment as any provider on the programmatic lane.
    """
    if candidate.provider == ModelProvider.OPENAI:
        # OpenAI is the gateway's native namespace; pass the bare model name through.
        return candidate.model_name
    return f"{candidate.provider.value}/{candidate.model_name}"
