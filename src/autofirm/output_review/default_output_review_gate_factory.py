"""Factory that wires the seven deterministic-floor checks into a default gate.

What this does
--------------
Provides :func:`build_default_output_review_gate`, the single place that constructs a
:class:`~autofirm.output_review.review_check_protocol.CheckRegistry`, registers the
SEVEN deterministic-floor checks (ACCOUNTING_IDENTITY, SPEC_ROUND_TRIP,
NUMERIC_RECOMPUTE, FILE_OPENS_CLEAN, FAST_LINT, IBCS_SUCCESS, VISUAL_INTEGRITY) in a
fixed registration order, and returns the composed
:class:`~autofirm.output_review.output_review_gate.OutputReviewGate`.

Why it exists / where it sits
-----------------------------
The gate is deliberately ignorant of *which* checks exist — it composes whatever the
registry holds (plan §B.3). This factory is the one component that knows the floor's
membership, so the deterministic floor is defined in exactly one place and the gate
stays a pure composer. ``FILE_OPENS_CLEAN`` is the only check that needs an external
collaborator (it reads bytes via a probe), so its :class:`FileOpenProbe` is INJECTED
here — unit callers pass a synthetic fake, integration callers a real renderer; the
factory never constructs a probe itself (network-free, CLAUDE.md §5.6).

Security / compliance invariants upheld (CLAUDE.md §5.6, §3.11)
--------------------------------------------------------------
* **Complete floor, fixed order:** all seven mandatory checks are registered, in a
  fixed order, so ``checks_run`` on the resulting verdict is stable and an omitted
  check is detectable (omission defence).
* **Fail-closed registration:** registration goes through the registry, which refuses
  duplicate ids — the floor can never silently shadow a mandatory check.
* **Injected probe / clock:** the only IO collaborator (the file-open probe) and the
  time source are injected, never constructed here, so the factory is pure and
  reproducible.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from autofirm.output_review.accounting_identity_check import AccountingIdentityCheck
from autofirm.output_review.fast_lint_check import FastLintCheck
from autofirm.output_review.file_opens_clean_check import FileOpensCleanCheck
from autofirm.output_review.ibcs_success_rubric_check import IbcsSuccessRubricCheck
from autofirm.output_review.numeric_recomputation_check import NumericRecomputationCheck
from autofirm.output_review.output_review_gate import OutputReviewGate
from autofirm.output_review.review_check_protocol import CheckRegistry
from autofirm.output_review.spec_artifact_round_trip_check import SpecRoundTripCheck
from autofirm.output_review.visual_integrity_lint_check import VisualIntegrityLintCheck

if TYPE_CHECKING:
    from collections.abc import Callable
    from datetime import datetime

    from autofirm.output_review.file_opens_clean_check import FileOpenProbe

__all__ = ["build_default_output_review_gate"]


def build_default_output_review_gate(
    file_open_probe: FileOpenProbe, clock: Callable[[], datetime]
) -> OutputReviewGate:
    """Construct the default gate with the seven floor checks registered in order.

    The registration order below is the order in which the resulting gate runs the
    checks and the order ``checks_run`` reports — keep it stable so verdicts are
    reproducible (CLAUDE.md §3.11).

    Args:
        file_open_probe: The :class:`FileOpenProbe` the FILE_OPENS_CLEAN check uses to
            test that a built file opens without repair. Injected — a synthetic fake
            in unit tests, a real renderer in integration.
        clock: Zero-argument callable returning the ``datetime`` stamped on verdicts.

    Returns:
        An :class:`OutputReviewGate` whose registry holds all seven floor checks.
    """
    registry = CheckRegistry()
    # Fixed registration order == run order == checks_run order (determinism).
    registry.register(AccountingIdentityCheck())
    registry.register(SpecRoundTripCheck())
    registry.register(NumericRecomputationCheck())
    # FILE_OPENS_CLEAN is the sole check with an IO collaborator — inject the probe.
    registry.register(FileOpensCleanCheck(file_open_probe))
    registry.register(FastLintCheck())
    registry.register(IbcsSuccessRubricCheck())
    registry.register(VisualIntegrityLintCheck())
    return OutputReviewGate(registry, clock)
