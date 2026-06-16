"""A non-secret REFERENCE to a scoped credential, safe to embed in a session.

What this does
--------------
Defines :class:`ScopedCredentialReference` — the *handle* a session carries to
the credential it was launched with. It records only non-secret metadata
(component, resource, granted operations, tenant, expiry); it NEVER holds the
secret material. The raw secret stays inside the access layer's
:class:`~autofirm.access.credential_scope_contract.ScopedCredential` (whose
``RedactedSecret`` already refuses to render itself) and is revealed only at the
point of use by the production launcher, never stored on the session model.

Why it exists / where it sits
-----------------------------
A5 SYNTHESIS §3(2): roles get least-authority, scoped credentials; the secret is
runtime-injected and must never appear in prompts, transcripts, or logs. The
session lifecycle, audit trail, and handoff summary all need to know *which*
credential a session holds (to enforce no-spawn-without-credential and to record
it) but must be structurally incapable of leaking the secret. This reference is
that structural guarantee: there is no field on it that could carry the secret,
so dumping / logging / handing-off a session can never expose credential
material. It is built from a live ``ScopedCredential`` via
:meth:`from_scoped_credential`, which reads only the credential's
``audit_projection`` (its own secret-free view).

Security / compliance invariants upheld (CLAUDE.md §5.6)
-------------------------------------------------------
* **Secret never logged / never stored on the session (§5.6):** this type has no
  secret field by construction; the access layer keeps the secret, the session
  keeps only this reference.
* **Fail-closed validity (§5.6):** :meth:`is_valid_at` treats ``now >= expiry``
  as expired and refuses — a session can never be (re)spawned against an expired
  credential.
* **Least privilege visibility:** only the granted-operations *names* are
  recorded, never a widened or wildcard scope.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator

from autofirm.access.credential_scope_contract import ScopedCredential

__all__ = ["ScopedCredentialReference"]


class ScopedCredentialReference(BaseModel):
    """An immutable, secret-free pointer to the credential a session was issued.

    Every field is non-secret metadata, so this object is safe to embed in the
    session model, write to the audit trail, and copy into a handoff summary. The
    secret itself is never present — by design there is no field that could hold
    it.
    """

    model_config = ConfigDict(frozen=True)

    component: str  # the component/role this credential was issued to
    resource: str  # the single resource it grants access to (e.g. "postgres:db")
    operations: tuple[str, ...]  # granted operation NAMES only (least privilege)
    tenant_id: str  # the one tenant it is locked to, or the platform sentinel
    expires_at: datetime  # absolute expiry; checked fail-closed on (re)spawn

    @field_validator("component", "resource", "tenant_id")
    @classmethod
    def _non_empty(cls, value: str) -> str:
        # fail-closed: an empty component/resource/tenant is an ambiguous
        # reference -> refuse it, so a session can never bind to a vague credential.
        if not value or not value.strip():
            raise ValueError("credential reference fields must be non-empty")
        return value

    @field_validator("operations")
    @classmethod
    def _at_least_one_operation(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        # fail-closed: a reference granting no operation is meaningless and must
        # never be mistaken for "grants everything".
        if not value:
            raise ValueError("credential reference must grant at least one operation")
        return value

    @classmethod
    def from_scoped_credential(cls, credential: ScopedCredential) -> ScopedCredentialReference:
        """Build a secret-free reference from a live ``ScopedCredential``.

        Reads ONLY the credential's ``audit_projection`` (its own secret-free
        view), so the secret material is never even passed into this type. This
        is the only supported way to construct a reference from a real
        credential.
        """
        # secrets-never-logged: audit_projection() deliberately omits the secret;
        # we copy only its non-secret metadata, so no secret can reach this object.
        projection = credential.audit_projection()
        operations = tuple(
            op for op in projection["operations"].split(",") if op
        )
        return cls(
            component=projection["component"],
            resource=projection["resource"],
            operations=operations,
            tenant_id=projection["tenant_id"],
            expires_at=credential.expires_at,
        )

    def is_valid_at(self, now: datetime) -> bool:
        """Return True iff the credential is still live at ``now`` (fail-closed).

        Uses ``now < expires_at`` (strict), so the exact expiry instant is already
        invalid — boundary-exact with the access layer's ``is_expired`` (which
        uses ``>=``). A session is refused (re)spawn the moment its credential
        reference is not valid here.
        """
        # fail-closed: at-or-after expiry the credential is dead; refuse use.
        return now < self.expires_at
