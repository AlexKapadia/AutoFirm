"""Scoped pytest runner for the output_review mutation gate (dev-box helper).

mutmut splits its ``runner`` string on whitespace, so an inline ``-o addopts=''``
override cannot be quoted safely. This tiny wrapper runs ONLY the test file(s)
named in the ``MUT_TESTS`` environment variable (space-separated), with coverage
disabled (coverage is a separate gate), so each mutant evaluates in ~1s instead
of re-running the whole repo suite. It is a developer convenience, not part of
the runtime closure; the canonical gate is ``scripts/run_mutation_gate.py``.

Why an env var rather than args: mutmut invokes ``config.test_command`` with no
extra arguments, so the per-module test selection must travel in the environment.
Forcing UTF-8 child I/O mirrors ``run_mutation_gate.py`` so a cp1252 console can
never crash a mutant evaluation on non-ASCII output.
"""

from __future__ import annotations

import os
import sys

import pytest

if __name__ == "__main__":
    os.environ.setdefault("PYTHONUTF8", "1")
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    mut_tests = os.environ.get("MUT_TESTS", "tests/output_review").split()
    rc = pytest.main(
        [
            *mut_tests,
            "-x",
            "-q",
            "-p",
            "no:cacheprovider",
            "--no-header",
            "-o",
            "addopts=",  # drop the global --cov gate for the mutation loop
            "-o",
            "pythonpath=src",
        ]
    )
    # Fail-closed exit-code normalisation (THE bug this fixes). mutmut grades a
    # mutant "killed" only when the runner returns exactly 1 (see mutmut/__init__.py
    # tests_pass: ``return returncode != 1``); ANY other code is read as "tests
    # passed -> survived". pytest returns 2 for a COLLECTION error -- exactly what a
    # mutant that breaks the module's import (an invalid pydantic config value, a
    # decorator on a non-existent field, an invalid model_validator mode, etc.)
    # produces. Such a mutant makes the whole suite fail to even load, so it is a
    # GENUINE kill, yet mutmut's default would mis-record it as a survivor. We
    # therefore map: clean pass (rc == 0) is the SOLE survival signal -> exit 0;
    # assertion failure (rc==1), collection/usage error (rc==2), internal error
    # (rc==3) all mean the suite did NOT cleanly pass under this mutant -> exit 1
    # so mutmut records a true kill.
    #
    # rc == 5 (NO TESTS COLLECTED) is the dangerous case the North Star flagged: a
    # mis-set MUT_TESTS that points at a path collecting zero tests must NEVER be
    # graded a kill, or every mutant would be falsely "killed" (a false-green gate
    # -- CLAUDE.md §3.6/§7.2 "never widen the killed-set"). We map rc==5 to exit 2:
    # NOT 1, so mutmut never records a kill; NOT 0, so it is not confused with a
    # genuine survival -- mutmut reads exit 2 as "survived", which surfaces EVERY
    # mutant as a survivor and FAILS the gate loudly, forcing the operator to fix
    # MUT_TESTS. Fail-closed: a runner that collected no tests proves nothing.
    raise SystemExit(0 if rc == 0 else (2 if rc == 5 else 1))
