"""The SPEC_ROUND_TRIP deterministic check: every spec value survives into the file.

What this does
--------------
Defines :class:`SpecRoundTripCheck`, the P1 deterministic-floor check that verifies a
built artifact actually carries what its originating spec declared. It compares two
by-value string maps the caller populates on the artifact's
:class:`~autofirm.output_review.reviewable_artifact_facts.SpecRoundTrip` bundle:

* ``declared_values`` — the spec truth (what the builder was *told* to render), and
* ``extracted_values`` — what was *re-read back* from the rendered artifact.

The two maps must be IDENTICAL. The check emits one BLOCKING
:class:`~autofirm.output_review.review_finding_and_severity_contracts.ReviewFinding`
per discrepancy — a declared key that vanished, a declared value that was altered, or
an unexpected extra key the spec never declared — and an empty tuple iff they match.

Why it exists / where it sits
-----------------------------
``SYNTHESIS.md`` §2.2/§3 makes round-tripping the spec one of the mechanical defences
of the deterministic floor: a title typo, a dropped figure, or a mangled label is a
MECHANICAL Panko-Halverson defect (``CHECK_DEFECT_CLASSES[SPEC_ROUND_TRIP]``) that an
independent re-read catches without any model judgement. It is a PURE function of the
by-value facts (plan §B.3) — no file IO, no clock, no randomness, no mutation — so the
gate (P2) composes it deterministically alongside its peers.

Security / compliance invariants upheld (CLAUDE.md §5.6, §3.11)
--------------------------------------------------------------
* **Fail closed on absent facts:** if the ``spec_round_trip`` bundle is ``None`` the
  check cannot verify anything, so it BLOCKS with an explicit finding rather than
  passing vacuously — a missing fact set must never read as "clean".
* **Applies to every kind:** the spec round-trip is meaningful for a model, a deck,
  AND a document, so the check declines no ``ArtifactKind`` (omission defence: no kind
  silently skips the check).
* **Deterministic ordering:** findings are emitted over the SORTED union of both key
  sets, so the output tuple is identical regardless of dict insertion order — a
  reproducible verdict (CLAUDE.md §3.11).
* **No PII:** findings carry the opaque string key as the locator and the synthetic
  declared/extracted scalars as ``expected``/``actual`` — never raw artifact bytes.
"""

from __future__ import annotations

from collections.abc import Mapping

from autofirm.output_review.review_finding_and_severity_contracts import (
    CheckSeverity,
    DefectClass,
    ReviewCheckId,
    ReviewFinding,
)
from autofirm.output_review.reviewable_artifact_contract import ReviewableArtifact

__all__ = ["SpecRoundTripCheck"]

# Sentinel rendered into ``expected``/``actual`` when one side has no value for a key.
# A literal marker (never a real value) so a send-back can distinguish "the value was
# wrong" from "the value was entirely missing / unexpectedly present".
_ABSENT = "<absent>"


class SpecRoundTripCheck:
    """Verify every declared spec value round-trips intact into the rendered artifact.

    Implements the :class:`~autofirm.output_review.review_check_protocol.ReviewCheck`
    Protocol (runtime-checkable): exposes :attr:`id` and a pure, deterministic
    :meth:`run`. The check holds no state and reads nothing but the artifact handed to
    ``run`` — so it can never consult a peer check's findings or the verdict
    (independence, plan §B.3).
    """

    @property
    def id(self) -> ReviewCheckId:
        """The closed-set id this check owns — its registry key."""
        return ReviewCheckId.SPEC_ROUND_TRIP

    def run(self, artifact: ReviewableArtifact) -> tuple[ReviewFinding, ...]:
        """Return one BLOCKING finding per round-trip discrepancy (empty == clean).

        Inputs
        ------
        * ``artifact`` — the by-value :class:`ReviewableArtifact`. Only its
          ``spec_round_trip`` bundle and ``artifact_ref`` are read; the check applies
          to every :class:`~autofirm.output_review.reviewable_artifact_contract.ArtifactKind`.

        Outputs
        -------
        An empty tuple iff ``declared_values`` and ``extracted_values`` are identical.
        Otherwise one BLOCKING / MECHANICAL finding per offending key, emitted over the
        SORTED union of both key sets (deterministic order), each locating the key and
        carrying the exact ``expected`` (spec) vs ``actual`` (artifact) mismatch.

        Failure modes
        -------------
        If ``spec_round_trip`` is ``None`` the facts are absent and nothing can be
        verified — the check returns a single BLOCKING finding located at the artifact
        ref rather than passing vacuously (fail-closed, CLAUDE.md §5.6).
        """
        facts = artifact.spec_round_trip
        if facts is None:
            # fail-closed: no round-trip facts means we CANNOT confirm the spec
            # survived — refuse with a blocking finding instead of a vacuous pass.
            return (
                ReviewFinding(
                    check_id=ReviewCheckId.SPEC_ROUND_TRIP,
                    severity=CheckSeverity.BLOCKING,
                    defect_class=DefectClass.MECHANICAL,
                    message="spec round-trip facts absent — cannot verify",
                    locator=artifact.artifact_ref,
                ),
            )

        return self._diff_findings(facts.declared_values, facts.extracted_values)

    @staticmethod
    def _diff_findings(
        declared: Mapping[str, str], extracted: Mapping[str, str]
    ) -> tuple[ReviewFinding, ...]:
        """Compare the two maps key-by-key over their sorted union.

        Iterating ``sorted(declared keys | extracted keys)`` makes the finding order a
        pure function of the data — independent of either dict's insertion order — so
        the same artifact always yields the identical findings tuple (determinism,
        CLAUDE.md §3.11). One finding is emitted per discrepancy; a key present and
        equal on both sides yields none.
        """
        findings: list[ReviewFinding] = []
        for key in sorted(declared.keys() | extracted.keys()):
            in_declared = key in declared
            in_extracted = key in extracted

            if in_declared and in_extracted:
                if declared[key] == extracted[key]:
                    continue  # value round-tripped intact — no defect for this key.
                # Declared key survived but its value was altered in the artifact.
                expected, actual = declared[key], extracted[key]
                message = "spec value altered in artifact"
            elif in_declared:
                # Declared key never made it into the rendered artifact (dropped).
                expected, actual = declared[key], _ABSENT
                message = "declared spec value missing from artifact"
            else:
                # Artifact carries a key the spec never declared (unexpected extra).
                expected, actual = _ABSENT, extracted[key]
                message = "artifact carries value not in spec"

            findings.append(
                ReviewFinding(
                    check_id=ReviewCheckId.SPEC_ROUND_TRIP,
                    severity=CheckSeverity.BLOCKING,
                    defect_class=DefectClass.MECHANICAL,
                    message=message,
                    locator=key,
                    expected=expected,
                    actual=actual,
                )
            )
        return tuple(findings)
