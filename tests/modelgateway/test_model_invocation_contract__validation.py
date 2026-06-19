"""Fail-closed validation tests for the §7 request/response/selector/message shapes.

Designed to kill mutants on every validator: the selector strategy-shape rules
(pinned==1, quorum required-iff-quorum, quorum<=len), the message trust tag, the
bounded output budget, the temperature range, and the non-empty role/use-case/messages.
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from pydantic import ValidationError

from autofirm.costledger.usage_cost_record import TokenUsage
from autofirm.modelgateway.model_invocation_contract import (
    Message,
    ModelInvocationRequest,
    ModelInvocationResponse,
    ModelSelector,
)
from autofirm.modelgateway.model_reference import UseCaseId
from autofirm.org.org_identifiers import RoleId
from tests.modelgateway.synthetic_gateway_fixtures import (
    CLAUDE_HAIKU,
    CLAUDE_OPUS,
    CORRELATION,
    FIXED_NOW,
    GPT,
    epoch,
    make_ref,
    make_request,
    selector,
)

# ------------------------------- Message ------------------------------------ #


@pytest.mark.unit
def test_message_is_frozen_and_trust_tagged() -> None:
    msg = Message(role="user", content="x", trust_tag="untrusted")
    with pytest.raises(ValidationError):
        msg.content = "y"  # type: ignore[misc]


@pytest.mark.unit
def test_message_refuses_unknown_role_and_trust_tag() -> None:
    with pytest.raises(ValidationError):
        Message(role="root", content="x", trust_tag="untrusted")  # type: ignore[arg-type]
    with pytest.raises(ValidationError):
        Message(role="user", content="x", trust_tag="maybe")  # type: ignore[arg-type]


@pytest.mark.unit
def test_message_allows_empty_string_but_not_none_content() -> None:
    assert Message(role="user", content="", trust_tag="trusted").content == ""
    with pytest.raises(ValidationError):
        Message(role="user", content=None, trust_tag="trusted")  # type: ignore[arg-type]


# ------------------------------ ModelSelector ------------------------------- #


@pytest.mark.unit
def test_selector_refuses_empty_candidates() -> None:
    with pytest.raises(ValidationError, match="at least one candidate"):
        ModelSelector(strategy="preferred_with_failover", candidates=())


@pytest.mark.unit
def test_pinned_requires_exactly_one_candidate() -> None:
    assert selector("pinned", (CLAUDE_OPUS,)).candidates == (CLAUDE_OPUS,)
    with pytest.raises(ValidationError, match="exactly one candidate"):
        selector("pinned", (CLAUDE_OPUS, CLAUDE_HAIKU))


@pytest.mark.unit
def test_quorum_required_only_for_ensemble_quorum() -> None:
    # quorum strategy with no quorum -> refuse
    with pytest.raises(ValidationError, match="requires a quorum"):
        selector("ensemble_quorum", (CLAUDE_OPUS, GPT))
    # quorum on a non-quorum strategy -> refuse
    with pytest.raises(ValidationError, match="only valid for the ensemble_quorum"):
        selector("preferred_with_failover", (CLAUDE_OPUS, GPT), quorum=2)


@pytest.mark.unit
def test_quorum_must_not_exceed_candidate_count() -> None:
    with pytest.raises(ValidationError, match="quorum must be <="):
        selector("ensemble_quorum", (CLAUDE_OPUS, GPT), quorum=3)
    # boundary: quorum == len(candidates) is allowed
    assert selector("ensemble_quorum", (CLAUDE_OPUS, GPT), quorum=2).quorum == 2


@pytest.mark.unit
def test_quorum_must_be_positive() -> None:
    with pytest.raises(ValidationError):
        selector("ensemble_quorum", (CLAUDE_OPUS, GPT), quorum=0)


# -------------------------- ModelInvocationRequest -------------------------- #


@pytest.mark.unit
def test_request_refuses_zero_or_negative_output_budget() -> None:
    with pytest.raises(ValidationError):
        make_request(selector=selector("pinned", (CLAUDE_OPUS,)), max_output_tokens=0)
    with pytest.raises(ValidationError):
        make_request(selector=selector("pinned", (CLAUDE_OPUS,)), max_output_tokens=-1)


@pytest.mark.unit
def test_request_temperature_defaults_to_zero_and_is_range_checked() -> None:
    req = make_request(selector=selector("pinned", (CLAUDE_OPUS,)))
    assert req.temperature == Decimal("0")  # deterministic default
    with pytest.raises(ValidationError, match=r"\[0, 2\]"):
        make_request(selector=selector("pinned", (CLAUDE_OPUS,)), temperature=Decimal("2.01"))
    with pytest.raises(ValidationError, match=r"\[0, 2\]"):
        make_request(selector=selector("pinned", (CLAUDE_OPUS,)), temperature=Decimal("-0.01"))
    # boundaries 0 and 2 are accepted
    make_request(selector=selector("pinned", (CLAUDE_OPUS,)), temperature=Decimal("0"))
    make_request(selector=selector("pinned", (CLAUDE_OPUS,)), temperature=Decimal("2"))


@pytest.mark.unit
def test_request_refuses_empty_role_use_case_and_messages() -> None:
    base = {
        "correlation_id": CORRELATION,
        "model_selector": selector("pinned", (CLAUDE_OPUS,)),
        "max_output_tokens": 8,
        "credential_ref": make_ref(),
        "kill_switch_token": epoch(),
    }
    with pytest.raises(ValidationError, match="requesting_role_id"):
        ModelInvocationRequest(
            requesting_role_id=RoleId("  "),
            use_case=UseCaseId("extract"),
            messages=(Message(role="user", content="x", trust_tag="untrusted"),),
            **base,
        )
    with pytest.raises(ValidationError, match="use_case must be non-empty"):
        ModelInvocationRequest(
            requesting_role_id=RoleId("r"),
            use_case=UseCaseId("   "),
            messages=(Message(role="user", content="x", trust_tag="untrusted"),),
            **base,
        )
    with pytest.raises(ValidationError, match="at least one message"):
        ModelInvocationRequest(
            requesting_role_id=RoleId("r"),
            use_case=UseCaseId("extract"),
            messages=(),
            **base,
        )


@pytest.mark.unit
def test_request_is_frozen_and_carries_secret_free_credential() -> None:
    req = make_request(selector=selector("pinned", (CLAUDE_OPUS,)))
    with pytest.raises(ValidationError):
        req.max_output_tokens = 9  # type: ignore[misc]
    # the credential ref is structurally secret-free (no field can hold a secret).
    assert "secret" not in req.credential_ref.model_dump_json().lower()


# -------------------------- ModelInvocationResponse ------------------------- #


@pytest.mark.unit
def test_response_refuses_unknown_finish_reason() -> None:
    with pytest.raises(ValidationError):
        ModelInvocationResponse(
            correlation_id=CORRELATION,
            served_by=CLAUDE_OPUS,
            output=Message(role="assistant", content="x", trust_tag="untrusted"),
            usage=TokenUsage(input_tokens=1, output_tokens=1),
            finish_reason="exploded",  # type: ignore[arg-type]
            served_at=FIXED_NOW,
        )
