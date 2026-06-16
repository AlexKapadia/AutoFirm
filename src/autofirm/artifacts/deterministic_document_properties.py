"""Fixed OOXML core-property timestamps for reproducible artifacts.

What this does
--------------
Provides a single frozen ``created``/``modified`` timestamp that every builder
stamps into its OOXML core properties, plus a constant author. OOXML packages
(.xlsx/.pptx/.docx) embed creation/modification times in ``docProps/core.xml`` by
default; left unset they default to *now*, so two identical specs built a second
apart produce different bytes.

Why it exists / where it sits
-----------------------------
CLAUDE.md §3.6 requires determinism: identical inputs must yield an identical
artifact. Pinning the embedded timestamps to a fixed epoch removes the only
non-deterministic field the libraries inject, making the output byte-stable and
diff-able (institution-grade reproducibility) without touching any content.
"""

from __future__ import annotations

import datetime as _dt

__all__ = ["ARTIFACT_AUTHOR", "FIXED_TIMESTAMP"]

# A fixed, timezone-aware epoch stamped into every artifact's core properties so
# the package bytes do not depend on wall-clock time. The value itself is
# arbitrary; only its constancy matters (determinism — CLAUDE.md §3.6).
FIXED_TIMESTAMP = _dt.datetime(2024, 1, 1, 0, 0, 0, tzinfo=_dt.UTC)

# Constant author so the creator field is also build-independent.
ARTIFACT_AUTHOR = "AutoFirm"
