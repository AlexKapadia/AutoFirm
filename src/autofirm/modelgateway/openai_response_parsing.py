"""PURE parser: an OpenAI-compatible completion body -> ModelInvocationResponse.

What this does
--------------
Parses the JSON body the gateway returns for one chat-completion into a validated
:class:`ModelInvocationResponse`, fail-closed at every field. It is split out from
:mod:`openai_compatible_gateway_client` so the network act and the (untrusted-input)
parsing are separately testable — the parser is PURE (body + request + clock ->
response) and is the fuzz target for malformed/partial provider JSON (CLAUDE.md §3.6).

The two security-critical refusals live here:

* **Verbatim provider usage (W5):** the ``usage`` object is read field-by-field into
  :class:`TokenUsage`; a missing/non-integer/negative bucket is REFUSED, never
  defaulted to a local-tokenizer estimate or silently zeroed.
* **No off-policy served_by:** the model the body claims served MUST resolve to one
  of the request's selector candidates; an un-asked-for model is REFUSED.

Why it exists / where it sits
-----------------------------
The provider response is UNTRUSTED external input (threat-model: external responses
are untrusted by default). Validating it here, at the boundary, means nothing
downstream re-checks it — and the fuzz suite proves a malformed body can never
produce a blank/garbage response.

Security / compliance invariants upheld (CLAUDE.md §5.6)
-------------------------------------------------------
* **Untrusted input validated at the boundary (§5.6):** every accessed field is
  type- and shape-checked; a malformed body raises :class:`GatewayResponseMalformed`.
* **Output is untrusted (C5):** the parsed model output Message is tagged
  ``untrusted`` so a consumer cannot mistake a model's words for trusted control flow.
* **Candidate-bound served_by:** the served model is matched against the request's
  candidates; a non-candidate is refused (the gateway cannot smuggle an off-policy model).
* **Provider usage verbatim:** counts come only from the body's ``usage``; no estimate.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from autofirm.costledger.usage_cost_record import TokenUsage
from autofirm.modelgateway.model_invocation_contract import (
    Message,
    ModelInvocationRequest,
    ModelInvocationResponse,
)
from autofirm.modelgateway.model_reference import ModelRef

__all__ = ["GatewayResponseMalformed", "parse_openai_chat_completion"]

# The closed set of finish reasons the response contract accepts. An OpenAI-style
# body uses these names directly; anything else is mapped to "error" (fail-closed:
# an unknown reason is treated as a non-clean finish, never silently accepted).
_KNOWN_FINISH_REASONS = frozenset(
    {"stop", "length", "tool_use", "content_filter", "error"}
)
# OpenAI emits "tool_calls" for tool stops; normalise it to our closed-set name.
_FINISH_REASON_ALIASES = {"tool_calls": "tool_use", "function_call": "tool_use"}


class GatewayResponseMalformed(RuntimeError):
    """Raised when the provider body is missing/ill-typed in a security-relevant field.

    A malformed body is REFUSED (never coerced into a blank output or a zeroed usage),
    so a corrupt/partial provider response can never be mistaken for a valid result.
    """


def _require_mapping(value: Any, field: str) -> dict[str, Any]:
    """Return ``value`` as a dict or raise — a non-object where an object is required."""
    if not isinstance(value, dict):
        raise GatewayResponseMalformed(f"{field} must be a JSON object")
    return value


def _require_non_negative_int(value: Any, field: str) -> int:
    """Return ``value`` as a non-negative int or raise (verbatim provider usage)."""
    # bool is an int subclass; a JSON true/false is NOT a token count — refuse it.
    if isinstance(value, bool) or not isinstance(value, int):
        raise GatewayResponseMalformed(f"{field} must be an integer token count")
    if value < 0:
        raise GatewayResponseMalformed(f"{field} must be >= 0")
    return value


def _parse_usage(payload: dict[str, Any]) -> TokenUsage:
    """Parse the body's ``usage`` object VERBATIM into TokenUsage (no local estimate).

    OpenAI-style names map to the ledger's buckets: ``prompt_tokens`` -> input,
    ``completion_tokens`` -> output. Cache/reasoning sub-counts (when present) are
    read from the nested ``*_tokens_details`` blocks; absent => 0 (the contract default).
    Required buckets are mandatory; a missing/ill-typed count is refused.
    """
    usage = _require_mapping(payload.get("usage"), "usage")
    # Required: a response with no input/output token counts is unusable for the cost
    # ledger — refuse rather than substitute a guessed count (fail-closed, W5).
    if "prompt_tokens" not in usage or "completion_tokens" not in usage:
        raise GatewayResponseMalformed("usage must carry prompt_tokens and completion_tokens")
    input_tokens = _require_non_negative_int(usage["prompt_tokens"], "usage.prompt_tokens")
    output_tokens = _require_non_negative_int(
        usage["completion_tokens"], "usage.completion_tokens"
    )
    prompt_details = usage.get("prompt_tokens_details") or {}
    completion_details = usage.get("completion_tokens_details") or {}
    prompt_details = _require_mapping(prompt_details, "usage.prompt_tokens_details")
    completion_details = _require_mapping(completion_details, "usage.completion_tokens_details")
    cache_read = _require_non_negative_int(
        prompt_details.get("cached_tokens", 0), "usage.prompt_tokens_details.cached_tokens"
    )
    reasoning = _require_non_negative_int(
        completion_details.get("reasoning_tokens", 0),
        "usage.completion_tokens_details.reasoning_tokens",
    )
    cache_write = _require_non_negative_int(
        usage.get("cache_creation_input_tokens", 0), "usage.cache_creation_input_tokens"
    )
    return TokenUsage(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cache_read_tokens=cache_read,
        cache_write_tokens=cache_write,
        reasoning_tokens=reasoning,
    )


def _resolve_served_candidate(
    served_model_name: str, request: ModelInvocationRequest
) -> ModelRef:
    """Map the body's model string back to one of the request's candidates, or refuse.

    A response may report the model as a bare name or as ``provider/name``; either way
    it MUST resolve to a request candidate. A model not among the candidates is refused
    (the gateway cannot smuggle an off-policy model into a response — C5/policy guard).
    """
    name = served_model_name.strip()
    for candidate in request.model_selector.candidates:
        # Match on the bare model name OR the namespaced provider/name form.
        if name == candidate.model_name:
            return candidate
        if name == f"{candidate.provider.value}/{candidate.model_name}":
            return candidate
    raise GatewayResponseMalformed(
        f"served_by model {served_model_name!r} is not one of the request candidates"
    )


def _parse_finish_reason(value: Any) -> str:
    """Map the body's finish reason to the closed contract set (unknown -> error)."""
    if not isinstance(value, str):
        # fail-closed: a missing/ill-typed reason is treated as a non-clean finish.
        return "error"
    reason = _FINISH_REASON_ALIASES.get(value, value)
    return reason if reason in _KNOWN_FINISH_REASONS else "error"


def parse_openai_chat_completion(
    *,
    payload: dict[str, Any],
    request: ModelInvocationRequest,
    served_at: datetime,
) -> ModelInvocationResponse:
    """Parse an OpenAI-compatible completion body into a validated response (fail-closed).

    Args:
        payload: the provider's JSON body (UNTRUSTED external input).
        request: the originating request (for correlation id + candidate matching).
        served_at: the injected clock instant to stamp on the response.

    Returns:
        A :class:`ModelInvocationResponse` with verbatim provider usage and a
        candidate-bound ``served_by``; the output message is tagged ``untrusted``.

    Raises:
        GatewayResponseMalformed: any missing/ill-typed security-relevant field — the
            usage object, the served model, or the choices/message content.
    """
    if not isinstance(payload, dict):
        raise GatewayResponseMalformed("response body must be a JSON object")

    served_model_name = payload.get("model")
    if not isinstance(served_model_name, str) or not served_model_name.strip():
        raise GatewayResponseMalformed("response is missing the served model name")
    served_by = _resolve_served_candidate(served_model_name, request)

    choices = payload.get("choices")
    if not isinstance(choices, list) or not choices:
        raise GatewayResponseMalformed("response must carry a non-empty choices array")
    first_choice = _require_mapping(choices[0], "choices[0]")
    message = _require_mapping(first_choice.get("message"), "choices[0].message")
    content = message.get("content")
    if not isinstance(content, str):
        # fail-closed: a non-string content (None / object) is not a usable reply —
        # refuse rather than render a blank/garbage output message.
        raise GatewayResponseMalformed("choices[0].message.content must be a string")

    usage = _parse_usage(payload)
    finish_reason = _parse_finish_reason(first_choice.get("finish_reason"))

    return ModelInvocationResponse(
        correlation_id=request.correlation_id,  # echo exactly; bound to the request
        served_by=served_by,
        # C5: a model's output is UNTRUSTED by default — never auto-promoted to trusted.
        output=Message(role="assistant", content=content, trust_tag="untrusted"),
        usage=usage,
        finish_reason=finish_reason,  # type: ignore[arg-type]  # narrowed to the closed set above
        served_at=served_at,
    )
