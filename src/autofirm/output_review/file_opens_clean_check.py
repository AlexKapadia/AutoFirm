"""FILE_OPENS_CLEAN — the deterministic check that a built artifact opens un-corrupt.

What this does
--------------
Implements :class:`FileOpensCleanCheck`, the deterministic-floor check that proves a
built artifact (xlsx / pptx / docx / pdf) actually OPENS without repair — i.e. the
bytes on disk are valid OOXML/PDF, not a truncated or malformed file a human would
hit a "do you want to repair?" dialog on. It is the MECHANICAL-class detector in the
floor (``CHECK_DEFECT_CLASSES[FILE_OPENS_CLEAN] == {MECHANICAL}``).

Unlike the other floor checks this one has **no by-value fact bundle**: validity is a
property of the bytes, not of recomputed scalars, so it must read ``artifact.path``.
To keep the check PURE and unit-testable without shelling out, the actual open is
delegated to an INJECTED :class:`FileOpenProbe` (P0 decision): unit tests pass a
synthetic fake probe; only integration-tagged tests wire a real LibreOffice-headless
probe. The check itself never imports a renderer and never touches the network.

Why it exists / where it sits
-----------------------------
``docs/research/B16-output-review-and-verification/SYNTHESIS.md`` §2.2/§3 makes
"the file opens clean" part of the deterministic floor: a corrupt deliverable is the
most basic, most embarrassing defect to ship to a human, and it is mechanically
detectable. The check sits beside the other P1 checks behind the
:class:`~autofirm.output_review.review_check_protocol.ReviewCheck` Protocol and is
composed by the P2 gate through the registry.

Security / compliance invariants upheld (CLAUDE.md §5.6)
-------------------------------------------------------
* **Fail closed on a missing file:** if ``artifact.path`` does not exist the check
  blocks (the probe is never even consulted) — an absent artifact is a defect, not a
  pass.
* **Fail closed on a raising probe:** ANY exception from the probe (renderer crash,
  timeout, OS error) becomes a BLOCKING finding — uncertainty about validity is
  treated as invalidity, never waved through. No exception escapes ``run``.
* **No raw content in findings:** findings carry the path locator and a short probe
  detail / error summary only — never the artifact bytes (hashes-not-PII, T1).
* **Deterministic:** given a deterministic probe, the same artifact always yields the
  same findings (the Protocol's purity contract — CLAUDE.md §3.11).
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

from autofirm.output_review.review_finding_and_severity_contracts import (
    CheckSeverity,
    DefectClass,
    ReviewCheckId,
    ReviewFinding,
)
from autofirm.output_review.reviewable_artifact_contract import (
    ArtifactKind,
    ReviewableArtifact,
)

__all__ = [
    "FileOpenProbe",
    "FileOpensCleanCheck",
]


@runtime_checkable
class FileOpenProbe(Protocol):
    """A swappable way to test whether an artifact file opens without repair.

    The seam that keeps :class:`FileOpensCleanCheck` pure and unit-testable: unit
    tests inject a synthetic fake, integration-tagged tests inject a real
    LibreOffice-headless probe. Runtime-checkable so the wiring layer can assert a
    candidate object satisfies the contract before trusting it.
    """

    def probe(self, path: Path, kind: ArtifactKind) -> tuple[bool, str]:
        """Attempt to open ``path`` as ``kind`` and report the outcome.

        Args:
            path: On-disk location of the built artifact (guaranteed to exist by the
                caller — the check checks existence before probing).
            kind: The :class:`ArtifactKind`, so a probe can pick the right opener.

        Returns:
            ``(opens_clean, detail)``: ``opens_clean`` is ``True`` when the file
            opens with no repair; ``detail`` explains the failure when it is
            ``False`` (and is empty when clean).
        """
        ...


class FileOpensCleanCheck:
    """Deterministic floor check: the built artifact must OPEN without repair.

    Applies to every :class:`ArtifactKind` (a corrupt file is a defect whatever the
    deliverable). The real open is delegated to an injected :class:`FileOpenProbe`,
    so the check stays a pure, deterministic function of ``(artifact, probe)`` and
    unit tests never shell out. Satisfies the runtime-checkable
    :class:`~autofirm.output_review.review_check_protocol.ReviewCheck` Protocol.
    """

    def __init__(self, probe: FileOpenProbe) -> None:
        """Store the injected file-open probe.

        Args:
            probe: The :class:`FileOpenProbe` used to test whether a file opens. In
                unit tests this is a synthetic fake; in integration it is a real
                renderer. The check never constructs a probe itself (dependency
                injection keeps it pure and network-free).
        """
        self._probe = probe

    @property
    def id(self) -> ReviewCheckId:
        """The closed-set id this check owns (its registry key)."""
        return ReviewCheckId.FILE_OPENS_CLEAN

    def run(self, artifact: ReviewableArtifact) -> tuple[ReviewFinding, ...]:
        """Return a BLOCKING finding unless the artifact opens clean (else empty).

        Fail-closed in three ways (CLAUDE.md §5.6): a missing file blocks without
        consulting the probe; a raising probe blocks (uncertainty == invalid); a
        ``False`` probe result blocks with the probe's own failure detail. A clean
        open is the only path that returns ``()``.
        """
        path = artifact.path
        # fail-closed: an artifact whose file is absent cannot have been delivered
        # cleanly — block immediately and never consult the probe (so a flaky probe
        # cannot turn a missing file into a pass).
        if not path.exists():
            return (
                self._blocking(
                    path=path,
                    message="artifact file missing",
                    actual="<file not found>",
                ),
            )

        try:
            opens_clean, detail = self._probe.probe(path, artifact.kind)
        except Exception as exc:  # fail-closed: ANY probe failure blocks delivery
            # fail-closed: a renderer crash / timeout / OS error leaves validity
            # UNKNOWN — treat unknown as invalid rather than risk shipping a corrupt
            # file. The message names the error type; actual is a bounded repr.
            return (
                self._blocking(
                    path=path,
                    message=f"file-open probe raised {type(exc).__name__}",
                    actual=repr(exc)[:500],
                ),
            )

        if opens_clean:
            return ()
        # fail-closed: the probe says the file does not open clean — block and carry
        # the probe's own explanation so the send-back targets the real defect.
        return (
            self._blocking(
                path=path,
                message="artifact does not open clean",
                actual=detail,
            ),
        )

    def _blocking(self, *, path: Path, message: str, actual: str) -> ReviewFinding:
        """Build the one BLOCKING, MECHANICAL finding this check ever raises.

        Args:
            path: The artifact path, used as the (always non-blank) locator.
            message: Human-readable explanation of why the file is not clean.
            actual: The observed detail (probe message / error summary / not-found
                marker); ``expected`` is intentionally omitted because "opens clean"
                has no numeric counterpart.
        """
        return ReviewFinding(
            check_id=ReviewCheckId.FILE_OPENS_CLEAN,
            severity=CheckSeverity.BLOCKING,  # fail-closed default — a corrupt file blocks
            defect_class=DefectClass.MECHANICAL,
            message=message,
            locator=str(path),
            actual=actual,
        )
