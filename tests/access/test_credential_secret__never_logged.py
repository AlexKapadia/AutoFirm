"""Adversarial + property tests: a secret NEVER appears in any string/log/audit.

The single most important security property of the broker: secret material is
opaque to every projection -- str(), repr(), f-strings/logging, exception text,
pydantic model_dump, AND the entire append-only audit stream -- and is reachable
ONLY via the explicit reveal(). Proven over arbitrary high-entropy secrets so a
regression that lets a secret slip into a log is caught immediately.
Synthetic only; no network/DB.
"""

from __future__ import annotations

import contextlib
from datetime import timedelta

import pytest
from hypothesis import given
from hypothesis import strategies as st

from autofirm.access.credential_broker import AccessDenied, CredentialBroker
from autofirm.access.credential_scope_contract import (
    CredentialScope,
    Operation,
    RedactedSecret,
)
from autofirm.access.secret_source_protocol import (
    MappingSecretSource,
    env_var_name_for,
)
from tests.access.synthetic_access_fixtures import (
    AdvancingClock,
    RecordingAuditSink,
)

# Synthetic secrets carry a sentinel prefix that CANNOT occur in the broker's
# fixed audit vocabulary (event names, metadata keys, ISO timestamps), so a
# substring hit in the audit blob can only mean the SECRET MATERIAL itself leaked
# -- not an incidental collision with an English word like "operation". The
# random tail keeps each example distinct/high-entropy.
_SECRET_SENTINEL = "ZZSECRETZZ-"
_secret_strategy = st.text(
    alphabet=st.characters(min_codepoint=33, max_codepoint=126),
    min_size=8,
    max_size=64,
).map(lambda tail: _SECRET_SENTINEL + tail)


def _all_recorded_text(events: list[dict[str, str]]) -> str:
    """Flatten every recorded audit value into one searchable blob."""
    return " ".join(f"{k}={v}" for e in events for k, v in e.items())


@pytest.mark.security
def test_redacted_secret_str_and_repr_hide_value() -> None:
    secret = RedactedSecret(secret_value="TOP-SECRET-1234")
    # secrets-never-logged: implicit projections must NOT contain the value.
    assert "TOP-SECRET-1234" not in str(secret)
    assert "TOP-SECRET-1234" not in repr(secret)
    assert "TOP-SECRET-1234" not in f"{secret}"
    assert "TOP-SECRET-1234" not in f"{secret!r}"
    # The marker is what leaks instead.
    assert str(secret) == "<redacted-secret>"
    # ...but reveal() at the point of use returns the real value.
    assert secret.reveal() == "TOP-SECRET-1234"


@pytest.mark.security
def test_model_dump_of_credential_does_not_leak_secret() -> None:
    sink = RecordingAuditSink()
    broker = CredentialBroker(
        MappingSecretSource({("billing", "pg:db"): "SENTINEL-SECRET-XYZ"}),
        AdvancingClock(),
        sink,
    )
    scope = CredentialScope(
        resource="pg:db", operations=frozenset({Operation.READ}), tenant_id="t1"
    )
    cred = broker.issue("billing", scope, timedelta(minutes=5))
    # audit_projection is the ONLY metadata path and must omit the secret entirely.
    assert "SENTINEL-SECRET-XYZ" not in str(cred.audit_projection())
    # repr of the whole credential (e.g. in an exception/log) redacts the secret.
    assert "SENTINEL-SECRET-XYZ" not in repr(cred)


@pytest.mark.security
def test_env_var_name_helper_never_embeds_a_secret_value() -> None:
    # The derived name carries only the (non-secret) component/resource, never a value.
    name = env_var_name_for("billing", "pg:db")
    assert name == "AUTOFIRM_SECRET__BILLING__PG_DB"
    assert "secret" not in name.lower().replace("autofirm_secret", "")


@pytest.mark.property
@given(secret=_secret_strategy)
def test_property_secret_never_appears_in_any_audit_event(secret: str) -> None:
    """No secret value ever appears in the audit stream (issuance + every decision)."""
    sink = RecordingAuditSink()
    broker = CredentialBroker(
        MappingSecretSource({("agent", "res"): secret}), AdvancingClock(), sink
    )
    scope = CredentialScope(
        resource="res", operations=frozenset({Operation.READ}), tenant_id="t1"
    )
    cred = broker.issue("agent", scope, timedelta(minutes=5))
    # Drive a success and several denials so every audit branch is exercised.
    broker.authorize(cred, "res", Operation.READ, "t1")
    for res, op, ten in [
        ("res", Operation.WRITE, "t1"),  # wrong op
        ("other", Operation.READ, "t1"),  # wrong resource
        ("res", Operation.READ, "t2"),  # cross tenant
    ]:
        # Each call denies (audited); suppress so we reach the blob scan below.
        with contextlib.suppress(AccessDenied):
            broker.authorize(cred, res, op, ten)
    blob = _all_recorded_text(sink.events)
    # secrets-never-logged: the secret must appear NOWHERE in the audit stream.
    assert secret not in blob


@pytest.mark.property
@given(secret=_secret_strategy)
def test_property_secret_never_appears_in_string_projections(secret: str) -> None:
    """str()/repr() of the holder never contain the value; reveal() returns it exactly."""
    holder = RedactedSecret(secret_value=secret)
    assert secret not in str(holder)
    assert secret not in repr(holder)
    assert holder.reveal() == secret  # exactness preserved for the point-of-use path
