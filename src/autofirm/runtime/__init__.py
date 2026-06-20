"""The activation / composition layer (B7): the ONE place the platform is turned on.

This package is the cure for fragmentation. It sits at the TOP of the import graph: it
imports and wires every other ``autofirm`` package into one cohesive
:class:`~autofirm.runtime.platform_runtime.Platform`, supervises its long-lived loops, proves
it serves with a readiness self-test, and exposes the ``autofirm`` CLI (``up`` / ``status`` /
``doctor`` / ``down``). Nothing else in the codebase news-up cross-package collaborators —
:func:`~autofirm.runtime.platform_composition_root.build_platform` is the single composition
site (Pure DI, no container).

Layering / import-linter
------------------------
``runtime`` may import the engine packages; the engine packages must NEVER import ``runtime``
(it stays at the top of the graph, no cycles). Typer/Click are imported ONLY by
:mod:`autofirm.runtime.cli_entrypoint` (the CLI edge), so the deterministic core never
depends on a CLI framework (design §7).
"""

from __future__ import annotations

from autofirm.runtime.platform_composition_root import build_platform
from autofirm.runtime.platform_config import PlatformConfig
from autofirm.runtime.platform_readiness_selftest import (
    ReadinessGrade,
    ReadinessResult,
    run_readiness_selftest,
)
from autofirm.runtime.platform_runtime import Platform, WiredCapability
from autofirm.runtime.platform_supervisor import PlatformSupervisor

__all__ = [
    "Platform",
    "PlatformConfig",
    "PlatformSupervisor",
    "ReadinessGrade",
    "ReadinessResult",
    "WiredCapability",
    "build_platform",
    "run_readiness_selftest",
]
