"""PURE builder of the CLI-substrate gateway env map (ADR-003 linchpin: Anthropic-only).

What this does
--------------
Builds the environment-variable map that points a ``claude`` CLI session at the
self-hosted model-egress gateway, and ENFORCES the ADR-003 linchpin: a CLI-substrate
agent may select ONLY Anthropic-family models. The three vars (verified live at
Gate-1) are:

* ``ANTHROPIC_BASE_URL``       — the gateway's OpenAI-compatible base URL.
* ``ANTHROPIC_AUTH_TOKEN``     — the per-session minted virtual key (the SECRET; the
  resolved value is injected by the launcher at point-of-use, never built here).
* ``CLAUDE_CODE_ENABLE_GATEWAY_MODEL_DISCOVERY`` = ``"1"`` — lets the CLI discover
  the gateway's model catalog (v2.1.129+).

For a CLI agent, any requested model is validated against an Anthropic-eligible
allowlist (provider ``anthropic`` OR a ``claude-``/``anthropic.`` /``anthropic/``-
prefixed name). A non-Anthropic model is REFUSED fail-closed — that traffic must use
the programmatic :class:`ModelGatewayClient` path, where any provider is allowed
(ADR-003 §3). The secret never appears in this map's *keys* and the SECRET VALUE is
resolved elsewhere: this builder takes only a non-secret token PLACEHOLDER reference,
so a constructed-and-logged env map can never leak the virtual key.

Why it exists / where it sits
-----------------------------
ADR-003 §2 (CLI lane = Anthropic-only full fidelity) and Gate-1 item 1 (the env
honouring). Keeping it PURE (a function of base-url + a secret-free token marker +
the requested model) makes the Anthropic-only enforcement exhaustively testable with
no process and no secret (CLAUDE.md §5.5).

Security / compliance invariants upheld (CLAUDE.md §5.6)
-------------------------------------------------------
* **ADR-003 linchpin fail-closed:** a non-Anthropic model for a CLI agent is REFUSED
  (raises) — the uncertified cross-provider CLI path is never built.
* **Secret never in this map:** the builder takes a secret-free placeholder for the
  auth token value; the real virtual key is resolved by the launcher at point-of-use.
* **No silent default:** an empty base URL or model name is refused (fail-closed).
"""

from __future__ import annotations

from autofirm.modelgateway.model_reference import ModelProvider, ModelRef

__all__ = [
    "ANTHROPIC_AUTH_TOKEN_ENV",
    "ANTHROPIC_BASE_URL_ENV",
    "GATEWAY_MODEL_DISCOVERY_ENV",
    "NonAnthropicModelRefused",
    "build_cli_gateway_env",
    "is_anthropic_eligible",
]

# The three CLI gateway env-var NAMES (Gate-1 verified). These are names, never
# secrets — only ANTHROPIC_AUTH_TOKEN's VALUE is a secret, injected by the launcher.
ANTHROPIC_BASE_URL_ENV = "ANTHROPIC_BASE_URL"
ANTHROPIC_AUTH_TOKEN_ENV = "ANTHROPIC_AUTH_TOKEN"  # nosec B105 - env-var NAME, not a secret
GATEWAY_MODEL_DISCOVERY_ENV = "CLAUDE_CODE_ENABLE_GATEWAY_MODEL_DISCOVERY"

# Name prefixes that mark an Anthropic-family model on a gateway whose catalog may
# expose many providers. The CLI lane is restricted to these; everything else must
# go through the programmatic any-provider lane (ADR-003 §2/§3).
_ANTHROPIC_NAME_PREFIXES = ("claude-", "anthropic.", "anthropic/")


class NonAnthropicModelRefused(ValueError):
    """Raised when a CLI agent requests a non-Anthropic model (ADR-003 linchpin).

    The CLI lane preserves full fidelity ONLY for Anthropic-family models; a
    non-Anthropic model on this path is refused fail-closed so the uncertified
    cross-provider CLI channel is never used. Names only the model (non-secret).

    Subclasses :class:`ValueError` so that when raised inside a pydantic
    ``field_validator`` (e.g. ``LaunchSpec.model``) it is surfaced as a
    ``ValidationError`` at the boundary, consistent with the other fail-closed
    validators — while still being a distinct, catchable type at a direct call site.
    """


def is_anthropic_eligible(model: ModelRef) -> bool:
    """Return True iff ``model`` is an Anthropic-family model selectable on the CLI lane.

    Eligible iff the provider is ``anthropic`` OR the model name carries an Anthropic
    family prefix (``claude-`` / ``anthropic.`` / ``anthropic/``) — the latter covers
    Anthropic models exposed under a hosted surface (e.g. Bedrock's
    ``anthropic.claude-...``) whose bytes-on-the-wire are still Anthropic-shaped.
    """
    if model.provider == ModelProvider.ANTHROPIC:
        return True
    name = model.model_name.strip().lower()
    return name.startswith(_ANTHROPIC_NAME_PREFIXES)


def build_cli_gateway_env(
    *,
    gateway_base_url: str,
    auth_token_placeholder: str,
    requested_model: ModelRef,
) -> dict[str, str]:
    """Build the CLI gateway env map for ``requested_model``; refuse non-Anthropic models.

    Args:
        gateway_base_url: the gateway's OpenAI-compatible base URL (non-empty).
        auth_token_placeholder: a SECRET-FREE marker for the auth-token value (the
            real per-session virtual key is resolved by the launcher at point-of-use;
            this builder must never receive the raw key).
        requested_model: the model the CLI session will select — MUST be Anthropic-
            eligible (ADR-003 linchpin) or the call is refused fail-closed.

    Returns:
        The env map: base URL, the (placeholder) auth-token var, and discovery=1.

    Raises:
        NonAnthropicModelRefused: ``requested_model`` is not Anthropic-eligible.
        ValueError: an empty base URL or token placeholder (fail-closed; no defaults).
    """
    # fail-closed: an empty base URL / token marker under-specifies the egress — refuse
    # rather than build a half-configured env the CLI would silently mis-route on.
    if not gateway_base_url or not gateway_base_url.strip():
        raise ValueError("gateway_base_url must be non-empty")
    if not auth_token_placeholder or not auth_token_placeholder.strip():
        raise ValueError("auth_token_placeholder must be non-empty")

    # ADR-003 LINCHPIN (fail-closed): a CLI agent may select ONLY an Anthropic-family
    # model — a non-Anthropic model degrades CLI fidelity and is uncertified, so it is
    # refused here. Such traffic must take the programmatic ModelGatewayClient lane.
    if not is_anthropic_eligible(requested_model):
        raise NonAnthropicModelRefused(
            f"CLI agents may select Anthropic-family models only; "
            f"{requested_model.provider.value}:{requested_model.model_name} is refused "
            f"(use the programmatic gateway lane for non-Anthropic models)"
        )

    return {
        ANTHROPIC_BASE_URL_ENV: gateway_base_url,
        # secret-free: the VALUE here is a placeholder the launcher replaces with the
        # resolved virtual key at point-of-use; the raw key never enters this builder.
        ANTHROPIC_AUTH_TOKEN_ENV: auth_token_placeholder,
        GATEWAY_MODEL_DISCOVERY_ENV: "1",
    }
