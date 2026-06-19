"""ADR-003 linchpin tests: the CLI gateway env builder is Anthropic-ONLY, fail-closed.

Mutation-CRITICAL: a mutant that lets a non-Anthropic CLI model through, drops the
discovery flag, or mis-names a var must be KILLED. Also a fuzz over model names proves
no non-Anthropic name is ever accepted.
"""

from __future__ import annotations

import pytest
from hypothesis import given
from hypothesis import strategies as st

from autofirm.modelgateway.cli_gateway_env_injection import (
    ANTHROPIC_AUTH_TOKEN_ENV,
    ANTHROPIC_BASE_URL_ENV,
    GATEWAY_MODEL_DISCOVERY_ENV,
    NonAnthropicModelRefused,
    build_cli_gateway_env,
    is_anthropic_eligible,
)
from autofirm.modelgateway.model_reference import ModelProvider, ModelRef

_URL = "http://localhost:18080/v1"
_TOKEN_PLACEHOLDER = "PLACEHOLDER-AUTH-TOKEN"


def _model(provider: ModelProvider, name: str) -> ModelRef:
    return ModelRef(provider=provider, model_name=name)


@pytest.mark.unit
def test_env_var_names_are_the_exact_gate1_verified_strings() -> None:
    # Pin the EXACT env-var NAME strings the CLI honours (Gate-1). Asserting the
    # literals (not the module constants against themselves) kills a mutant that
    # renames a var -> the CLI would silently fail to pick up the gateway config.
    assert ANTHROPIC_BASE_URL_ENV == "ANTHROPIC_BASE_URL"
    assert ANTHROPIC_AUTH_TOKEN_ENV == "ANTHROPIC_AUTH_TOKEN"
    assert GATEWAY_MODEL_DISCOVERY_ENV == "CLAUDE_CODE_ENABLE_GATEWAY_MODEL_DISCOVERY"


@pytest.mark.unit
def test_anthropic_provider_model_is_eligible_and_builds_three_vars() -> None:
    env = build_cli_gateway_env(
        gateway_base_url=_URL,
        auth_token_placeholder=_TOKEN_PLACEHOLDER,
        requested_model=_model(ModelProvider.ANTHROPIC, "claude-opus"),
    )
    # Assert the literal keys + values (not via the constants) so a mutated constant
    # or discovery value ("1" -> something else) is caught.
    assert env == {
        "ANTHROPIC_BASE_URL": _URL,
        "ANTHROPIC_AUTH_TOKEN": _TOKEN_PLACEHOLDER,
        "CLAUDE_CODE_ENABLE_GATEWAY_MODEL_DISCOVERY": "1",
    }


@pytest.mark.unit
@pytest.mark.parametrize(
    ("name", "eligible"),
    [
        ("claude-opus", True),  # claude- prefix
        ("anthropic.claude-v2", True),  # anthropic. surface prefix
        ("anthropic/claude", True),  # anthropic/ namespaced prefix
        ("claudette", False),  # near-miss: not the claude- prefix
        ("anthropi", False),  # near-miss: not anthropic. / anthropic/
        ("gpt-claude", False),  # contains 'claude' but not a prefix -> ineligible
    ],
)
def test_each_anthropic_name_prefix_decides_eligibility_for_other_providers(
    name: str, eligible: bool
) -> None:
    # Per-prefix coverage so dropping/altering ANY element of the prefix tuple is
    # caught (the near-misses prove it is a PREFIX match, not a substring match).
    assert is_anthropic_eligible(_model(ModelProvider.OPENAI, name)) is eligible


@pytest.mark.unit
def test_claude_prefixed_name_under_other_surface_is_eligible() -> None:
    # An Anthropic model exposed via a hosted surface (e.g. Bedrock) is still eligible
    # because the bytes-on-the-wire are Anthropic-shaped.
    assert is_anthropic_eligible(_model(ModelProvider.BEDROCK, "anthropic.claude-v2"))
    env = build_cli_gateway_env(
        gateway_base_url=_URL,
        auth_token_placeholder=_TOKEN_PLACEHOLDER,
        requested_model=_model(ModelProvider.BEDROCK, "anthropic.claude-v2"),
    )
    assert env[GATEWAY_MODEL_DISCOVERY_ENV] == "1"


@pytest.mark.unit
@pytest.mark.security
@pytest.mark.parametrize(
    "model",
    [
        ModelRef(provider=ModelProvider.OPENAI, model_name="gpt-x"),
        ModelRef(provider=ModelProvider.GOOGLE, model_name="gemini-y"),
        ModelRef(provider=ModelProvider.OPENROUTER, model_name="llama-z"),
        ModelRef(provider=ModelProvider.BEDROCK, model_name="titan-text"),
    ],
)
def test_non_anthropic_cli_model_is_refused_fail_closed(model: ModelRef) -> None:
    assert not is_anthropic_eligible(model)
    # anchored exact message (the whole refusal text) kills the f-string-literal mutants.
    expected = (
        rf"^CLI agents may select Anthropic-family models only; "
        rf"{model.provider.value}:{model.model_name} is refused "
        rf"\(use the programmatic gateway lane for non-Anthropic models\)$"
    )
    with pytest.raises(NonAnthropicModelRefused, match=expected):
        build_cli_gateway_env(
            gateway_base_url=_URL,
            auth_token_placeholder=_TOKEN_PLACEHOLDER,
            requested_model=model,
        )


@pytest.mark.unit
@pytest.mark.parametrize("bad_url", ["", "   ", "\t"])
def test_blank_base_url_refused(bad_url: str) -> None:
    anth = _model(ModelProvider.ANTHROPIC, "claude")
    # anchored message + whitespace cases kill both the empty-check and the strip()
    # mutant (a blank-but-non-empty URL must also be refused).
    with pytest.raises(ValueError, match=r"^gateway_base_url must be non-empty$"):
        build_cli_gateway_env(
            gateway_base_url=bad_url,
            auth_token_placeholder=_TOKEN_PLACEHOLDER,
            requested_model=anth,
        )


@pytest.mark.unit
@pytest.mark.parametrize("bad_token", ["", "   ", "\t"])
def test_blank_auth_token_placeholder_refused(bad_token: str) -> None:
    anth = _model(ModelProvider.ANTHROPIC, "claude")
    with pytest.raises(ValueError, match=r"^auth_token_placeholder must be non-empty$"):
        build_cli_gateway_env(
            gateway_base_url=_URL, auth_token_placeholder=bad_token, requested_model=anth
        )


@pytest.mark.property
@given(name=st.text(min_size=1, max_size=24).filter(lambda s: s.strip() != ""))
def test_fuzz_non_anthropic_provider_never_accepted_unless_name_is_anthropic_family(
    name: str,
) -> None:
    # For a non-Anthropic provider, eligibility hinges ONLY on an Anthropic-family
    # name prefix; anything else must be refused. This pins the exact rule under fuzz.
    # (ModelRef itself refuses a blank name -- that fail-closed guard is tested
    # separately; here we fuzz only valid, non-blank model names.)
    model = _model(ModelProvider.OPENAI, name)
    lowered = name.strip().lower()
    expected_eligible = lowered.startswith(("claude-", "anthropic.", "anthropic/"))
    assert is_anthropic_eligible(model) == expected_eligible
    if not expected_eligible:
        with pytest.raises(NonAnthropicModelRefused):
            build_cli_gateway_env(
                gateway_base_url=_URL,
                auth_token_placeholder=_TOKEN_PLACEHOLDER,
                requested_model=model,
            )
