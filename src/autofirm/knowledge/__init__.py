"""W2 shared-knowledge / coordination substrate (extends the A4 memory plane).

Lets HETEROGENEOUS agents (different model providers) share context reliably via
a single bi-temporal store behind a Protocol seam, a model-agnostic Letta-style
shared-context block as the cross-provider interop primitive, a pure assembler
that emits MINIMAL ranked context carrying provenance/taint with every value, and
a read-only Obsidian projection. See ``docs/research/B2-shared-knowledge-graph/``.
"""

from __future__ import annotations
