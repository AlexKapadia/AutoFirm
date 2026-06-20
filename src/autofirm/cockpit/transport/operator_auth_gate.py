"""The fail-closed operator authentication gate (deny-by-default, constant-time, no leaks).

What this does
--------------
Defines :class:`AuthError` and :func:`authenticate_operator`, the single guard the cockpit
transport calls before any auth-gated command runs. The EXPECTED operator secret is read from
the injected environment under :data:`OPERATOR_TOKEN_ENV_VAR`; the PRESENTED token arrives on a
separate channel (the CLI ``--token`` value). The gate refuses — raising :class:`AuthError` —
when the expected secret is missing/blank, the presented token is missing/blank, or the two do
not match, and otherwise returns ``None`` (allow). The comparison is constant-time
(``hmac.compare_digest``) and NO token value ever appears in a message, log, or exception.

Why it exists / where it sits
-----------------------------
A cockpit observes the whole company; it must not launch for an unauthenticated operator. This
is the deny-by-default trust boundary (CLAUDE.md §5.6): unless a correct, non-blank token is
presented against a configured, non-blank secret, the gate refuses and the CLI emits no data.
Sits in the transport layer; depends only on stdlib (``hmac``) — no adapter/eventlog/on-main.

Security / compliance invariants upheld
---------------------------------------
* **Deny by default (§5.6):** every failure mode (no secret configured, no token presented,
  mismatch) refuses; only an exact, non-blank match returns. There is no implicit-allow path.
* **Constant-time comparison (§5.6):** ``hmac.compare_digest`` defends against a timing oracle;
  an equal-length-but-different and a different-length token both refuse.
* **No secret leakage (§5.6):** neither the expected nor the presented token is ever placed in
  an exception message, so a refusal is auditable without exposing a credential.
* **No ambient env read (§5.6 least surprise / testability):** the environment is INJECTED, so
  the gate never reads ``os.environ`` itself and a test never mutates process state.
"""

from __future__ import annotations

import hmac
from collections.abc import Mapping

__all__ = ["OPERATOR_TOKEN_ENV_VAR", "AuthError", "authenticate_operator"]

# The environment key the configured operator secret is read from (never hard-coded, never
# logged). The CLI passes the PRESENTED token separately via --token; the two are compared.
OPERATOR_TOKEN_ENV_VAR = "AUTOFIRM_COCKPIT_TOKEN"


class AuthError(Exception):
    """Raised when operator authentication fails (fail-closed; carries no token value).

    The message names only the failure category (no secret configured / no token presented /
    mismatch) — never the expected or presented token — so a refusal is auditable without
    exposing a credential.
    """


def authenticate_operator(presented_token: str | None, *, env: Mapping[str, str]) -> None:
    """Authenticate the operator fail-closed; return ``None`` on success, raise on refusal.

    Args:
        presented_token: The token supplied on the command channel (the CLI ``--token``).
            ``None``, empty, or whitespace-only is refused.
        env: The environment mapping to read the configured secret from (injected — the gate
            never touches ``os.environ`` directly).

    Returns:
        ``None`` when the presented token exactly matches the configured secret.

    Raises:
        AuthError: If the configured secret is missing/blank, the presented token is
            missing/blank, or the two do not match (constant-time comparison).
    """
    expected = env.get(OPERATOR_TOKEN_ENV_VAR)
    # fail-closed: no secret configured -> refuse (never compare a token to itself).
    if expected is None or not expected.strip():
        raise AuthError("operator token is not configured")
    # fail-closed: no token presented -> refuse before any comparison.
    if presented_token is None or not presented_token.strip():
        raise AuthError("no operator token was presented")
    # constant-time: defends against a timing side-channel; refuses on any difference
    # (including a different-length token) without revealing which byte differed.
    if not hmac.compare_digest(expected.encode("utf-8"), presented_token.encode("utf-8")):
        raise AuthError("operator token did not match")
