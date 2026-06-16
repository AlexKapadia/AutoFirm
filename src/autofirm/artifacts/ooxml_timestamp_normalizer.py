"""Make a written OOXML package byte-deterministic by pinning its timestamps.

What this does
--------------
Rewrites an already-saved ``.xlsx`` / ``.docx`` package in place so its bytes do
not depend on wall-clock time: the ``dcterms:modified`` value in
``docProps/core.xml`` is forced to the fixed epoch, and every ZIP member's
modification date is normalised to a constant. The result is identical bytes for
identical content.

Why it exists / where it sits
-----------------------------
openpyxl and python-docx both overwrite ``modified`` to "now" *inside* their
``save()`` — there is no public option to disable it — so setting the property
beforehand is not enough. A post-save normalisation pass is the only library-
agnostic way to satisfy the determinism requirement (CLAUDE.md §3.6) without
forking the libraries. python-pptx does not stamp, so the deck builder does not
need this pass.

Security / compliance invariants upheld
---------------------------------------
The function only edits two fields (a timestamp value and ZIP member dates); it
never alters document content, and it rewrites atomically via a temp file so a
crash cannot leave a truncated package on disk (fail-safe write).
"""

from __future__ import annotations

import re
import zipfile
from pathlib import Path

from autofirm.artifacts.deterministic_document_properties import FIXED_TIMESTAMP

__all__ = ["normalize_ooxml_timestamps"]

# A constant ZIP member date (the DOS epoch lower bound 1980-01-01) so the
# archive's per-member modification times are build-independent.
_FIXED_ZIP_DATE = (1980, 1, 1, 0, 0, 0)
_CORE_PART = "docProps/core.xml"
_FIXED_MODIFIED = FIXED_TIMESTAMP.strftime("%Y-%m-%dT%H:%M:%SZ")
# Match the <dcterms:modified ...>VALUE</dcterms:modified> text content only.
_MODIFIED_RE = re.compile(rb"(<dcterms:modified[^>]*>)[^<]*(</dcterms:modified>)")


def normalize_ooxml_timestamps(package_path: Path) -> Path:
    """Rewrite ``package_path`` so its timestamps are fixed (byte-deterministic).

    Args:
        package_path: An existing OOXML (.xlsx/.docx) file to normalise in place.

    Returns:
        The same ``package_path`` (now timestamp-normalised).
    """
    with zipfile.ZipFile(package_path) as source:
        members = source.namelist()
        payloads = {name: source.read(name) for name in members}

    if _CORE_PART in payloads:
        # Force the modified field to the fixed epoch; the regex touches only the
        # modified value, leaving the (already-fixed) created value and all other
        # content untouched.
        payloads[_CORE_PART] = _MODIFIED_RE.sub(
            rb"\g<1>" + _FIXED_MODIFIED.encode("ascii") + rb"\g<2>",
            payloads[_CORE_PART],
        )

    # Write to a sibling temp file then replace, so an interrupted run cannot
    # leave a half-written package (fail-safe write).
    tmp_path = package_path.with_suffix(package_path.suffix + ".tmp")
    with zipfile.ZipFile(tmp_path, "w", zipfile.ZIP_DEFLATED) as out:
        for name in members:  # preserve original member order for stable bytes
            info = zipfile.ZipInfo(filename=name, date_time=_FIXED_ZIP_DATE)
            info.compress_type = zipfile.ZIP_DEFLATED
            out.writestr(info, payloads[name])
    tmp_path.replace(package_path)
    return package_path
