"""Scoped pytest runner for the W2 knowledge mutation gate (dev-box helper).

mutmut splits its ``--runner`` string on whitespace, so an inline ``-o addopts=''``
override cannot be quoted safely. This tiny wrapper runs ONLY the knowledge tests
with coverage disabled (coverage is a separate gate) so each mutant evaluates in
~1s instead of re-running the whole 1500-test suite. It is a developer convenience,
not part of the runtime closure; the canonical gate is ``scripts/run_mutation_gate.py``.
"""

from __future__ import annotations

import sys

import pytest

if __name__ == "__main__":
    raise SystemExit(
        pytest.main(
            [
                "tests/knowledge",
                "-x",
                "-q",
                "-p",
                "no:cacheprovider",
                "--no-header",
                "-o",
                "addopts=",  # drop the global --cov gate for the mutation loop
                *sys.argv[1:],
            ]
        )
    )
