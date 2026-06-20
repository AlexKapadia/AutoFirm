"""Tests for PlatformConfig: env-only resolution, presence-not-value, blank-is-absent, defaults."""

from __future__ import annotations

from pathlib import Path

from autofirm.runtime.platform_config import DEFAULT_GATEWAY_URL, PlatformConfig


def test_from_environment__present_key_marks_provider_present_without_storing_value() -> None:
    """A set provider key marks the provider present — but the config stores NO key value."""
    config = PlatformConfig.from_environment({"ANTHROPIC_API_KEY": "sk-secret-value"})
    assert config.has_provider("anthropic")
    # The secret value must never appear anywhere on the (loggable) config object.
    assert "sk-secret-value" not in repr(config)


def test_from_environment__absent_key_marks_provider_absent() -> None:
    """With no provider key in the env, the provider is absent (drives degraded-binding)."""
    config = PlatformConfig.from_environment({})
    assert not config.has_provider("anthropic")
    assert config.present_providers == frozenset()


def test_from_environment__blank_key_is_treated_as_absent_fail_closed() -> None:
    """A set-but-blank key is ABSENT (fail-closed) — a blank env var cannot pose as a credential."""
    config = PlatformConfig.from_environment({"ANTHROPIC_API_KEY": "   "})
    assert not config.has_provider("anthropic")


def test_from_environment__gateway_url_defaults_when_unset() -> None:
    """An unset gateway URL falls back to the safe, non-secret default."""
    assert PlatformConfig.from_environment({}).gateway_url == DEFAULT_GATEWAY_URL


def test_from_environment__gateway_url_is_overridable() -> None:
    """A set gateway URL overrides the default."""
    config = PlatformConfig.from_environment({"AUTOFIRM_GATEWAY_URL": "http://gw:9000"})
    assert config.gateway_url == "http://gw:9000"


def test_from_environment__state_dir_defaults_and_overrides() -> None:
    """The state dir defaults to .autofirm and is overridable via the env."""
    assert PlatformConfig.from_environment({}).state_dir == Path(".autofirm")
    overridden = PlatformConfig.from_environment({"AUTOFIRM_STATE_DIR": "/tmp/af"})
    assert overridden.state_dir == Path("/tmp/af")


def test_config__is_frozen_immutable() -> None:
    """A resolved config is frozen — it cannot be mutated mid-run."""
    config = PlatformConfig.from_environment({})
    import dataclasses

    try:
        config.gateway_url = "mutated"  # type: ignore[misc]
    except dataclasses.FrozenInstanceError:
        return
    raise AssertionError("PlatformConfig must be frozen/immutable")


# ---------------------------------------------------------------------------
# Mutation-hardening (CLAUDE.md §3.6): pin the EXACT dataclass field DEFAULTS
# directly (constructing with no args), independent of from_environment, so a
# mutant changing any default value is caught. Also pin the module constant.
# ---------------------------------------------------------------------------


def test_default_gateway_url_constant_is_the_exact_local_address() -> None:
    """The default gateway URL constant is pinned byte-exact (kills string-default mutants)."""
    assert DEFAULT_GATEWAY_URL == "http://localhost:4000"


def test_platform_config__bare_construction_uses_the_documented_field_defaults() -> None:
    """A no-args PlatformConfig carries EXACTLY its documented field defaults (kills defaults).

    Exercises the dataclass field defaults themselves — a path ``from_environment`` does not
    take — so a mutant altering any default (the providers set, gateway URL, state dir, or the
    feature flags) is caught here even though the env-resolution path overrides some of them.
    """
    config = PlatformConfig()
    assert config.present_providers == frozenset()  # default: no providers present
    assert config.gateway_url == DEFAULT_GATEWAY_URL  # default sourced from the constant
    assert config.gateway_url == "http://localhost:4000"  # ... and that constant is exact
    assert config.state_dir == Path(".autofirm")  # default state directory
    assert config.embedding_enabled is True  # OPTIONAL embedding default-on
    assert config.analysis_enabled is False  # analysis default-OFF (kept out of runtime closure)
