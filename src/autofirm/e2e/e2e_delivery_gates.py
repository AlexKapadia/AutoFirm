"""Factory: wire the REAL output-review gate + release authority for the e2e run.

What this does
--------------
Provides :func:`build_e2e_delivery_gates`, the one place the end-to-end validation
constructs the two gates a human-facing deliverable must clear before it is filed:

* an :class:`~autofirm.output_review.output_review_gate.OutputReviewGate` (the seven
  deterministic-floor checks), built with the REAL stdlib OOXML
  :class:`~autofirm.e2e.zipfile_ooxml_file_open_probe.ZipfileOoxmlFileOpenProbe`
  injected into FILE_OPENS_CLEAN, and
* a :class:`~autofirm.output_review.release_decision_gate.ReleaseDecisionGate` (the
  release authority), writing through an append-only
  :class:`~autofirm.e2e.in_memory_release_audit_sink.InMemoryReleaseAuditSink`.

Both share one DETERMINISTIC clock pinned to the build's founding epoch, so every
verdict and decision the validation produces is reproducible (CLAUDE.md §3.11) —
two runs over the same corpus yield byte-identical timestamps.

Why it exists / where it sits
-----------------------------
The validation has two delivery paths (the founding charter at build time, the
investor update at operate time). Both must gate through the SAME real machinery,
so this factory centralises the wiring (probe, clock, sink) and the call sites just
thread the returned pair — no call site re-wires (or mis-wires) the gate itself.

Security / compliance invariants upheld (CLAUDE.md §5.6, §3.11)
--------------------------------------------------------------
* **Real probe, not a permissive fake:** FILE_OPENS_CLEAN reads the actual bytes,
  so a corrupt deliverable genuinely blocks.
* **Audited releases:** every decision is written through the append-only sink, so a
  release that cannot be recorded fails closed (no unaudited delivery).
* **Deterministic clock (never now()):** both gates take the founding-epoch clock,
  so the validation is reproducible.
"""

from __future__ import annotations

from datetime import datetime
from typing import NamedTuple

from autofirm.e2e.in_memory_release_audit_sink import InMemoryReleaseAuditSink
from autofirm.e2e.zipfile_ooxml_file_open_probe import ZipfileOoxmlFileOpenProbe
from autofirm.output_review.default_output_review_gate_factory import (
    build_default_output_review_gate,
)
from autofirm.output_review.output_review_gate import OutputReviewGate
from autofirm.output_review.release_decision_gate import ReleaseDecisionGate

__all__ = ["E2eDeliveryGates", "build_e2e_delivery_gates"]


class E2eDeliveryGates(NamedTuple):
    """The review gate + release authority a deliverable clears before filing.

    A named pair (tuple-unpackable AND attribute-accessible) so call sites can read
    ``gates.review_gate`` / ``gates.release_gate`` and the harness can thread one
    value through build + operate.

    Attributes:
        review_gate: The composed output-review gate (seven floor checks).
        release_gate: The release authority that audits + authorises a decision.
    """

    review_gate: OutputReviewGate
    release_gate: ReleaseDecisionGate


def build_e2e_delivery_gates() -> E2eDeliveryGates:
    """Construct the real review + release gates on the deterministic founding clock.

    Returns:
        The :class:`E2eDeliveryGates` pair: a gate composed with the REAL OOXML
        file-open probe and a release authority backed by an append-only in-memory
        audit sink, both stamped from the founding-epoch clock.
    """
    # Imported lazily: ``company_build_flow`` imports this factory, so importing its
    # FOUNDING_EPOCH at module top would form a cycle. The constant is the single
    # source of truth for the build's deterministic instant (CLAUDE.md §3.11).
    from autofirm.e2e.company_build_flow import FOUNDING_EPOCH  # noqa: PLC0415

    def founding_clock() -> datetime:
        """Return the fixed founding instant — the injected, never-now() time source."""
        return FOUNDING_EPOCH

    review_gate = build_default_output_review_gate(ZipfileOoxmlFileOpenProbe(), founding_clock)
    release_gate = ReleaseDecisionGate(InMemoryReleaseAuditSink(), founding_clock)
    return E2eDeliveryGates(review_gate=review_gate, release_gate=release_gate)
