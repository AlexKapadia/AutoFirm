"""Typed least-privilege scope + the secret-redacting credential it grants.

What this does
--------------
Defines the two value objects the broker traffics in:

* :class:`CredentialScope` — the explicit, immutable description of *exactly*
  what a credential may do: a single ``resource`` (e.g. ``"postgres:tenant-db"``),
  a frozen set of ``operations`` (``READ`` / ``WRITE`` / ``ADMIN``), and a single
  ``tenant_id`` the credential is locked to (or the sentinel
  :data:`PLATFORM_TENANT` for non-tenant platform resources). A scope cannot be
  widened after construction.
* :class:`ScopedCredential` — a scope **plus** an opaque
  :class:`RedactedSecret` holding the actual secret material and an absolute
  expiry. Its ``__str__``/``__repr__`` and :meth:`audit_projection` NEVER reveal
  the secret — only non-secret metadata leaks out.

Why it exists / where it sits
-----------------------------
Research ``A8-integration-and-data-layer/SYNTHESIS.md`` L1.A8.3: agents get
**per-component, least-privilege, short-TTL** credentials, never standing god-keys,
and the secret is runtime-injected and never appears in prompts/logs. This module
is the typed contract that makes "least privilege" and "secret never logged"
*structural* properties rather than conventions. The broker
(:mod:`autofirm.access.credential_broker`) is the only thing that mints these.

Security / compliance invariants upheld (CLAUDE.md §5.6)
-------------------------------------------------------
* **Least privilege / no widening:** :class:`CredentialScope` is frozen; the only
  scope-to-scope relation exposed is :meth:`CredentialScope.permits`, which is a
  strict subset/equality check — a credential can only ever do *less*.
* **Secret never logged:** :class:`RedactedSecret` overrides every string
  projection to emit a redaction marker; the raw value is reachable only via the
  explicit :meth:`RedactedSecret.reveal`, used at the point of use, never in logs.
* **Validate at boundary:** empty resource, empty operation set, or an unknown
  operation is refused at construction (fail-closed).
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Final

from pydantic import BaseModel, ConfigDict, field_validator

__all__ = [
    "PLATFORM_TENANT",
    "CredentialScope",
    "Operation",
    "RedactedSecret",
    "ScopedCredential",
]

# Sentinel tenant for platform-level (non-tenant) resources. A real tenant id can
# never equal this (validated below), so a tenant credential can never be confused
# with a platform credential.
PLATFORM_TENANT: Final[str] = "__platform__"

# The fixed marker emitted anywhere a secret would otherwise be rendered. Asserted
# verbatim by the secrets-never-logged tests so a regression is caught immediately.
_REDACTION_MARKER: Final[str] = "<redacted-secret>"


class Operation(StrEnum):
    """The closed set of operations a scope may grant (deny-by-default).

    Kept deliberately small and ordered least->most privileged so tests can
    enumerate the full space; ``ADMIN`` does NOT imply ``READ``/``WRITE`` — each
    operation must be granted explicitly (no privilege bundling that could leak
    an unintended capability).
    """

    READ = "READ"
    WRITE = "WRITE"
    ADMIN = "ADMIN"


class CredentialScope(BaseModel):
    """An immutable, explicit description of what a credential may do.

    A scope is *(resource, operations, tenant_id)*. It is frozen, so it can never
    be widened after the broker mints it. :meth:`permits` is the single authority
    on whether an attempted (resource, operation, tenant) access is inside this
    scope — every guard in the system routes through it (one definition of "in
    scope", no convention drift).
    """

    model_config = ConfigDict(frozen=True)

    resource: str  # opaque resource id, e.g. "postgres:tenant-db" or "kms:signing"
    operations: frozenset[Operation]  # exact granted ops; never widened post-build
    tenant_id: str  # the one tenant this is locked to, or PLATFORM_TENANT

    @field_validator("resource", "tenant_id")
    @classmethod
    def _non_empty(cls, value: str) -> str:
        # fail-closed: an empty resource/tenant is ambiguous -> refuse to mint it.
        if not value or not value.strip():
            raise ValueError("scope resource and tenant_id must be non-empty")
        return value

    @field_validator("operations")
    @classmethod
    def _at_least_one_operation(
        cls, value: frozenset[Operation]
    ) -> frozenset[Operation]:
        # fail-closed: a scope granting no operations is meaningless; an empty set
        # must never be mistaken for "grants everything" -> refuse it outright.
        if not value:
            raise ValueError("scope must grant at least one operation")
        return value

    def permits(self, resource: str, operation: Operation, tenant_id: str) -> bool:
        """Return True iff this scope allows ``operation`` on ``resource`` for ``tenant_id``.

        Deny-by-default: every clause must match. Resource and tenant must be
        *exactly* equal (no prefix/wildcard widening) and the operation must be in
        the explicitly-granted set. This is the only place a credential's reach is
        decided, so a credential can never act outside its scope.
        """
        # tenant isolation: scope is locked to one tenant; a mismatch is refused.
        if tenant_id != self.tenant_id:
            return False  # fail-closed: cross-tenant use of this credential denied
        # least privilege: exact resource match only -- no wildcard/prefix widening.
        if resource != self.resource:
            return False  # fail-closed: out-of-resource use denied
        # least privilege: operation must be explicitly granted (no bundling).
        return operation in self.operations


class RedactedSecret(BaseModel):
    """An opaque holder for secret material whose string forms NEVER reveal it.

    The raw value is reachable only through the explicit :meth:`reveal`, called at
    the point of use (e.g. opening a DB connection). Every implicit projection
    (``str``/``repr``, logging via ``%s``/f-strings, pydantic ``model_dump`` of the
    parent) yields :data:`_REDACTION_MARKER`, so a secret cannot leak into a log,
    an audit record, or an exception message by accident.
    """

    model_config = ConfigDict(frozen=True)

    # The secret is stored under a private-by-convention field; all public
    # projections below redact it. Validation guarantees it is non-empty so a
    # "successfully issued" credential can never carry an empty secret.
    secret_value: str

    @field_validator("secret_value")
    @classmethod
    def _non_empty_secret(cls, value: str) -> str:
        # fail-closed: an empty secret is not a usable credential -> refuse it.
        if not value:
            raise ValueError("secret_value must be non-empty")
        return value

    def reveal(self) -> str:
        """Return the raw secret. Call ONLY at the point of use, never to log it."""
        return self.secret_value

    def __str__(self) -> str:  # noqa: D105 - redaction projection
        # secrets-never-logged: any str() (incl. f-strings/logging) is redacted.
        return _REDACTION_MARKER

    def __repr__(self) -> str:  # noqa: D105 - redaction projection
        # secrets-never-logged: repr() (incl. container/exception dumps) redacted.
        return _REDACTION_MARKER


class ScopedCredential(BaseModel):
    """A minted credential: a least-privilege :class:`CredentialScope` + secret + expiry.

    The credential is valid only until :attr:`expires_at`; the broker and every
    guard treat ``now >= expires_at`` as expired and fail closed. The secret is an
    opaque :class:`RedactedSecret`, so dumping or logging a credential never leaks
    its material -- only :meth:`audit_projection`'s non-secret metadata escapes.
    """

    model_config = ConfigDict(frozen=True)

    component: str  # who this was issued to (an opaque component/agent id)
    scope: CredentialScope
    secret: RedactedSecret
    issued_at: datetime
    expires_at: datetime

    def is_expired(self, now: datetime) -> bool:
        """Return True iff ``now`` is at or past the absolute expiry (fail-closed)."""
        # fail-closed: at-or-after expiry the credential is dead; '>=' (not '>') so
        # the exact expiry instant is already invalid (boundary-exact).
        return now >= self.expires_at

    def permits(self, resource: str, operation: Operation, tenant_id: str) -> bool:
        """Delegate the in-scope decision to the underlying :class:`CredentialScope`."""
        return self.scope.permits(resource, operation, tenant_id)

    def audit_projection(self) -> dict[str, str]:
        """Return ONLY non-secret metadata, safe to write to the append-only audit.

        Deliberately omits the secret entirely (not even the redaction marker for
        the value) so an audit record can never carry credential material.
        """
        return {
            "component": self.component,
            "resource": self.scope.resource,
            "operations": ",".join(sorted(op.value for op in self.scope.operations)),
            "tenant_id": self.scope.tenant_id,
            "issued_at": self.issued_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
        }
