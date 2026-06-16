"""Tests: secrets come only from env/secret-manager and missing ones fail closed.

Proves the env source reads the deterministic variable name, fails closed (raising
SecretNotAvailable, naming only the variable not any value) when absent or blank,
and that the derived name is deterministic. Synthetic env only; never touches the
real process environment.
"""

from __future__ import annotations

import pytest
from hypothesis import given

from autofirm.access.secret_source_protocol import (
    EnvironmentSecretSource,
    MappingSecretSource,
    SecretNotAvailable,
    env_var_name_for,
)
from tests.access.synthetic_access_fixtures import identifier_strategy


@pytest.mark.unit
def test_env_source_reads_the_deterministic_variable() -> None:
    name = env_var_name_for("billing", "pg:db")
    source = EnvironmentSecretSource(environ={name: "synthetic-secret"})
    assert source.fetch("billing", "pg:db").reveal() == "synthetic-secret"


@pytest.mark.security
def test_env_source_missing_variable_fails_closed() -> None:
    source = EnvironmentSecretSource(environ={})  # nothing configured
    # fail-closed: no env var -> refuse, do not fabricate.
    with pytest.raises(SecretNotAvailable):
        source.fetch("billing", "pg:db")


@pytest.mark.security
def test_env_source_blank_variable_fails_closed() -> None:
    name = env_var_name_for("billing", "pg:db")
    source = EnvironmentSecretSource(environ={name: ""})  # present but empty
    with pytest.raises(SecretNotAvailable):
        source.fetch("billing", "pg:db")


@pytest.mark.security
def test_secret_not_available_message_does_not_leak_a_value() -> None:
    source = EnvironmentSecretSource(environ={})
    with pytest.raises(SecretNotAvailable) as exc:
        source.fetch("billing", "pg:db")
    # The message names the VARIABLE only -- it cannot leak a value it never had.
    assert "AUTOFIRM_SECRET__BILLING__PG_DB" in str(exc.value)


@pytest.mark.security
def test_mapping_source_unmapped_pair_fails_closed() -> None:
    source = MappingSecretSource({})
    with pytest.raises(SecretNotAvailable):
        source.fetch("billing", "pg:db")


@pytest.mark.unit
@pytest.mark.parametrize("blank", ["", "   "])
def test_env_var_name_refuses_blank_inputs(blank: str) -> None:
    with pytest.raises(ValueError):
        env_var_name_for(blank, "pg:db")
    with pytest.raises(ValueError):
        env_var_name_for("billing", blank)


@pytest.mark.property
@given(component=identifier_strategy, resource=identifier_strategy)
def test_property_env_var_name_is_deterministic_and_safe(
    component: str, resource: str
) -> None:
    """The derived name is deterministic, env-var-safe, and prefixed."""
    a = env_var_name_for(component, resource)
    b = env_var_name_for(component, resource)
    assert a == b  # deterministic
    assert a.startswith("AUTOFIRM_SECRET__")
    # Every char after the prefix is upper-alnum or underscore (env-var-safe).
    body = a[len("AUTOFIRM_SECRET__") :]
    assert all((c.isalnum() and (c.isupper() or c.isdigit())) or c == "_" for c in body)
