"""Resolve the operator cockpit's version string from installed package metadata.

The cockpit ships as part of the ``autofirm`` distribution, so its version is the
distribution version — read from installed metadata rather than duplicated as a literal,
which would be a second source of truth that silently drifts (cockpit-research/PLAN.md, the
``autofirm version`` subcommand in §3.2). This is the C0 trivial pure-logic module: it
gives the test / coverage / mutation machinery a real, deterministic function to chew on
while later gates add the substantive decision modules.

Pure and side-effect-free: it reads metadata and returns a string; it performs no I/O on
the event log, makes no network call, and holds no state.
"""

from __future__ import annotations

from importlib import metadata

# The distribution this package is published under. The cockpit is not a separate
# distribution — it lives inside ``autofirm`` — so its version is the autofirm version.
_DISTRIBUTION_NAME = "autofirm"

# Stable, documented fallback when the package is imported from a source tree that was
# never installed (no metadata). It is a sentinel, NOT a guessed version number: a real
# release always resolves the true version from metadata, so this never masquerades as one.
_UNINSTALLED_SENTINEL = "0+unknown"


def cockpit_version() -> str:
    """Return the operator cockpit's version string.

    Returns:
        The installed ``autofirm`` distribution version (e.g. ``"0.0.1"``) when metadata is
        available, otherwise the :data:`_UNINSTALLED_SENTINEL` (``"0+unknown"``) for an
        uninstalled source tree. The result is always a non-empty string.

    Failure modes:
        Never raises. A missing distribution (source tree without an editable/wheel install)
        resolves to the sentinel rather than propagating
        :class:`importlib.metadata.PackageNotFoundError` to the caller.
    """
    try:
        return metadata.version(_DISTRIBUTION_NAME)
    except metadata.PackageNotFoundError:
        # Fail soft to a clearly-non-release sentinel: an uninstalled source tree must still
        # report a usable version string rather than crash the `version` path.
        return _UNINSTALLED_SENTINEL
