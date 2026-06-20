"""operator_auth_gate: deny-by-default, constant-time, no-leak operator authentication.

This is the cockpit's security-critical trust boundary. Every refusal path is asserted
INDEPENDENTLY so a `not`/boolean mutant that collapses one path is killed; the exact-match
allow path is the only non-raising one, and no test ever lets a token reach an error string.
"""

from __future__ import annotations

from collections.abc import Mapping

import pytest

from autofirm.cockpit.transport.operator_auth_gate import (
    OPERATOR_TOKEN_ENV_VAR,
    AuthError,
    authenticate_operator,
)

_SECRET = "s3cr3t-operator-token-value"


def _env(value: str | None) -> Mapping[str, str]:
    return {} if value is None else {OPERATOR_TOKEN_ENV_VAR: value}


# --------------------------- configured secret missing/blank --------------------------- #


def test_refuses_when_secret_not_configured() -> None:
    with pytest.raises(AuthError, match="not configured"):
        authenticate_operator(_SECRET, env=_env(None))


def test_refuses_when_secret_is_empty() -> None:
    with pytest.raises(AuthError, match="not configured"):
        authenticate_operator(_SECRET, env=_env(""))


@pytest.mark.parametrize("blank", ["   ", "\t", "\n", " \t "])
def test_refuses_when_secret_is_whitespace_only(blank: str) -> None:
    with pytest.raises(AuthError, match="not configured"):
        authenticate_operator(_SECRET, env=_env(blank))


# --------------------------- presented token missing/blank --------------------------- #


def test_refuses_when_no_token_presented() -> None:
    with pytest.raises(AuthError, match="no operator token"):
        authenticate_operator(None, env=_env(_SECRET))


def test_refuses_when_presented_token_empty() -> None:
    with pytest.raises(AuthError, match="no operator token"):
        authenticate_operator("", env=_env(_SECRET))


@pytest.mark.parametrize("blank", ["   ", "\t", "\n"])
def test_refuses_when_presented_token_whitespace_only(blank: str) -> None:
    with pytest.raises(AuthError, match="no operator token"):
        authenticate_operator(blank, env=_env(_SECRET))


# --------------------------- mismatch (constant-time comparison) --------------------------- #


def test_refuses_on_equal_length_but_different_token() -> None:
    presented = "x" * len(_SECRET)  # same length, different content -> compare_digest False
    assert len(presented) == len(_SECRET)
    with pytest.raises(AuthError, match="did not match"):
        authenticate_operator(presented, env=_env(_SECRET))


def test_refuses_on_different_length_token() -> None:
    with pytest.raises(AuthError, match="did not match"):
        authenticate_operator(_SECRET + "extra", env=_env(_SECRET))


def test_refuses_on_case_difference() -> None:
    with pytest.raises(AuthError, match="did not match"):
        authenticate_operator(_SECRET.upper(), env=_env(_SECRET))


# --------------------------- allow (exact match) --------------------------- #


def test_allows_exact_match_returns_none() -> None:
    assert authenticate_operator(_SECRET, env=_env(_SECRET)) is None


def test_allows_when_secret_has_internal_whitespace_but_matches_exactly() -> None:
    secret = "a b c"  # non-blank (strip is truthy); compared verbatim, not stripped
    assert authenticate_operator("a b c", env=_env(secret)) is None
    with pytest.raises(AuthError, match="did not match"):
        authenticate_operator("abc", env=_env(secret))  # stripping would WRONGLY allow this


# --------------------------- no-leak invariant --------------------------- #


def test_no_token_value_appears_in_any_error_message() -> None:
    presented = "presented-secret-DO-NOT-LEAK"
    secret = "expected-secret-DO-NOT-LEAK"
    with pytest.raises(AuthError) as exc:
        authenticate_operator(presented, env=_env(secret))
    message = str(exc.value)
    assert presented not in message
    assert secret not in message


def test_no_secret_value_leaks_when_no_token_presented() -> None:
    secret = "expected-secret-DO-NOT-LEAK"
    with pytest.raises(AuthError) as exc:
        authenticate_operator(None, env=_env(secret))
    assert secret not in str(exc.value)
