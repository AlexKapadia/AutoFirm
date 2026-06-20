"""Teeth-tests for FILE_OPENS_CLEAN — corruption and probe failure must fail closed.

Prove (CLAUDE.md §3.6 / §5.6) that :class:`FileOpensCleanCheck`:

* PASSES (empty tuple) only when the injected probe reports a clean open of a real
  file;
* BLOCKS when the probe reports ``(False, detail)`` — carrying ``detail`` verbatim
  in ``actual`` so the send-back targets the real defect;
* BLOCKS fail-closed when the probe RAISES — no exception escapes ``run`` and the
  finding names the error type;
* BLOCKS when the file is MISSING **without ever calling the probe** (verified with a
  spy that records every invocation) — a flaky probe can never resurrect a missing
  file into a pass;
* is DETERMINISTIC (N identical runs → byte-identical findings); and
* satisfies the runtime-checkable Protocols.

All probes here are synthetic fakes (no LibreOffice, no network); real files are
empty ``tmp_path`` files used only to exercise ``Path.exists()``. The injected-probe
design means the unit suite fully covers the source with fakes — the real
LibreOffice-headless probe lives behind the same :class:`FileOpenProbe` seam and is
exercised only in integration-tagged tests in the artifacts lane (see the report's
shared-file note: registering an ``integration`` pytest marker is a prerequisite).
"""

from __future__ import annotations

from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from autofirm.output_review.file_opens_clean_check import (
    FileOpenProbe,
    FileOpensCleanCheck,
)
from autofirm.output_review.review_check_protocol import ReviewCheck
from autofirm.output_review.review_finding_and_severity_contracts import (
    CheckSeverity,
    DefectClass,
    ReviewCheckId,
)
from autofirm.output_review.reviewable_artifact_contract import (
    ArtifactKind,
    ReviewableArtifact,
)


class _SpyProbe:
    """A probe that records every call and returns a pre-programmed verdict.

    The recorded ``calls`` let a test ASSERT the probe was (or was not) consulted —
    the only reliable way to prove the missing-file path short-circuits before any
    open is attempted.
    """

    def __init__(self, opens_clean: bool, detail: str) -> None:
        self._opens_clean = opens_clean
        self._detail = detail
        self.calls: list[tuple[Path, ArtifactKind]] = []

    def probe(self, path: Path, kind: ArtifactKind) -> tuple[bool, str]:
        self.calls.append((path, kind))
        return (self._opens_clean, self._detail)


class _RaisingProbe:
    """A probe that always raises, to drive the fail-closed exception path."""

    def __init__(self, exc: Exception) -> None:
        self._exc = exc
        self.calls = 0

    def probe(self, path: Path, kind: ArtifactKind) -> tuple[bool, str]:
        self.calls += 1
        raise self._exc


def _real_file(tmp_path: Path, name: str = "artifact.xlsx") -> Path:
    """Create a real (empty) file so ``Path.exists()`` is True for probe-path tests."""
    target = tmp_path / name
    target.write_bytes(b"")  # contents are irrelevant: the fake probe decides validity
    return target


def _artifact(path: Path, kind: ArtifactKind = ArtifactKind.FINANCIAL_MODEL) -> (
    ReviewableArtifact
):
    return ReviewableArtifact(artifact_ref="ref-1", kind=kind, path=path)


def test_check_satisfies_review_check_protocol() -> None:
    check = FileOpensCleanCheck(_SpyProbe(opens_clean=True, detail=""))
    assert isinstance(check, ReviewCheck)
    assert check.id is ReviewCheckId.FILE_OPENS_CLEAN


def test_file_open_probe_is_runtime_checkable() -> None:
    assert isinstance(_SpyProbe(opens_clean=True, detail=""), FileOpenProbe)
    # A bare object with no `probe` method must NOT pass the structural check.
    assert not isinstance(object(), FileOpenProbe)


def test_clean_open_on_real_file_passes_empty(tmp_path: Path) -> None:
    spy = _SpyProbe(opens_clean=True, detail="")
    check = FileOpensCleanCheck(spy)
    path = _real_file(tmp_path)
    assert check.run(_artifact(path)) == ()
    # The probe WAS consulted, with the artifact's own path + kind.
    assert spy.calls == [(path, ArtifactKind.FINANCIAL_MODEL)]


@pytest.mark.parametrize(
    "kind",
    [ArtifactKind.FINANCIAL_MODEL, ArtifactKind.SLIDE_DECK, ArtifactKind.BUSINESS_DOCUMENT],
)
def test_clean_open_passes_for_every_kind(tmp_path: Path, kind: ArtifactKind) -> None:
    # Applies to ALL kinds: a clean open passes regardless of deliverable type.
    check = FileOpensCleanCheck(_SpyProbe(opens_clean=True, detail=""))
    assert check.run(_artifact(_real_file(tmp_path), kind=kind)) == ()


def test_corrupt_open_blocks_and_carries_detail(tmp_path: Path) -> None:
    spy = _SpyProbe(opens_clean=False, detail="needs repair")
    check = FileOpensCleanCheck(spy)
    path = _real_file(tmp_path)

    findings = check.run(_artifact(path))

    assert len(findings) == 1
    finding = findings[0]
    assert finding.check_id is ReviewCheckId.FILE_OPENS_CLEAN
    assert finding.severity is CheckSeverity.BLOCKING
    assert finding.defect_class is DefectClass.MECHANICAL
    assert finding.message == "artifact does not open clean"
    assert finding.locator == str(path)
    assert finding.actual == "needs repair"  # probe detail surfaced verbatim
    assert finding.expected is None


def test_corrupt_detail_not_confused_with_clean_message(tmp_path: Path) -> None:
    # Boundary: a corrupt verdict must NEVER reuse the missing-file message/marker.
    check = FileOpensCleanCheck(_SpyProbe(opens_clean=False, detail="bad zip header"))
    finding = check.run(_artifact(_real_file(tmp_path)))[0]
    assert finding.message != "artifact file missing"
    assert finding.actual != "<file not found>"


@pytest.mark.parametrize(
    "exc",
    [
        RuntimeError("renderer crashed"),
        TimeoutError("probe timed out"),
        OSError("soffice not found"),
        ValueError("garbage in, garbage out"),
    ],
)
def test_probe_exception_blocks_fail_closed(tmp_path: Path, exc: Exception) -> None:
    check = FileOpensCleanCheck(_RaisingProbe(exc))
    path = _real_file(tmp_path)

    # The whole point: run() swallows the exception and converts it to a finding.
    findings = check.run(_artifact(path))

    assert len(findings) == 1
    finding = findings[0]
    assert finding.severity is CheckSeverity.BLOCKING
    assert finding.defect_class is DefectClass.MECHANICAL
    # message names the concrete error TYPE (so triage knows what failed)...
    assert type(exc).__name__ in finding.message
    assert finding.message.startswith("file-open probe raised ")
    # ...and actual carries a bounded repr summary of the error.
    assert finding.actual is not None
    assert str(exc) in finding.actual
    assert len(finding.actual) <= 500
    assert finding.locator == str(path)


def test_probe_exception_repr_is_truncated(tmp_path: Path) -> None:
    # Boundary: a pathologically long error message is bounded in `actual`.
    check = FileOpensCleanCheck(_RaisingProbe(RuntimeError("x" * 5000)))
    finding = check.run(_artifact(_real_file(tmp_path)))[0]
    assert finding.actual is not None
    assert len(finding.actual) == 500  # repr(exc)[:500]


def test_missing_file_blocks_without_calling_probe(tmp_path: Path) -> None:
    spy = _SpyProbe(opens_clean=True, detail="")  # would PASS if ever consulted
    check = FileOpensCleanCheck(spy)
    missing = tmp_path / "never_built.xlsx"  # never created
    assert not missing.exists()

    findings = check.run(_artifact(missing))

    assert len(findings) == 1
    finding = findings[0]
    assert finding.severity is CheckSeverity.BLOCKING
    assert finding.defect_class is DefectClass.MECHANICAL
    assert finding.message == "artifact file missing"
    assert finding.actual == "<file not found>"
    assert finding.locator == str(missing)
    # The load-bearing assertion: the probe was NEVER consulted (fail-closed
    # short-circuit), so a clean-reporting probe could not have rescued it.
    assert spy.calls == []


def test_missing_file_blocks_even_with_raising_probe(tmp_path: Path) -> None:
    # Even a probe that WOULD raise is never reached on the missing-file path.
    raising = _RaisingProbe(RuntimeError("should never be called"))
    check = FileOpensCleanCheck(raising)
    findings = check.run(_artifact(tmp_path / "absent.pptx"))
    assert len(findings) == 1
    assert findings[0].message == "artifact file missing"
    assert raising.calls == 0


@settings(max_examples=300)
@given(
    detail=st.text(
        alphabet=st.characters(
            # Malformed bytes / control chars / unicode the renderer might emit.
            codec="utf-8",
            categories=["Cc", "Cf", "Cs", "Co", "Ll", "Lu", "Nd", "Po", "Zs"],
        ),
        max_size=400,
    ),
    kind=st.sampled_from(list(ArtifactKind)),
)
def test_fuzz_corrupt_detail_always_one_blocking_finding(
    tmp_path_factory: pytest.TempPathFactory, detail: str, kind: ArtifactKind
) -> None:
    """Whatever garbage the probe's detail string is, run() blocks exactly once."""
    path = tmp_path_factory.mktemp("fuzz") / "a.bin"
    path.write_bytes(b"")
    check = FileOpensCleanCheck(_SpyProbe(opens_clean=False, detail=detail))

    findings = check.run(_artifact(path, kind=kind))

    assert len(findings) == 1
    finding = findings[0]
    assert finding.severity is CheckSeverity.BLOCKING
    assert finding.defect_class is DefectClass.MECHANICAL
    assert finding.message == "artifact does not open clean"
    # The (possibly blank/garbage) detail rides through to actual unchanged — but the
    # message and locator (the validated, non-blank fields) are always well-formed.
    assert finding.actual == detail
    assert finding.message and finding.locator


@settings(max_examples=100)
@given(detail=st.sampled_from(["", "   ", "\n", "\t\t", "\x00", "  needs repair  "]))
def test_fuzz_blank_or_whitespace_detail_still_blocks(
    tmp_path_factory: pytest.TempPathFactory, detail: str
) -> None:
    # Even an EMPTY/whitespace detail (a misbehaving probe) yields a valid finding:
    # message + locator are non-blank, so ReviewFinding construction never fails.
    path = tmp_path_factory.mktemp("blank") / "a.bin"
    path.write_bytes(b"")
    check = FileOpensCleanCheck(_SpyProbe(opens_clean=False, detail=detail))
    findings = check.run(_artifact(path))
    assert len(findings) == 1
    assert findings[0].message == "artifact does not open clean"


@pytest.mark.parametrize(
    ("opens_clean", "detail"),
    [(True, ""), (False, "needs repair")],
)
def test_determinism_same_inputs_same_findings(
    tmp_path: Path, opens_clean: bool, detail: str
) -> None:
    check = FileOpensCleanCheck(_SpyProbe(opens_clean=opens_clean, detail=detail))
    artifact = _artifact(_real_file(tmp_path))
    runs = [check.run(artifact) for _ in range(25)]
    first = runs[0]
    for other in runs[1:]:
        # Frozen pydantic models compare by value: identical inputs -> identical out.
        assert other == first


def test_determinism_missing_file_path(tmp_path: Path) -> None:
    check = FileOpensCleanCheck(_SpyProbe(opens_clean=True, detail=""))
    artifact = _artifact(tmp_path / "absent.docx")
    runs = [check.run(artifact) for _ in range(25)]
    assert all(r == runs[0] for r in runs[1:])
