"""Tests for the deterministic FakeModelGatewayClient double (network-free).

Proves the fake records calls, serves canned per-candidate responses, and simulates a
candidate outage so a caller can exercise failover/quorum without a real provider.
"""

from __future__ import annotations

import pytest

from autofirm.costledger.usage_cost_record import TokenUsage
from autofirm.modelgateway.model_egress_client_protocol import (
    CandidateUnavailable,
    FakeModelGatewayClient,
    ModelGatewayClient,
)
from autofirm.modelgateway.model_invocation_contract import (
    Message,
    ModelInvocationResponse,
)
from tests.modelgateway.synthetic_gateway_fixtures import (
    CLAUDE_OPUS,
    FIXED_NOW,
    GPT,
    make_request,
    selector,
)


def _resp(model) -> ModelInvocationResponse:
    from tests.modelgateway.synthetic_gateway_fixtures import CORRELATION

    return ModelInvocationResponse(
        correlation_id=CORRELATION,
        served_by=model,
        output=Message(role="assistant", content="hi", trust_tag="untrusted"),
        usage=TokenUsage(input_tokens=1, output_tokens=1),
        finish_reason="stop",
        served_at=FIXED_NOW,
    )


@pytest.mark.unit
def test_fake_satisfies_the_protocol() -> None:
    assert isinstance(FakeModelGatewayClient({}), ModelGatewayClient)


@pytest.mark.unit
def test_fake_serves_canned_response_and_records_the_call() -> None:
    fake = FakeModelGatewayClient({CLAUDE_OPUS: _resp(CLAUDE_OPUS)})
    req = make_request(selector=selector("pinned", (CLAUDE_OPUS,)))
    out = fake.invoke(req, CLAUDE_OPUS)
    assert out.served_by == CLAUDE_OPUS
    assert fake.calls() == ((str(req.correlation_id), CLAUDE_OPUS),)


@pytest.mark.unit
def test_fake_simulates_outage_for_a_down_candidate() -> None:
    fake = FakeModelGatewayClient(
        {CLAUDE_OPUS: _resp(CLAUDE_OPUS), GPT: _resp(GPT)}, down=frozenset({CLAUDE_OPUS})
    )
    req = make_request(selector=selector("preferred_with_failover", (CLAUDE_OPUS, GPT)))
    with pytest.raises(CandidateUnavailable, match="outage"):
        fake.invoke(req, CLAUDE_OPUS)
    # the next candidate is reachable -> failover succeeds.
    assert fake.invoke(req, GPT).served_by == GPT


@pytest.mark.unit
def test_fake_refuses_a_candidate_with_no_canned_response() -> None:
    fake = FakeModelGatewayClient({CLAUDE_OPUS: _resp(CLAUDE_OPUS)})
    req = make_request(selector=selector("preferred_with_failover", (CLAUDE_OPUS, GPT)))
    with pytest.raises(CandidateUnavailable, match="no canned response"):
        fake.invoke(req, GPT)
