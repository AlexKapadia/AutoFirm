"""Fail-closed validation tests for the shared ModelRef / ModelProvider / UseCaseId."""

import pytest
from pydantic import ValidationError

from autofirm.modelgateway.model_reference import ModelProvider, ModelRef, UseCaseId


def test_model_ref_requires_non_empty_model_name() -> None:
    with pytest.raises(ValidationError, match="non-empty"):
        ModelRef(provider=ModelProvider.OPENAI, model_name="")
    with pytest.raises(ValidationError, match="non-empty"):
        ModelRef(provider=ModelProvider.OPENAI, model_name="   ")


def test_model_ref_refuses_unknown_provider() -> None:
    with pytest.raises(ValidationError):
        ModelRef(provider="not-a-provider", model_name="x")  # type: ignore[arg-type]


def test_model_ref_is_frozen() -> None:
    m = ModelRef(provider=ModelProvider.ANTHROPIC, model_name="claude")
    with pytest.raises(ValidationError):
        m.model_name = "other"  # type: ignore[misc]


def test_provider_enum_values_are_lower_cased_stable() -> None:
    assert ModelProvider.ANTHROPIC.value == "anthropic"
    assert ModelProvider.OPENAI.value == "openai"
    assert ModelProvider.GOOGLE.value == "google"
    assert ModelProvider.BEDROCK.value == "bedrock"
    assert ModelProvider.OPENROUTER.value == "openrouter"


def test_use_case_id_is_a_str_newtype() -> None:
    uc = UseCaseId("market-research")
    assert uc == "market-research"


def test_two_models_same_name_different_provider_are_distinct() -> None:
    a = ModelRef(provider=ModelProvider.GOOGLE, model_name="m")
    b = ModelRef(provider=ModelProvider.BEDROCK, model_name="m")
    assert a != b  # surface/provider is part of identity
