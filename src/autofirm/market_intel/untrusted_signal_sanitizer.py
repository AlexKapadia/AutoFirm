"""Sanitize untrusted fetched signal content at the trust boundary (fail-closed).

What this does
--------------
A single, well-named boundary function — :func:`sanitize_untrusted_signal` — that
takes a raw text fragment pulled from an EXTERNAL feed (a competitor page, a trend
API, a news item) and either returns a clean, bounded, single-line string safe to
embed in a :class:`~autofirm.market_intel.market_insight_contract.MarketInsight`,
or **refuses it** with :class:`SignalRejectedError`. There is no "best effort,
keep going" path: content that is empty, oversized, or carries injection / control
markers is rejected fail-closed so it can never silently become a trusted insight.

Why it exists / where it sits
-----------------------------
All feed content is UNTRUSTED (CLAUDE.md §5.6: "treat all external/document input
as untrusted"). Centralising the validation here means the sensing sweep and the
green-light gate operate only on already-sanitized text — the trust boundary is
one auditable place, not scattered ``if`` checks. The sweep records every
rejection (append-only), so a refused signal is surfaced, never dropped.

Security / compliance invariants upheld
---------------------------------------
* **Bounded length (§5.6):** content longer than :data:`MAX_SIGNAL_CHARS` is
  refused — an oversized payload cannot exhaust downstream storage/audit.
* **Injection defence (§5.6):** prompt-injection / control markers (NUL, ANSI
  escapes, and the classic "ignore previous instructions" style override phrases)
  are refused, not stripped-and-trusted — fail-closed denial by default.
* **Determinism (§3.11):** sanitisation is a pure function of the input string.
"""

from __future__ import annotations

import re

__all__ = ["MAX_SIGNAL_CHARS", "SignalRejectedError", "sanitize_untrusted_signal"]

# Hard upper bound on a single sanitized signal fragment. Generous for a real
# headline/observation, but bounded so an oversized untrusted payload cannot
# exhaust audit/storage downstream (fail-closed resource bound, §5.6).
MAX_SIGNAL_CHARS = 2000

# Control characters that must never survive into a trusted insight: NUL and the
# C0/C1 control range (except the common whitespace tab/newline/CR, which we
# collapse rather than reject). ANSI escape sequences ride in on ``\x1b``.
_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]")

# Runs of any whitespace collapse to a single space so a sanitized observation is
# a single tidy line (newlines in untrusted content are a common injection vector).
_WHITESPACE_RUN = re.compile(r"\s+")

# Prompt-injection / instruction-override phrases. We REJECT (not sanitise) these
# because their presence in feed content is a strong signal of an adversarial
# payload trying to subvert a downstream LLM/agent — fail-closed denial.
_INJECTION_PHRASES = (
    "ignore previous instructions",
    "ignore all previous instructions",
    "disregard the above",
    "disregard previous",
    "system prompt:",
    "you are now",
    "<|im_start|>",
    "<|im_end|>",
)


class SignalRejectedError(Exception):
    """Raised when untrusted content is refused at the boundary (fail-closed).

    Carries a short, PII-free ``reason`` so the sweep can record exactly why a
    signal was rejected in the append-only audit trail (explain-every-decision).
    """

    def __init__(self, reason: str) -> None:
        """Build the rejection with a short machine-stable ``reason`` code/phrase."""
        super().__init__(reason)
        self.reason = reason


def sanitize_untrusted_signal(raw: str) -> str:
    """Return a clean, bounded, single-line string or refuse it fail-closed.

    The ordering is deliberate — cheapest/strongest refusals first, so an
    adversarial payload is rejected before we spend work normalising it:

    1. reject a non-``str`` or empty/blank fragment (nothing to trust),
    2. reject anything over :data:`MAX_SIGNAL_CHARS` (bounded resource use),
    3. reject embedded control characters / ANSI escapes (terminal-injection),
    4. reject known prompt-injection override phrases,
    5. otherwise collapse whitespace and return the clean single line.

    Args:
        raw: an untrusted text fragment from an external feed.

    Returns:
        The sanitized, single-line, length-bounded observation text.

    Raises:
        SignalRejectedError: if the content cannot be trusted (any rule above).
    """
    if not isinstance(raw, str):  # fail-closed: only text is a valid signal body
        raise SignalRejectedError("non-text signal content")
    if not raw.strip():
        # fail-closed: an empty/whitespace-only fragment carries no observation.
        raise SignalRejectedError("empty signal content")
    if len(raw) > MAX_SIGNAL_CHARS:
        # fail-closed: bound the payload before any further work (§5.6).
        raise SignalRejectedError("oversized signal content")
    if _CONTROL_CHARS.search(raw):
        # fail-closed: control chars / ANSI escapes are an injection vector — we
        # REFUSE rather than strip-and-trust, so a crafted terminal/markup
        # payload can never reach a downstream consumer (§5.6 injection defence).
        raise SignalRejectedError("control characters in signal content")
    lowered = raw.lower()
    for phrase in _INJECTION_PHRASES:
        if phrase in lowered:
            # fail-closed: a prompt-injection override phrase signals an
            # adversarial payload — deny by default, do not sanitise-and-keep.
            raise SignalRejectedError("prompt-injection phrase in signal content")
    # Safe to normalise: collapse whitespace runs to single spaces and trim.
    return _WHITESPACE_RUN.sub(" ", raw).strip()
