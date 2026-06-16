"""The secret-source seam: secrets come ONLY from env / a secret manager.

What this does
--------------
Defines :class:`SecretSource`, the injected Protocol the broker pulls raw secret
material from, plus two concrete sources:

* :class:`EnvironmentSecretSource` — reads the secret for a *(component, resource)*
  pair from a process environment variable, the only place a real deployment keeps
  a secret (env / secret-manager injection, never hard-coded). It fails closed if
  the variable is missing or blank.
* :class:`MappingSecretSource` — an in-memory source over an explicit mapping, for
  unit tests only (synthetic secrets, no real material, no environment mutation).

Why it exists / where it sits
-----------------------------
Research ``A8.../SYNTHESIS.md`` L1.A8.3 and CLAUDE.md §5.6: "Secrets via
environment or a secret manager only — never hard-coded, never in logs." Making
the source an injected Protocol keeps the broker free of any hard-coded secret and
lets tests drive it without touching the real environment. The deterministic
env-var **name** is derived here (not the value) so issuance is reproducible.

Security / compliance invariants upheld (CLAUDE.md §5.6)
-------------------------------------------------------
* **Secrets only from env/secret-manager:** there is no code path that embeds a
  secret literal; the value always originates from an injected source.
* **Fail closed on missing secret:** a source that cannot supply a non-empty
  secret raises :class:`SecretNotAvailable`; the broker turns that into a refusal.
* **Never logged:** sources return a :class:`RedactedSecret`, so the value is
  opaque to logging from the moment it enters the process.
"""

from __future__ import annotations

import os
from typing import Protocol, runtime_checkable

from autofirm.access.credential_scope_contract import RedactedSecret

__all__ = [
    "EnvironmentSecretSource",
    "MappingSecretSource",
    "SecretNotAvailable",
    "SecretSource",
    "env_var_name_for",
]


class SecretNotAvailable(Exception):
    """Raised when a source cannot supply a non-empty secret (fail-closed signal).

    The message intentionally names only the *env-var name / lookup key*, never any
    secret value, so even the failure path cannot leak material.
    """


def env_var_name_for(component: str, resource: str) -> str:
    """Derive the deterministic, upper-snake env-var NAME for a credential.

    Only the *name* is derived (e.g. ``AUTOFIRM_SECRET__BILLING__POSTGRES_TENANT_DB``);
    the value is never constructed in code. Determinism lets a deployment know
    exactly which variable to set and lets tests predict the lookup key.
    """
    # fail-closed: blank inputs would collapse to a guessable/ambiguous key.
    if not component or not component.strip() or not resource or not resource.strip():
        raise ValueError("component and resource must be non-empty to derive a key")

    def _norm(token: str) -> str:
        # Normalise to a stable env-var-safe token; non-alnum -> single underscore.
        out = []
        for ch in token.upper():
            out.append(ch if ch.isalnum() else "_")
        return "".join(out)

    return f"AUTOFIRM_SECRET__{_norm(component)}__{_norm(resource)}"


@runtime_checkable
class SecretSource(Protocol):
    """The single source of raw secret material for the broker (injected).

    Implementations MUST return a :class:`RedactedSecret` (so the value is opaque
    immediately) or raise :class:`SecretNotAvailable` (fail-closed). They must
    never log, print, or echo the value.
    """

    def fetch(self, component: str, resource: str) -> RedactedSecret:
        """Return the secret for ``(component, resource)`` or raise SecretNotAvailable."""
        ...


class EnvironmentSecretSource:
    """A :class:`SecretSource` backed by process environment variables.

    The real-deployment source: a secret is set in the environment (typically by a
    secret manager at launch) under the deterministic name from
    :func:`env_var_name_for`. A missing or blank variable fails closed.
    """

    def __init__(self, environ: dict[str, str] | None = None) -> None:
        """Bind to ``environ`` (defaults to the live ``os.environ`` snapshot)."""
        # Inject the mapping for testability; default to the real process env.
        self._environ = dict(os.environ) if environ is None else environ

    def fetch(self, component: str, resource: str) -> RedactedSecret:
        """Read the secret env var; raise :class:`SecretNotAvailable` if absent/blank."""
        name = env_var_name_for(component, resource)
        raw = self._environ.get(name)
        # fail-closed: no secret configured for this component/resource -> refuse.
        # The exception names only the VARIABLE, never any value (no leak).
        if raw is None or raw == "":
            raise SecretNotAvailable(f"no secret configured at env var {name}")
        return RedactedSecret(secret_value=raw)


class MappingSecretSource:
    """An in-memory :class:`SecretSource` over an explicit mapping (tests only).

    Keys are ``(component, resource)`` tuples mapping to synthetic secret strings.
    Used so unit tests never touch the real environment or any real secret.
    """

    def __init__(self, secrets: dict[tuple[str, str], str]) -> None:
        """Bind to a synthetic ``(component, resource) -> secret`` mapping."""
        self._secrets = dict(secrets)

    def fetch(self, component: str, resource: str) -> RedactedSecret:
        """Return the mapped synthetic secret or raise :class:`SecretNotAvailable`."""
        raw = self._secrets.get((component, resource))
        # fail-closed: unmapped pair -> refuse, identical contract to the env source.
        if raw is None or raw == "":
            raise SecretNotAvailable(
                f"no secret configured for ({component!r}, {resource!r})"
            )
        return RedactedSecret(secret_value=raw)
