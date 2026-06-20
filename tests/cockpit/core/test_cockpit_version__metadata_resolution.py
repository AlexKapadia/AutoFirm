"""Behaviour tests for ``cockpit_version`` — exact metadata resolution + fail-soft sentinel.

These prove the version path is correct AND has teeth: the returned string must equal the
installed distribution version *exactly* (not merely "looks like a version"), the function
must be deterministic across repeated calls, and the uninstalled fallback must return the
documented sentinel rather than propagating ``PackageNotFoundError``. The fallback is
exercised by injecting the exception at the metadata seam — no reliance on an actually-
missing install.
"""

from importlib import metadata

import pytest

from autofirm.cockpit.core import cockpit_version as version_module
from autofirm.cockpit.core.cockpit_version import (
    _DISTRIBUTION_NAME,
    _UNINSTALLED_SENTINEL,
    cockpit_version,
)


def test_returns_installed_distribution_version_exactly() -> None:
    # The cockpit version IS the autofirm distribution version — byte-for-byte equal, not a
    # loose prefix/contains check (a mutated wrong distribution name would slip past that).
    assert cockpit_version() == metadata.version("autofirm")


def test_resolves_against_the_autofirm_distribution_name() -> None:
    # Pin the source of truth: kills a mutant that swaps the distribution name to something
    # else that happens to also be installed.
    assert _DISTRIBUTION_NAME == "autofirm"
    assert cockpit_version() == metadata.version(_DISTRIBUTION_NAME)


def test_is_deterministic_across_repeated_calls() -> None:
    # Same input (no input) -> identical output every time; the function holds no state.
    results = {cockpit_version() for _ in range(25)}
    assert len(results) == 1


def test_returns_non_empty_string() -> None:
    result = cockpit_version()
    assert isinstance(result, str)
    assert result  # non-empty: the `version` path must always print something usable


def test_falls_back_to_sentinel_when_distribution_is_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Force the uninstalled-source-tree branch by making metadata lookup raise. The function
    # must swallow it and return the sentinel — never re-raise to the caller.
    def _raise_not_found(_name: str) -> str:
        raise metadata.PackageNotFoundError(_name)

    monkeypatch.setattr(version_module.metadata, "version", _raise_not_found)
    assert cockpit_version() == _UNINSTALLED_SENTINEL


def test_sentinel_is_a_clearly_non_release_marker() -> None:
    # The fallback must not masquerade as a real release version (kills a mutant that makes
    # the sentinel a plausible number like "1.0.0").
    assert _UNINSTALLED_SENTINEL == "0+unknown"
    assert "unknown" in _UNINSTALLED_SENTINEL


def test_does_not_swallow_unrelated_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    # Fail-closed boundary: only PackageNotFoundError is the soft-fallback case. Any other
    # error (e.g. a corrupt metadata store raising RuntimeError) must propagate, not be
    # silently masked as the sentinel.
    def _raise_runtime(_name: str) -> str:
        raise RuntimeError("corrupt metadata store")

    monkeypatch.setattr(version_module.metadata, "version", _raise_runtime)
    with pytest.raises(RuntimeError):
        cockpit_version()
