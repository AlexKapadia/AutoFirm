"""Per-provider usage parsers — the INVERTED cache-subset semantics, made correct.

What this does
--------------
Parses each provider's raw usage object into the platform's normalised
:class:`~autofirm.costledger.usage_cost_record.TokenUsage`, encoding the
load-bearing accuracy quirks the research RED-flagged (``SYNTHESIS.md`` §2,
``accuracy-bar-and-golden-set.md`` §2). The decomposition is provider-specific by
design — a single shared "subtract cached from input" rule is WRONG because the
cache-token / prompt relationship is **inverted between providers** (OpenAI/Google:
cached ⊂ prompt; Anthropic/Bedrock: cache separate).

Why it exists / where it sits
-----------------------------
``SYNTHESIS.md`` §2: "Each provider gets its own decomposition adapter; the *pricing*
core is shared, the *parsing* is not." These adapters are the parsing layer; the
pure cost computation prices the normalised result. They sit above ``TokenUsage`` and
below the cost computation. Every adapter is PURE and fail-closed.

The quirks encoded here (each = a wrong cost a naive parser would produce)
------------------------------------------------------------------------------
* **OpenAI** — ``cached_tokens ⊂ prompt_tokens`` and ``reasoning_tokens ⊂
  completion_tokens``: subtract BOTH before pricing base buckets, or double-charge.
  Also normalises **Chat vs Responses** field names (``prompt_tokens`` vs
  ``input_tokens``) — a hard-coded shape silently reads 0 → "free".
* **Google** — ``promptTokenCount`` INCLUDES ``cachedContentTokenCount``: subtract or
  double-charge; output base = ``candidatesTokenCount`` and thinking = ``thoughtsTokenCount``.
* **Anthropic** — ``cache_read``/``cache_creation`` are SEPARATE from ``input_tokens``
  (do NOT subtract); the 5m/1h cache-write split is summed into one write bucket
  (priced via per-surface vectors).
* **Bedrock** — ``inputTokens`` EXCLUDES ``cacheReadInputTokens`` (separate, do NOT
  subtract).

Security / compliance invariants upheld
---------------------------------------
* **Fail-closed parsing (§5.6):** a missing REQUIRED field is a refusal, never a
  silent 0 (which would under-bill). Negative/garbage counts are refused by
  ``TokenUsage`` downstream; an inverted subset that would go negative is refused here.
* **Provider usage is ground truth (folder 07):** counts are read verbatim from the
  provider object; nothing is re-tokenised.
"""

from __future__ import annotations

from collections.abc import Mapping

from autofirm.costledger.usage_cost_record import TokenUsage

__all__ = [
    "UsageParseError",
    "parse_anthropic_usage",
    "parse_bedrock_usage",
    "parse_google_usage",
    "parse_openai_usage",
]


class UsageParseError(Exception):
    """Raised when a provider usage object is missing a required field or is inconsistent."""


def _require_int(usage: Mapping[str, object], key: str) -> int:
    """Read a required non-negative integer field, fail-closed on absent/garbage.

    A missing field is the silent-``0`` trap (folder 02 quirk 8): refuse it so an
    un-parsed shape can never be billed as free.
    """
    if key not in usage:
        # fail-closed: a required usage field is absent — refuse rather than bill 0.
        raise UsageParseError(f"required usage field {key!r} is missing")
    value = usage[key]
    if not isinstance(value, int) or isinstance(value, bool):
        # fail-closed: a non-int (or bool) token count is malformed usage.
        raise UsageParseError(f"usage field {key!r} must be an int, got {type(value).__name__}")
    if value < 0:
        raise UsageParseError(f"usage field {key!r} must be >= 0, got {value}")
    return value


def _opt_int(usage: Mapping[str, object], key: str, default: int = 0) -> int:
    """Read an OPTIONAL non-negative integer field (default 0), fail-closed on garbage.

    Optional fields (cache, reasoning) legitimately default to 0 when absent (§8); a
    PRESENT-but-malformed value is still refused.
    """
    if key not in usage:
        return default
    value = usage[key]
    if not isinstance(value, int) or isinstance(value, bool):
        raise UsageParseError(f"usage field {key!r} must be an int, got {type(value).__name__}")
    if value < 0:
        raise UsageParseError(f"usage field {key!r} must be >= 0, got {value}")
    return value


def parse_openai_usage(usage: Mapping[str, object]) -> TokenUsage:
    """Parse an OpenAI usage object (Chat OR Responses), subset-correct (folder 02).

    Normalises the Chat (``prompt_tokens``/``completion_tokens``) and Responses
    (``input_tokens``/``output_tokens``) field names. Subtracts ``cached_tokens``
    (⊂ prompt) and ``reasoning_tokens`` (⊂ completion) before pricing base buckets,
    so neither is double-charged. Nested details live in
    ``prompt_tokens_details``/``completion_tokens_details``.
    """
    prompt = _first_present_int(usage, ("prompt_tokens", "input_tokens"))
    completion = _first_present_int(usage, ("completion_tokens", "output_tokens"))
    cached = _nested_opt_int(
        usage, ("prompt_tokens_details", "input_tokens_details"), "cached_tokens"
    )
    reasoning = _nested_opt_int(
        usage, ("completion_tokens_details", "output_tokens_details"), "reasoning_tokens"
    )
    # cached ⊂ prompt, reasoning ⊂ completion: subtract to get the base buckets.
    base_input = prompt - cached
    base_output = completion - reasoning
    if base_input < 0 or base_output < 0:
        # fail-closed: a cached/reasoning subset exceeding its parent is impossible
        # real usage — refuse rather than price a negative (under-billing) bucket.
        raise UsageParseError(
            "OpenAI cached/reasoning subset exceeds its parent count (inconsistent usage)"
        )
    return TokenUsage(
        input_tokens=base_input,
        output_tokens=base_output,
        cache_read_tokens=cached,
        reasoning_tokens=reasoning,
    )


def parse_google_usage(usage: Mapping[str, object]) -> TokenUsage:
    """Parse a Google/Gemini usage object, subset-correct (folder 03).

    ``promptTokenCount`` INCLUDES ``cachedContentTokenCount`` → subtract before
    pricing base input. Output base = ``candidatesTokenCount``; thinking =
    ``thoughtsTokenCount`` (billed at output rate, itemised, not added on top).
    """
    prompt = _require_int(usage, "promptTokenCount")
    cached = _opt_int(usage, "cachedContentTokenCount")
    candidates = _require_int(usage, "candidatesTokenCount")
    thoughts = _opt_int(usage, "thoughtsTokenCount")
    base_input = prompt - cached  # cached ⊂ prompt: subtract or double-charge.
    if base_input < 0:
        # fail-closed: cached exceeding the prompt total is impossible — refuse.
        raise UsageParseError(
            "Google cachedContentTokenCount exceeds promptTokenCount (inconsistent usage)"
        )
    return TokenUsage(
        input_tokens=base_input,
        output_tokens=candidates,
        cache_read_tokens=cached,
        reasoning_tokens=thoughts,
    )


def parse_anthropic_usage(usage: Mapping[str, object]) -> TokenUsage:
    """Parse an Anthropic usage object, cache-SEPARATE (folder 01).

    ``cache_read_input_tokens`` and ``cache_creation_input_tokens`` are SEPARATE from
    ``input_tokens`` (do NOT subtract — that is the inverted-quirk trap). The 5m/1h
    write split (``cache_creation.{ephemeral_5m,ephemeral_1h}``) is summed into one
    write bucket here; the per-TTL price difference is carried by the price surface.
    Thinking tokens (``output_tokens_details.thinking_tokens``) are itemised reasoning.
    """
    input_tokens = _require_int(usage, "input_tokens")
    output_tokens = _require_int(usage, "output_tokens")
    cache_read = _opt_int(usage, "cache_read_input_tokens")
    cache_write = _anthropic_cache_write(usage)
    reasoning = _nested_opt_int(usage, ("output_tokens_details",), "thinking_tokens")
    # NOTE: NO subtraction — Anthropic cache buckets are separate, not a subset.
    return TokenUsage(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cache_read_tokens=cache_read,
        cache_write_tokens=cache_write,
        reasoning_tokens=reasoning,
    )


def parse_bedrock_usage(usage: Mapping[str, object]) -> TokenUsage:
    """Parse an AWS Bedrock usage object, cache-SEPARATE (folder 04).

    ``inputTokens`` EXCLUDES ``cacheReadInputTokens`` (separate — do NOT subtract).
    ``outputTokens`` is the completion count. (The per-1K-vs-per-1M unit trap is
    handled by the price catalog's ``unit_divisor``, not here.)
    """
    return TokenUsage(
        input_tokens=_require_int(usage, "inputTokens"),
        output_tokens=_require_int(usage, "outputTokens"),
        cache_read_tokens=_opt_int(usage, "cacheReadInputTokens"),
        cache_write_tokens=_opt_int(usage, "cacheWriteInputTokens"),
    )


def _first_present_int(usage: Mapping[str, object], keys: tuple[str, ...]) -> int:
    """Return the first present required int among ``keys`` (Chat/Responses divergence).

    fail-closed: if NONE of the alternative field names is present, the shape is
    unrecognised — refuse rather than read a silent 0 (folder 02 quirk 8).
    """
    for key in keys:
        if key in usage:
            return _require_int(usage, key)
    raise UsageParseError(f"none of the required usage fields {keys} is present")


def _nested_opt_int(
    usage: Mapping[str, object], container_keys: tuple[str, ...], inner_key: str
) -> int:
    """Read an optional int nested under the first present container key (default 0).

    Used for ``*_details.cached_tokens`` / ``.reasoning_tokens`` / ``.thinking_tokens``.
    A missing container or inner key means the provider did not report it → 0; a
    present-but-malformed value is refused by ``_opt_int``.
    """
    for container_key in container_keys:
        container = usage.get(container_key)
        if isinstance(container, Mapping):
            return _opt_int(container, inner_key)
    return 0


def _anthropic_cache_write(usage: Mapping[str, object]) -> int:
    """Sum the Anthropic 5m + 1h cache-write split into one write bucket (folder 01).

    Prefers the detailed ``cache_creation.{ephemeral_5m,ephemeral_1h}`` split when
    present; otherwise falls back to the top-level ``cache_creation_input_tokens``
    total. The two TTLs price differently, but that difference is carried by the
    price surface — here we only need the total write-token count.
    """
    creation = usage.get("cache_creation")
    if isinstance(creation, Mapping):
        return _opt_int(creation, "ephemeral_5m") + _opt_int(creation, "ephemeral_1h")
    return _opt_int(usage, "cache_creation_input_tokens")
