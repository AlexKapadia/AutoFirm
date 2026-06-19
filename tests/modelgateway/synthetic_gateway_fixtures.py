"""Synthetic, deterministic builders + Hypothesis strategies for the gateway tests.

Everything here is process- and network-free: frozen instants, secret-free
credential references, model/selector/request builders, an OpenAI-shaped response
body builder, and Hypothesis strategies over candidate orders, availability subsets,
and caps. NO real provider, NO real secret — the gateway's testability contract.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID

from hypothesis import strategies as st

from autofirm.modelgateway.kill_switch_epoch import KillSwitchEpoch
from autofirm.modelgateway.model_invocation_contract import (
    Message,
    ModelInvocationRequest,
    ModelSelector,
    SelectionStrategy,
)
from autofirm.modelgateway.model_reference import ModelProvider, ModelRef, UseCaseId
from autofirm.org.org_identifiers import RoleId
from autofirm.substrate.scoped_credential_reference import ScopedCredentialReference

FIXED_NOW = datetime(2026, 6, 17, 12, 0, 0, tzinfo=UTC)
CORRELATION = UUID("11111111-1111-1111-1111-111111111111")

# A pool of distinct candidate models (provider + name part of identity).
CLAUDE_OPUS = ModelRef(provider=ModelProvider.ANTHROPIC, model_name="claude-opus")
CLAUDE_HAIKU = ModelRef(provider=ModelProvider.ANTHROPIC, model_name="claude-haiku")
GPT = ModelRef(provider=ModelProvider.OPENAI, model_name="gpt-x")
GEMINI = ModelRef(provider=ModelProvider.GOOGLE, model_name="gemini-y")
LLAMA = ModelRef(provider=ModelProvider.OPENROUTER, model_name="llama-z")
MODEL_POOL = (CLAUDE_OPUS, CLAUDE_HAIKU, GPT, GEMINI, LLAMA)


def make_ref() -> ScopedCredentialReference:
    """A valid, secret-free credential reference (non-expired)."""
    return ScopedCredentialReference(
        component="agent",
        resource="gateway:egress",
        operations=("READ",),
        tenant_id="tenant-1",
        expires_at=FIXED_NOW + timedelta(minutes=30),
    )


def epoch(*, tripped: bool = False, version: int = 1) -> KillSwitchEpoch:
    """A kill-switch epoch (untripped by default)."""
    return KillSwitchEpoch(version=version, tripped=tripped)


def make_request(
    *,
    selector: ModelSelector,
    max_output_tokens: int = 256,
    temperature: Decimal = Decimal("0"),
    kill_switch: KillSwitchEpoch | None = None,
) -> ModelInvocationRequest:
    """Build a valid invocation request around ``selector``."""
    return ModelInvocationRequest(
        correlation_id=CORRELATION,
        requesting_role_id=RoleId("role-1"),
        use_case=UseCaseId("extract"),
        model_selector=selector,
        messages=(Message(role="user", content="hi", trust_tag="untrusted"),),
        max_output_tokens=max_output_tokens,
        temperature=temperature,
        credential_ref=make_ref(),
        kill_switch_token=kill_switch or epoch(),
    )


def selector(
    strategy: SelectionStrategy,
    candidates: tuple[ModelRef, ...],
    *,
    quorum: int | None = None,
) -> ModelSelector:
    """Build a selector (defaults respect each strategy's validation)."""
    return ModelSelector(strategy=strategy, candidates=candidates, quorum=quorum)


def openai_body(  # noqa: PLR0913 -- a response-body builder mirrors the wide OpenAI
    # usage shape (prompt/completion/cached/reasoning); each is an independent knob.
    *,
    model_name: str,
    content: str = "ok",
    prompt_tokens: int = 7,
    completion_tokens: int = 3,
    finish_reason: str = "stop",
    cached_tokens: int | None = None,
    reasoning_tokens: int | None = None,
) -> dict[str, object]:
    """Build a well-formed OpenAI-compatible chat-completion body."""
    usage: dict[str, object] = {
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
    }
    if cached_tokens is not None:
        usage["prompt_tokens_details"] = {"cached_tokens": cached_tokens}
    if reasoning_tokens is not None:
        usage["completion_tokens_details"] = {"reasoning_tokens": reasoning_tokens}
    return {
        "model": model_name,
        "choices": [
            {"message": {"role": "assistant", "content": content}, "finish_reason": finish_reason}
        ],
        "usage": usage,
    }


# --- Hypothesis strategies ---------------------------------------------------

# A non-empty, ordered, DISTINCT tuple of candidate models from the pool.
candidate_tuple_strategy = st.lists(
    st.sampled_from(MODEL_POOL), min_size=1, max_size=len(MODEL_POOL), unique=True
).map(tuple)

# A subset of the pool that is "available" right now (may be empty).
availability_strategy = st.sets(st.sampled_from(MODEL_POOL)).map(frozenset)

# A positive Decimal cost cap, or None for no cap.
cost_cap_strategy = st.one_of(
    st.none(),
    st.decimals(min_value=Decimal("0.01"), max_value=Decimal("100"), places=2),
)
