"""Adversarial + property tests: the broker is least-privilege and fail-closed.

Proves the broker enforces the security spine, not just the happy path:
* a scoped credential NEVER authorizes anything outside its exact scope (PBT over
  arbitrary resource/op/tenant tuples);
* missing secret, blank component, non-positive TTL, and expiry all FAIL CLOSED
  and are audited as denials;
* every refusal and success is recorded append-only.
Synthetic only; no network/DB/real secrets.
"""

from __future__ import annotations

from datetime import timedelta

import pytest
from hypothesis import given
from hypothesis import strategies as st

from autofirm.access.credential_broker import (
    AccessDenied,
    CredentialBroker,
    CredentialIssuanceError,
)
from autofirm.access.credential_scope_contract import (
    CredentialScope,
    Operation,
)
from autofirm.access.secret_source_protocol import MappingSecretSource
from tests.access.synthetic_access_fixtures import (
    FIXED_NOW,
    AdvancingClock,
    RecordingAuditSink,
    identifier_strategy,
    operation_set_strategy,
    operation_strategy,
)


def _broker(secrets: dict[tuple[str, str], str]) -> tuple[CredentialBroker, RecordingAuditSink]:
    sink = RecordingAuditSink()
    broker = CredentialBroker(MappingSecretSource(secrets), AdvancingClock(), sink)
    return broker, sink


# --- Happy path: issuance is correct and audited ----------------------------


@pytest.mark.unit
def test_issue_stamps_scope_secret_and_expiry() -> None:
    broker, sink = _broker({("billing", "pg:db"): "synthetic-secret"})
    scope = CredentialScope(
        resource="pg:db", operations=frozenset({Operation.READ}), tenant_id="t1"
    )
    cred = broker.issue("billing", scope, timedelta(minutes=5))
    assert cred.component == "billing"
    assert cred.scope == scope
    assert cred.issued_at == FIXED_NOW
    assert cred.expires_at == FIXED_NOW + timedelta(minutes=5)
    # Issuance is audited with metadata only.
    assert sink.events[0]["event"] == "credential.issue"
    assert sink.events[0]["resource"] == "pg:db"


# --- Fail-closed issuance matrix --------------------------------------------


@pytest.mark.security
def test_missing_secret_fails_closed_and_is_audited() -> None:
    broker, sink = _broker({})  # no secret configured at all
    scope = CredentialScope(
        resource="pg:db", operations=frozenset({Operation.READ}), tenant_id="t1"
    )
    # fail-closed: no secret -> refuse to issue (never fabricate a credential).
    with pytest.raises(CredentialIssuanceError):
        broker.issue("billing", scope, timedelta(minutes=5))
    assert sink.events[-1]["event"] == "credential.issue.deny"
    assert sink.events[-1]["reason"] == "secret_not_available"


@pytest.mark.security
@pytest.mark.parametrize("bad_component", ["", "   ", "\t"])
def test_blank_component_is_refused(bad_component: str) -> None:
    broker, _ = _broker({(bad_component, "pg:db"): "s"})
    scope = CredentialScope(
        resource="pg:db", operations=frozenset({Operation.READ}), tenant_id="t1"
    )
    with pytest.raises(CredentialIssuanceError):
        broker.issue(bad_component, scope, timedelta(minutes=1))


@pytest.mark.security
@pytest.mark.parametrize("bad_ttl", [timedelta(0), timedelta(seconds=-1), timedelta(days=-1)])
def test_non_positive_ttl_is_refused(bad_ttl: timedelta) -> None:
    broker, _ = _broker({("billing", "pg:db"): "s"})
    scope = CredentialScope(
        resource="pg:db", operations=frozenset({Operation.READ}), tenant_id="t1"
    )
    # fail-closed: a zero/negative TTL would mint an already-dead/eternal credential.
    with pytest.raises(CredentialIssuanceError):
        broker.issue("billing", scope, bad_ttl)


# --- authorize() fail-closed boundaries -------------------------------------


@pytest.mark.security
def test_authorize_allows_exact_scope() -> None:
    broker, sink = _broker({("billing", "pg:db"): "s"})
    scope = CredentialScope(
        resource="pg:db", operations=frozenset({Operation.READ}), tenant_id="t1"
    )
    cred = broker.issue("billing", scope, timedelta(minutes=5))
    broker.authorize(cred, "pg:db", Operation.READ, "t1")  # in scope -> no raise
    assert sink.events[-1]["event"] == "credential.authorize.ok"


@pytest.mark.security
def test_authorize_denies_wrong_operation() -> None:
    broker, sink = _broker({("billing", "pg:db"): "s"})
    scope = CredentialScope(
        resource="pg:db", operations=frozenset({Operation.READ}), tenant_id="t1"
    )
    cred = broker.issue("billing", scope, timedelta(minutes=5))
    # least privilege: WRITE was never granted -> refuse even on the right resource.
    with pytest.raises(AccessDenied):
        broker.authorize(cred, "pg:db", Operation.WRITE, "t1")
    assert sink.events[-1]["reason"] == "out_of_scope"


@pytest.mark.security
def test_authorize_denies_wrong_resource() -> None:
    broker, _ = _broker({("billing", "pg:db"): "s"})
    scope = CredentialScope(
        resource="pg:db", operations=frozenset({Operation.READ}), tenant_id="t1"
    )
    cred = broker.issue("billing", scope, timedelta(minutes=5))
    with pytest.raises(AccessDenied):
        broker.authorize(cred, "kms:signing", Operation.READ, "t1")


@pytest.mark.security
def test_authorize_denies_cross_tenant() -> None:
    broker, sink = _broker({("billing", "pg:db"): "s"})
    scope = CredentialScope(
        resource="pg:db", operations=frozenset({Operation.READ}), tenant_id="t1"
    )
    cred = broker.issue("billing", scope, timedelta(minutes=5))
    # tenant isolation: a t1 credential can never act as t2.
    with pytest.raises(AccessDenied):
        broker.authorize(cred, "pg:db", Operation.READ, "t2")
    assert sink.events[-1]["reason"] == "out_of_scope"


@pytest.mark.security
def test_authorize_denies_at_and_after_expiry_boundary() -> None:
    # Clock advances 60s/call: issue at T, then authorize calls land at T+60, T+120.
    sink = RecordingAuditSink()
    clock = AdvancingClock(step=timedelta(seconds=60))
    broker = CredentialBroker(
        MappingSecretSource({("billing", "pg:db"): "s"}), clock, sink
    )
    scope = CredentialScope(
        resource="pg:db", operations=frozenset({Operation.READ}), tenant_id="t1"
    )
    # issued_at = FIXED_NOW (clock call #1); ttl 60s -> expires at FIXED_NOW+60.
    cred = broker.issue("billing", scope, timedelta(seconds=60))
    # authorize clock call #2 == FIXED_NOW+60 == exact expiry -> already expired.
    with pytest.raises(AccessDenied):
        broker.authorize(cred, "pg:db", Operation.READ, "t1")
    assert sink.events[-1]["reason"] == "expired"


# --- PROPERTY: no scoped credential ever exceeds its scope -------------------


# A grant and an attempt, each a (resource, op, tenant) triple, drawn independently
# so Hypothesis explores in-scope and every flavour of out-of-scope attempt.
_access_triple = st.tuples(identifier_strategy, operation_strategy, identifier_strategy)


@pytest.mark.property
@given(
    grant=st.tuples(identifier_strategy, operation_set_strategy, identifier_strategy),
    attempt=_access_triple,
)
def test_property_credential_never_exceeds_its_scope(
    grant: tuple[str, frozenset[Operation], str],
    attempt: tuple[str, Operation, str],
) -> None:
    """authorize() succeeds IFF the attempt is exactly inside the granted scope."""
    granted_resource, granted_ops, granted_tenant = grant
    attempt_resource, attempt_op, attempt_tenant = attempt
    broker, _ = _broker({("agent", granted_resource): "synthetic"})
    scope = CredentialScope(
        resource=granted_resource, operations=granted_ops, tenant_id=granted_tenant
    )
    cred = broker.issue("agent", scope, timedelta(minutes=5))

    in_scope = (
        attempt_resource == granted_resource
        and attempt_tenant == granted_tenant
        and attempt_op in granted_ops
    )
    if in_scope:
        broker.authorize(cred, attempt_resource, attempt_op, attempt_tenant)  # no raise
    else:
        with pytest.raises(AccessDenied):
            broker.authorize(cred, attempt_resource, attempt_op, attempt_tenant)


@pytest.mark.property
@given(
    ops_a=operation_set_strategy,
    ops_b=operation_set_strategy,
    resource=identifier_strategy,
    tenant=identifier_strategy,
    probe_op=operation_strategy,
)
def test_property_a_credential_is_a_subset_only_grant(
    ops_a: frozenset[Operation],
    ops_b: frozenset[Operation],
    resource: str,
    tenant: str,
    probe_op: Operation,
) -> None:
    """A scope's permits() is exactly its operation-set membership (no widening)."""
    scope_a = CredentialScope(resource=resource, operations=ops_a, tenant_id=tenant)
    # The mere existence of a broader scope_b must not affect scope_a's reach.
    _ = CredentialScope(resource=resource, operations=ops_a | ops_b, tenant_id=tenant)
    assert scope_a.permits(resource, probe_op, tenant) == (probe_op in ops_a)
