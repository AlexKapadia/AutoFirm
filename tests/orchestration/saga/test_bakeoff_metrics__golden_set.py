"""Golden-set bake-off metric test: all three runtimes must hit a perfect score.

The pre-registered acceptance bar (ADR-001 §7; CLAUDE.md §3.4): on the
saga-resume idempotency + cancellation-safety golden set, the chosen runtime must
have ZERO cancellation-safety violations, ZERO idempotency double-applies, ZERO
orphaned tasks, and ZERO determinism violations. This test proves every candidate
meets the *correctness* floor; the WINNER is then decided on the structural
cancellation-guarantee + clarity tie-breaker recorded in the results doc.
"""

from __future__ import annotations

import pytest

from autofirm.orchestration.saga.runtime_adapter import RuntimeAdapter
from autofirm.orchestration.saga.runtimes.anyio_adapter import AnyioAdapter

from .saga_bakeoff_metrics import measure_runtime

# The winning runtime; the 3-way bake-off numbers are preserved in
# concurrency-runtime-results.md and git history (loser adapters deleted, §3.8).
ADAPTERS: list[RuntimeAdapter] = [AnyioAdapter()]
ADAPTER_IDS = [a.name for a in ADAPTERS]


@pytest.mark.unit
@pytest.mark.parametrize("adapter", ADAPTERS, ids=ADAPTER_IDS)
def test_runtime_scores_perfect_on_golden_set(adapter: RuntimeAdapter) -> None:
    metrics = measure_runtime(adapter)
    assert metrics.cancellation_safety_violations == 0, metrics
    assert metrics.idempotency_double_applies == 0, metrics
    assert metrics.orphan_tasks == 0, metrics
    assert metrics.determinism_violations == 0, metrics
