"""The typed, frozen platform configuration: resolved once at the CLI edge from env only.

What this does
--------------
Defines :class:`PlatformConfig` — the single typed value object the composition root reads
to decide which capabilities to bind live vs degraded. It records which provider keys are
present, the gateway base URL, filesystem paths, and feature flags. It is resolved ONCE at
the CLI edge (via :meth:`PlatformConfig.from_environment`) so ``import autofirm`` stays
side-effect-free (no import-time env reads — 12-Factor III).

Why it exists / where it sits
-----------------------------
This is the seam between the untrusted outside world (environment, secret manager) and the
deterministic composition root. The root never reads ``os.environ`` itself; it takes a
fully-resolved, frozen :class:`PlatformConfig`, so the whole graph is reproducible in tests
by passing a synthetic config (no monkeypatching of globals).

Security / compliance invariants upheld
---------------------------------------
* **Secrets via environment only (§5.6):** the config records the *presence* of a provider
  key (a bool), NEVER the key value itself — so a :class:`PlatformConfig` is safe to log,
  print in ``status``, and assert on in tests. The real secret is fetched lazily through the
  credential broker at use time, never stored here.
* **No secrets in the repo (§5.6):** ``from_environment`` reads names from the environment;
  there are no hard-coded keys or magic constants.
* **Frozen / immutable:** once resolved, the config cannot be mutated mid-run, so the wired
  graph always reflects exactly the environment that was observed at activation.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

# The default OpenAI-compatible gateway base URL the model-gateway capability binds against
# when the environment does not override it. A non-secret, non-magic default (a real local
# gateway address), overridable per deployment via ``AUTOFIRM_GATEWAY_URL``.
DEFAULT_GATEWAY_URL = "http://localhost:4000"

# The environment variable names the config reads. Names only — never values — live here.
_GATEWAY_URL_VAR = "AUTOFIRM_GATEWAY_URL"
_PROVIDER_KEY_VARS: Mapping[str, str] = {
    "anthropic": "ANTHROPIC_API_KEY",  # presence enables the anthropic provider capability
}


@dataclass(frozen=True)
class PlatformConfig:
    """Resolved, frozen activation configuration (presence flags + paths, never secrets).

    Args:
        present_providers: The set of provider ids whose API key was present in the
            environment at resolution time (e.g. ``{"anthropic"}``). Drives degrade-vs-bind.
        gateway_url: The OpenAI-compatible gateway base URL the model capability targets.
        state_dir: The directory the bootstrap ledger and durable state live under.
        embedding_enabled: Whether the semantic-embedding backend should be bound (an
            OPTIONAL capability — degrades cleanly when False).
        analysis_enabled: Whether analysis/plotting capabilities are available (OPTIONAL;
            kept out of the runtime import closure regardless — ADR-001 §5).
    """

    present_providers: frozenset[str] = frozenset()
    gateway_url: str = DEFAULT_GATEWAY_URL
    state_dir: Path = field(default_factory=lambda: Path(".autofirm"))
    embedding_enabled: bool = True
    analysis_enabled: bool = False

    def has_provider(self, provider: str) -> bool:
        """Return True iff ``provider``'s API key was present at resolution (case-sensitive id)."""
        return provider in self.present_providers

    @classmethod
    def from_environment(cls, environ: Mapping[str, str]) -> PlatformConfig:
        """Resolve a config from an environment mapping (the ONLY place env is read).

        Records only the *presence* of each known provider key (never the value), the
        gateway URL (with a safe default), and the state directory. Passing ``os.environ``
        here at the CLI edge keeps every other module free of import-time env reads.

        Args:
            environ: The environment mapping (``os.environ`` at the edge; a synthetic dict
                in tests — no real keys required for the no-secrets path).

        Returns:
            A frozen :class:`PlatformConfig`.
        """
        present = frozenset(
            provider
            for provider, var in _PROVIDER_KEY_VARS.items()
            # presence == a non-blank value: a set-but-empty key is treated as ABSENT
            # (fail-closed) so a blank env var cannot masquerade as a real credential.
            if environ.get(var, "").strip()
        )
        gateway_url = environ.get(_GATEWAY_URL_VAR, "").strip() or DEFAULT_GATEWAY_URL
        state_dir_raw = environ.get("AUTOFIRM_STATE_DIR", "").strip()
        state_dir = Path(state_dir_raw) if state_dir_raw else Path(".autofirm")
        return cls(
            present_providers=present,
            gateway_url=gateway_url,
            state_dir=state_dir,
        )
