"""The credential broker: mints per-component, least-privilege, audited credentials.

What this does
--------------
:class:`CredentialBroker` is the *only* thing in the platform that issues a
:class:`~autofirm.access.credential_scope_contract.ScopedCredential`. Given a
component id and the explicit :class:`~autofirm.access.credential_scope_contract.CredentialScope`
it needs, the broker:

1. pulls the raw secret from the injected
   :class:`~autofirm.access.secret_source_protocol.SecretSource` (env /
   secret-manager only) -- failing closed if none is configured;
2. stamps an absolute short TTL from the injected clock;
3. emits an append-only audit record of the issuance (non-secret metadata only); and
4. returns the credential.

It also exposes :meth:`authorize`, the single guard a holder calls before acting:
it re-checks expiry and scope and fails closed (auditing the DENY) on any miss.

Why it exists / where it sits
-----------------------------
Research ``A8.../SYNTHESIS.md`` L1.A8.3 (per-session, least-privilege, short-TTL
credentials; no standing god-keys) and CLAUDE.md §5.6. Centralising issuance +
authorization here means least-privilege and fail-closed are enforced in one
audited place, not re-implemented (and mis-implemented) per call site.

Security / compliance invariants upheld (CLAUDE.md §5.6)
-------------------------------------------------------
* **No god-keys / least privilege:** every credential carries exactly the
  caller-declared scope; the broker never widens it and there is no "all access".
* **Secrets via env/secret-manager only, never logged:** the secret comes from the
  injected source and is wrapped opaque; only :meth:`ScopedCredential.audit_projection`
  metadata is ever audited.
* **Fail closed:** missing secret, non-positive TTL, expired credential, or any
  out-of-scope / cross-tenant access is refused (and the refusal is audited).
* **Append-only audit:** issuance and every DENY/SUCCESS authorization decision is
  recorded via the injected sink, which only ever appends.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Protocol, runtime_checkable

from autofirm.access.credential_scope_contract import (
    CredentialScope,
    Operation,
    ScopedCredential,
)
from autofirm.access.secret_source_protocol import SecretNotAvailable, SecretSource

__all__ = [
    "AccessDenied",
    "AuditSink",
    "Clock",
    "CredentialBroker",
    "CredentialIssuanceError",
]


class CredentialIssuanceError(Exception):
    """Raised when a credential cannot be minted (fail-closed issuance failure)."""


class AccessDenied(Exception):
    """Raised by :meth:`CredentialBroker.authorize` on any out-of-scope/expired use.

    Carries only non-secret context (component, resource, operation, tenant) so the
    refusal is debuggable without ever exposing credential material.
    """


@runtime_checkable
class Clock(Protocol):
    """Injected source of 'now' (mirrors :class:`autofirm.org.org_identifiers.Clock`).

    Injecting time keeps issuance/expiry deterministic and lets tests pin the exact
    issued_at/expires_at instants rather than depending on wall-clock.
    """

    def now(self) -> datetime:
        """Return the current instant as a timezone-aware UTC ``datetime``."""
        ...


@runtime_checkable
class AuditSink(Protocol):
    """Append-only sink for issuance / authorization decisions (injected).

    The broker hands it a *non-secret* event dict; implementations MUST only append
    (never update/delete) and MUST NOT log the dict anywhere that mixes in secrets.
    """

    def append(self, event: dict[str, str]) -> None:
        """Append one non-secret audit event. Implementations never mutate history."""
        ...


class CredentialBroker:
    """Mints and authorizes least-privilege, fail-closed, audited credentials.

    The broker is constructed with its three seams -- a :class:`SecretSource`
    (where secrets come from), a :class:`Clock` (the only source of now/expiry), and
    an :class:`AuditSink` (append-only record of every decision) -- so it holds no
    ambient state and is fully deterministic under test.
    """

    def __init__(
        self,
        secret_source: SecretSource,
        clock: Clock,
        audit_sink: AuditSink,
    ) -> None:
        """Bind the broker to its secret source, clock, and append-only audit sink."""
        self._secret_source = secret_source
        self._clock = clock
        self._audit = audit_sink

    def issue(
        self,
        component: str,
        scope: CredentialScope,
        ttl: timedelta,
    ) -> ScopedCredential:
        """Issue a scoped, short-TTL credential for ``component`` over ``scope``.

        Pulls the secret from the injected source, stamps issued/expiry from the
        clock, audits the issuance (non-secret metadata only), and returns the
        credential. Fails closed -- raising :class:`CredentialIssuanceError` -- if
        the component is blank, the TTL is non-positive, or no secret is configured.

        Args:
            component: Opaque component/agent id the credential is issued to.
            scope: The exact (and only) privileges the credential will carry.
            ttl: Positive lifetime; the credential expires at ``now + ttl``.

        Returns:
            A :class:`ScopedCredential` valid until ``issued_at + ttl``.

        Raises:
            CredentialIssuanceError: blank component, non-positive TTL, or no secret.
        """
        # fail-closed: a blank component id makes issuance untraceable -> refuse.
        if not component or not component.strip():
            raise CredentialIssuanceError("component must be a non-empty id")
        # fail-closed: a zero/negative TTL would mint an already-dead or eternal
        # credential; both are unsafe, so only a strictly-positive TTL is allowed.
        if ttl <= timedelta(0):
            raise CredentialIssuanceError("ttl must be strictly positive")

        try:
            # Secrets via env/secret-manager only: the value originates from the
            # injected source, never from code in this module.
            secret = self._secret_source.fetch(component, scope.resource)
        except SecretNotAvailable as exc:
            # fail-closed: no secret configured -> refuse to issue (never fabricate).
            self._audit.append(
                {
                    "event": "credential.issue.deny",
                    "reason": "secret_not_available",
                    "component": component,
                    "resource": scope.resource,
                    "tenant_id": scope.tenant_id,
                }
            )
            raise CredentialIssuanceError(
                f"no secret available for component {component!r}"
            ) from exc

        issued_at = self._clock.now()
        credential = ScopedCredential(
            component=component,
            scope=scope,
            secret=secret,
            issued_at=issued_at,
            expires_at=issued_at + ttl,
        )
        # Append-only audit of issuance -- metadata ONLY (audit_projection omits the
        # secret entirely), so no credential material can reach the audit log.
        self._audit.append({"event": "credential.issue", **credential.audit_projection()})
        return credential

    def authorize(
        self,
        credential: ScopedCredential,
        resource: str,
        operation: Operation,
        tenant_id: str,
    ) -> None:
        """Assert ``credential`` may perform ``operation`` on ``resource`` for ``tenant_id``.

        The single guard every holder calls before acting. It fails closed on an
        expired credential or any out-of-scope / cross-tenant access, auditing the
        DENY; on success it audits a SUCCESS and returns ``None``.

        Raises:
            AccessDenied: credential expired, or access is outside the credential's
                scope / tenant.
        """
        now = self._clock.now()
        # fail-closed: an expired credential authorizes nothing.
        if credential.is_expired(now):
            self._audit.append(
                {
                    "event": "credential.authorize.deny",
                    "reason": "expired",
                    "component": credential.component,
                    "resource": resource,
                    "operation": operation.value,
                    "tenant_id": tenant_id,
                }
            )
            raise AccessDenied(
                f"credential for {credential.component!r} expired "
                f"(resource={resource!r}, op={operation.value}, tenant={tenant_id!r})"
            )
        # least privilege + tenant isolation: the scope is the sole authority on
        # reach; anything it does not explicitly permit is refused.
        if not credential.permits(resource, operation, tenant_id):
            self._audit.append(
                {
                    "event": "credential.authorize.deny",
                    "reason": "out_of_scope",
                    "component": credential.component,
                    "resource": resource,
                    "operation": operation.value,
                    "tenant_id": tenant_id,
                }
            )
            raise AccessDenied(
                f"out-of-scope access refused for {credential.component!r} "
                f"(resource={resource!r}, op={operation.value}, tenant={tenant_id!r})"
            )
        self._audit.append(
            {
                "event": "credential.authorize.ok",
                "component": credential.component,
                "resource": resource,
                "operation": operation.value,
                "tenant_id": tenant_id,
            }
        )
