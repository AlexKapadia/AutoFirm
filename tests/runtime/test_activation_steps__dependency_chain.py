"""Tests pinning the concrete activation step DAG returned by ``activation_steps()``.

The ``_FactStep`` value type's frozen-ness and id/requires/criticality PROPERTIES are covered
by the unit tests in ``test_activation_commands__up_idempotent_degraded_never_blocks.py``.
What those do NOT cover is the actual DAG WIRING in ``activation_steps()`` itself: the literal
``requires`` EDGES (venv -> deps -> package -> state -> smoke). Dropping an edge there (e.g.
``("venv.present",) -> ()``) survived the existing suite because nothing asserted the chain.
This module closes that gap with a boundary-exact pin of the whole chain (CLAUDE.md §3.6).
"""

from __future__ import annotations

from autofirm.bootstrap.bootstrap_step_contract import Criticality
from autofirm.runtime.activation_bootstrap_steps import activation_steps

# The activation DAG ``autofirm up`` converges before composing the platform, pinned EXACTLY as
# (id, requires, criticality). Dropping/altering any ``requires`` edge in ``activation_steps()``
# flips this tuple and is caught; the chain is a real ordering invariant, not a fixture value.
_EXPECTED_DAG: tuple[tuple[str, tuple[str, ...], Criticality], ...] = (
    ("venv.present", (), Criticality.REQUIRED),
    ("deps.installed", ("venv.present",), Criticality.REQUIRED),
    ("package.importable", ("deps.installed",), Criticality.REQUIRED),
    ("state.dir", ("package.importable",), Criticality.REQUIRED),
    ("smoke.composed", ("state.dir",), Criticality.REQUIRED),
)


def test_activation_steps__are_the_exact_dependency_chain() -> None:
    """``activation_steps()`` wires the EXACT venv->deps->package->state->smoke edge chain.

    Kills the dropped-/rewired-edge mutants in the step LIST (e.g. removing ``deps.installed``'s
    ``("venv.present",)`` requirement), which the ``_FactStep`` property unit tests cannot catch
    because they construct steps directly rather than reading the wired DAG.
    """
    actual = tuple((s.id, s.requires, s.criticality) for s in activation_steps())
    assert actual == _EXPECTED_DAG


def test_activation_steps__exactly_one_root_the_rest_chain_to_existing_steps() -> None:
    """Exactly one rootless step (``venv.present``); every other edge points at a real step.

    A dropped edge turns a non-root step into a second root; a rewired edge points outside the
    set. Both are caught: exactly one step has no ``requires`` and every requirement resolves.
    """
    steps = activation_steps()
    ids = {s.id for s in steps}
    roots = [s.id for s in steps if not s.requires]
    assert roots == ["venv.present"]  # a dropped edge would add a spurious second root
    for step in steps:
        for req in step.requires:
            assert req in ids  # no dangling/rewired requirement
