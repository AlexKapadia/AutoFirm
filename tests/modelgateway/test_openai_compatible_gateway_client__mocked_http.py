"""Mocked-HTTP tests for the OpenAI-compatible gateway client (NO network).

Proves: kill-switch refuses before egress; a missing virtual key is refused; the secret
never appears in the URL; a non-2xx / transport error becomes CandidateUnavailable (so
the caller fails over); provider usage is parsed verbatim; an off-policy served_by is
refused. A fake transport stands in for the socket — the only network seam.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import pytest

from autofirm.modelgateway.model_egress_client_protocol import CandidateUnavailable
from autofirm.modelgateway.openai_compatible_gateway_client import (
    GatewayConfigError,
    OpenAiCompatibleGatewayClient,
)
from autofirm.modelgateway.openai_response_parsing import GatewayResponseMalformed
from tests.modelgateway.synthetic_gateway_fixtures import (
    CLAUDE_OPUS,
    FIXED_NOW,
    epoch,
    make_request,
    openai_body,
    selector,
)

_URL = "http://localhost:18080/v1"
_KEY = "VIRTUAL-KEY-abc"


class _FakeResponse:
    def __init__(self, status_code: int, body: dict[str, Any]) -> None:
        self.status_code = status_code
        self._body = body

    def json(self) -> dict[str, Any]:
        return self._body


class _RecordingTransport:
    """Records the URL/headers/body and returns a canned response (or raises)."""

    def __init__(self, response: _FakeResponse | None = None, *, boom: bool = False) -> None:
        self._response = response
        self._boom = boom
        self.calls: list[dict[str, Any]] = []

    def post_json(
        self, url: str, *, headers: dict[str, str], body: dict[str, Any]
    ) -> _FakeResponse:
        self.calls.append({"url": url, "headers": headers, "body": body})
        if self._boom:
            raise ConnectionError("simulated transport failure")
        assert self._response is not None
        return self._response


class _KeyResolver:
    def __init__(self, key: str | None) -> None:
        self._key = key

    def resolve_virtual_key(self, request: object) -> str | None:
        return self._key


def _clock() -> datetime:
    return FIXED_NOW


def _client(
    transport: _RecordingTransport, key: str | None = _KEY
) -> OpenAiCompatibleGatewayClient:
    return OpenAiCompatibleGatewayClient(_URL, transport, _KeyResolver(key), _clock)


@pytest.mark.unit
@pytest.mark.security
def test_kill_switch_refuses_before_any_transport_call() -> None:
    transport = _RecordingTransport(_FakeResponse(200, openai_body(model_name="claude-opus")))
    client = _client(transport)
    req = make_request(
        selector=selector("pinned", (CLAUDE_OPUS,)), kill_switch=epoch(tripped=True)
    )
    from autofirm.modelgateway.kill_switch_epoch import KillSwitchEngaged

    with pytest.raises(KillSwitchEngaged):
        client.invoke(req, CLAUDE_OPUS)
    assert transport.calls == []  # never egressed


@pytest.mark.unit
@pytest.mark.security
def test_missing_virtual_key_is_refused_fail_closed() -> None:
    transport = _RecordingTransport(_FakeResponse(200, openai_body(model_name="claude-opus")))
    client = _client(transport, key=None)
    req = make_request(selector=selector("pinned", (CLAUDE_OPUS,)))
    with pytest.raises(GatewayConfigError, match="virtual key"):
        client.invoke(req, CLAUDE_OPUS)
    assert transport.calls == []  # never sent a blank-auth call


@pytest.mark.unit
@pytest.mark.security
def test_secret_goes_in_auth_header_only_never_in_url() -> None:
    transport = _RecordingTransport(_FakeResponse(200, openai_body(model_name="claude-opus")))
    client = _client(transport)
    req = make_request(selector=selector("pinned", (CLAUDE_OPUS,)))
    client.invoke(req, CLAUDE_OPUS)
    call = transport.calls[0]
    assert _KEY not in call["url"]  # never in the URL
    assert call["headers"]["Authorization"] == f"Bearer {_KEY}"


@pytest.mark.unit
def test_provider_usage_is_parsed_verbatim() -> None:
    body = openai_body(
        model_name="claude-opus",
        prompt_tokens=123,
        completion_tokens=45,
        cached_tokens=10,
        reasoning_tokens=5,
    )
    transport = _RecordingTransport(_FakeResponse(200, body))
    out = _client(transport).invoke(
        make_request(selector=selector("pinned", (CLAUDE_OPUS,))), CLAUDE_OPUS
    )
    assert out.usage.input_tokens == 123
    assert out.usage.output_tokens == 45
    assert out.usage.cache_read_tokens == 10
    assert out.usage.reasoning_tokens == 5
    assert out.served_by == CLAUDE_OPUS
    assert out.output.trust_tag == "untrusted"  # model output is untrusted by default
    assert out.served_at == FIXED_NOW  # injected clock


@pytest.mark.unit
def test_non_2xx_becomes_candidate_unavailable_for_failover() -> None:
    transport = _RecordingTransport(_FakeResponse(503, {}))
    with pytest.raises(CandidateUnavailable, match="status 503"):
        _client(transport).invoke(
            make_request(selector=selector("pinned", (CLAUDE_OPUS,))), CLAUDE_OPUS
        )


@pytest.mark.unit
def test_transport_error_becomes_candidate_unavailable() -> None:
    transport = _RecordingTransport(boom=True)
    with pytest.raises(CandidateUnavailable, match="transport error"):
        _client(transport).invoke(
            make_request(selector=selector("pinned", (CLAUDE_OPUS,))), CLAUDE_OPUS
        )


@pytest.mark.unit
@pytest.mark.security
def test_off_policy_served_by_is_refused() -> None:
    # The gateway claims it served a model that is NOT a request candidate -> refuse.
    body = openai_body(model_name="some-other-model")
    transport = _RecordingTransport(_FakeResponse(200, body))
    with pytest.raises(GatewayResponseMalformed, match="not one of the request candidates"):
        _client(transport).invoke(
            make_request(selector=selector("pinned", (CLAUDE_OPUS,))), CLAUDE_OPUS
        )


@pytest.mark.unit
def test_request_body_routes_by_namespaced_provider_model() -> None:
    # A non-OpenAI provider is namespaced provider/model in the gateway routing name.
    body = openai_body(model_name="openrouter/llama-z")
    transport = _RecordingTransport(_FakeResponse(200, body))
    from tests.modelgateway.synthetic_gateway_fixtures import LLAMA

    _client(transport).invoke(
        make_request(selector=selector("pinned", (LLAMA,))), LLAMA
    )
    assert transport.calls[0]["body"]["model"] == "openrouter/llama-z"


@pytest.mark.unit
def test_openai_provider_routes_by_bare_model_name_not_namespaced() -> None:
    # OpenAI is the gateway's native namespace, so its routing name is the BARE model
    # name (no "openai/" prefix) — the distinct branch from the namespaced one above.
    # A mutant that namespaces OpenAI too would put "openai/gpt-x" on the wire and fail.
    from tests.modelgateway.synthetic_gateway_fixtures import GPT

    body = openai_body(model_name="gpt-x")
    transport = _RecordingTransport(_FakeResponse(200, body))
    _client(transport).invoke(make_request(selector=selector("pinned", (GPT,))), GPT)
    assert transport.calls[0]["body"]["model"] == "gpt-x"  # bare, never "openai/gpt-x"


@pytest.mark.unit
def test_empty_gateway_url_refused_at_construction() -> None:
    with pytest.raises(GatewayConfigError, match="gateway_base_url"):
        OpenAiCompatibleGatewayClient("  ", _RecordingTransport(), _KeyResolver(_KEY), _clock)
