"""Fuzz + fail-closed tests for the provider-response parser (untrusted input).

The provider body is UNTRUSTED external input. These tests fuzz it with malformed and
partial JSON and assert the parser ALWAYS either returns a fully-valid response or
raises GatewayResponseMalformed — it never emits a blank/garbage usage and never accepts
an off-policy served_by. Kills mutants on every field guard.
"""

from __future__ import annotations

from typing import Any

import pytest
from hypothesis import given
from hypothesis import strategies as st

from autofirm.modelgateway.openai_response_parsing import (
    GatewayResponseMalformed,
    parse_openai_chat_completion,
)
from tests.modelgateway.synthetic_gateway_fixtures import (
    CLAUDE_OPUS,
    FIXED_NOW,
    make_request,
    openai_body,
    selector,
)

_REQ = make_request(selector=selector("pinned", (CLAUDE_OPUS,)))


def _parse(body: Any):
    return parse_openai_chat_completion(payload=body, request=_REQ, served_at=FIXED_NOW)


@pytest.mark.unit
def test_well_formed_body_parses() -> None:
    out = _parse(openai_body(model_name="claude-opus", prompt_tokens=2, completion_tokens=1))
    assert out.usage.input_tokens == 2
    assert out.usage.output_tokens == 1
    assert out.served_by == CLAUDE_OPUS


@pytest.mark.unit
@pytest.mark.parametrize(
    "mutate",
    [
        lambda b: {k: v for k, v in b.items() if k != "usage"},  # no usage
        lambda b: {**b, "usage": {"completion_tokens": 1}},  # missing prompt_tokens
        lambda b: {**b, "usage": {"prompt_tokens": 1}},  # missing completion_tokens
        lambda b: {**b, "usage": {"prompt_tokens": -1, "completion_tokens": 1}},  # negative
        lambda b: {**b, "usage": {"prompt_tokens": True, "completion_tokens": 1}},  # bool
        lambda b: {**b, "usage": "not-an-object"},  # usage not a dict
        lambda b: {k: v for k, v in b.items() if k != "model"},  # no model
        lambda b: {**b, "model": ""},  # blank model
        lambda b: {**b, "model": "off-policy-model"},  # off-policy served_by
        lambda b: {k: v for k, v in b.items() if k != "choices"},  # no choices
        lambda b: {**b, "choices": []},  # empty choices
        lambda b: {**b, "choices": [{"message": {"content": None}}]},  # null content
        lambda b: {**b, "choices": [{"message": {"role": "assistant"}}]},  # no content key
        lambda b: {**b, "choices": [{"finish_reason": "stop"}]},  # no message
    ],
)
def test_malformed_bodies_are_refused_fail_closed(mutate) -> None:
    body = mutate(openai_body(model_name="claude-opus"))
    with pytest.raises(GatewayResponseMalformed):
        _parse(body)


@pytest.mark.unit
def test_unknown_finish_reason_maps_to_error_not_a_crash() -> None:
    body = openai_body(model_name="claude-opus", finish_reason="banana")
    assert _parse(body).finish_reason == "error"  # closed-set, fail-closed mapping


@pytest.mark.unit
def test_tool_calls_finish_reason_alias_is_normalised() -> None:
    body = openai_body(model_name="claude-opus", finish_reason="tool_calls")
    assert _parse(body).finish_reason == "tool_use"


@pytest.mark.unit
@pytest.mark.parametrize("bad_reason", [None, 7, 1.5, True, ["stop"], {"r": "stop"}])
def test_non_string_finish_reason_maps_to_error_fail_closed(bad_reason: Any) -> None:
    # A provider that sends a non-string finish_reason (null / number / list / object)
    # must be coerced to the closed-set "error", never crash and never silently treated
    # as a clean "stop". This drives the non-str branch directly (distinct from the
    # string-but-unknown "banana" path) and kills any mutant on the isinstance guard.
    body = openai_body(model_name="claude-opus")
    body["choices"] = [{"message": {"content": "ok"}, "finish_reason": bad_reason}]
    assert _parse(body).finish_reason == "error"  # fail-closed: non-clean finish


@pytest.mark.property
@given(
    payload=st.recursive(
        st.none()
        | st.booleans()
        | st.integers()
        | st.text(max_size=8)
        | st.floats(allow_nan=False, allow_infinity=False),
        lambda children: st.lists(children, max_size=4)
        | st.dictionaries(st.text(max_size=6), children, max_size=4),
        max_leaves=12,
    )
)
def test_fuzz_arbitrary_json_never_returns_garbage(payload: Any) -> None:
    # For ANY arbitrary JSON-ish payload the parser either returns a valid response or
    # raises GatewayResponseMalformed — never a half-built / blank response.
    try:
        result = parse_openai_chat_completion(
            payload=payload, request=_REQ, served_at=FIXED_NOW
        )
    except GatewayResponseMalformed:
        return
    # If it DID parse, every security-relevant field is well-formed and on-policy.
    assert result.served_by in _REQ.model_selector.candidates  # never off-policy
    assert result.usage.input_tokens >= 0 and result.usage.output_tokens >= 0
    assert result.output.trust_tag == "untrusted"
    assert result.correlation_id == _REQ.correlation_id


@pytest.mark.property
@given(prompt=st.integers(min_value=0, max_value=10_000), completion=st.integers(0, 10_000))
def test_fuzz_valid_usage_counts_echoed_exactly(prompt: int, completion: int) -> None:
    body = openai_body(
        model_name="claude-opus", prompt_tokens=prompt, completion_tokens=completion
    )
    out = _parse(body)
    # provider usage is ground truth: echoed verbatim, never re-estimated.
    assert out.usage.input_tokens == prompt
    assert out.usage.output_tokens == completion
