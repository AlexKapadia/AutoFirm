"""Provider-quirk regression tests — one per RED flag (each prevents a WRONG cost).

These are the load-bearing accuracy facts from the research (SYNTHESIS.md §2,
accuracy-bar §2). Each test parses a realistic provider usage object and asserts BOTH
the correct decomposition AND that the resulting cost differs from the naive
(wrong) computation a flat token-counter would produce — so the test would FAIL if
the quirk were not handled. No tautologies: the wrong number is computed explicitly.
"""

from decimal import Decimal

import pytest

from autofirm.costledger.exact_cost_computation import compute_exact_cost
from autofirm.costledger.provider_usage_adapters import (
    UsageParseError,
    parse_anthropic_usage,
    parse_bedrock_usage,
    parse_google_usage,
    parse_openai_usage,
)
from autofirm.costledger.usage_cost_record import TokenUsage
from autofirm.foundation.money.money_amount import Money
from tests.costledger.synthetic_cost_fixtures import make_prices

# ---- QUIRK 2 (OpenAI): cached ⊂ prompt, reasoning ⊂ completion -> subtract ---- #


def test_openai_cached_and_reasoning_are_subsets_subtracted_not_double_charged() -> None:
    # prompt=1000 INCLUDES 200 cached; completion=500 INCLUDES 300 reasoning.
    raw = {
        "prompt_tokens": 1000,
        "completion_tokens": 500,
        "prompt_tokens_details": {"cached_tokens": 200},
        "completion_tokens_details": {"reasoning_tokens": 300},
    }
    parsed = parse_openai_usage(raw)
    # base input = 1000-200 = 800 ; base output = 500-300 = 200.
    assert parsed == TokenUsage(
        input_tokens=800, output_tokens=200, cache_read_tokens=200, reasoning_tokens=300
    )
    # The WRONG (naive: don't subtract) version would price 1000 input + 500 output
    # AND 200 cache + 300 reasoning => double-charging the cached + reasoning tokens.
    prices = make_prices(
        input_price="0.001", output_price="0.002",
        cache_read_price="0.0005", reasoning_price="0.003",
        cache_write_price="0",
    )
    correct = compute_exact_cost(parsed, prices)
    naive_double = compute_exact_cost(
        TokenUsage(input_tokens=1000, output_tokens=500,
                   cache_read_tokens=200, reasoning_tokens=300),
        prices,
    )
    assert correct != naive_double  # proves subtraction matters
    # correct: 800*.001 + 200*.002 + 200*.0005 + 300*.003 = .8+.4+.1+.9 = 2.20
    assert correct == Money(Decimal("2.20"), "USD")


def test_openai_subset_exceeding_parent_fails_closed() -> None:
    # cached > prompt is impossible real usage — refuse, don't price a negative bucket.
    with pytest.raises(UsageParseError, match="subset exceeds its parent"):
        parse_openai_usage(
            {"prompt_tokens": 100, "completion_tokens": 50,
             "prompt_tokens_details": {"cached_tokens": 200}}
        )


# ---- QUIRK 8 (OpenAI): Chat vs Responses field-name divergence ---- #


def test_openai_chat_and_responses_field_names_both_parse_identically() -> None:
    chat = parse_openai_usage({"prompt_tokens": 700, "completion_tokens": 250})
    responses = parse_openai_usage({"input_tokens": 700, "output_tokens": 250})
    assert chat == responses == TokenUsage(input_tokens=700, output_tokens=250)


def test_openai_unrecognised_shape_fails_closed_not_silent_zero() -> None:
    # A hard-coded shape reading neither field name would silently bill 0 ("free").
    with pytest.raises(UsageParseError, match="none of the required usage fields"):
        parse_openai_usage({"totally_wrong_key": 5})


# ---- QUIRK 2 (Google): promptTokenCount INCLUDES cachedContentTokenCount ---- #


def test_google_prompt_includes_cached_so_subtract() -> None:
    raw = {
        "promptTokenCount": 1000,  # INCLUDES the 200 cached
        "cachedContentTokenCount": 200,
        "candidatesTokenCount": 400,
        "thoughtsTokenCount": 100,
    }
    parsed = parse_google_usage(raw)
    # base input = 1000-200 = 800 ; output = 400 ; reasoning(thoughts) = 100.
    assert parsed == TokenUsage(
        input_tokens=800, output_tokens=400, cache_read_tokens=200, reasoning_tokens=100
    )
    prices = make_prices(input_price="0.001", output_price="0.002",
                         cache_read_price="0.0005", reasoning_price="0.002",
                         cache_write_price="0")
    correct = compute_exact_cost(parsed, prices)
    naive = compute_exact_cost(  # naive: price the full 1000 prompt AND the 200 cache
        TokenUsage(input_tokens=1000, output_tokens=400,
                   cache_read_tokens=200, reasoning_tokens=100),
        prices,
    )
    assert correct != naive  # double-charging the cached tokens is wrong
    # 800*.001 + 400*.002 + 200*.0005 + 100*.002 = .8+.8+.1+.2 = 1.90
    assert correct == Money(Decimal("1.90"), "USD")


def test_google_cached_exceeding_prompt_fails_closed() -> None:
    with pytest.raises(UsageParseError, match="exceeds promptTokenCount"):
        parse_google_usage(
            {"promptTokenCount": 100, "cachedContentTokenCount": 200,
             "candidatesTokenCount": 10}
        )


# ---- QUIRK 2 (Anthropic): cache buckets SEPARATE — do NOT subtract ---- #


def test_anthropic_cache_is_separate_not_subtracted() -> None:
    raw = {
        "input_tokens": 1000,  # does NOT include cache here (separate, inverted!)
        "output_tokens": 500,
        "cache_read_input_tokens": 200,
        "cache_creation": {"ephemeral_5m": 100, "ephemeral_1h": 50},
        "output_tokens_details": {"thinking_tokens": 80},
    }
    parsed = parse_anthropic_usage(raw)
    # input stays 1000 (NOT 800) — Anthropic cache is separate. write = 100+50 = 150.
    assert parsed == TokenUsage(
        input_tokens=1000, output_tokens=500,
        cache_read_tokens=200, cache_write_tokens=150, reasoning_tokens=80,
    )


def test_anthropic_applying_openai_rule_would_be_wrong() -> None:
    # If we WRONGLY applied OpenAI's "subtract cached from input" to Anthropic, the
    # input bucket would be 800 not 1000 — a different (under-billed) cost. Prove it.
    raw = {"input_tokens": 1000, "output_tokens": 0, "cache_read_input_tokens": 200}
    parsed = parse_anthropic_usage(raw)
    prices = make_prices(input_price="0.001", output_price="0",
                         cache_read_price="0.0005", cache_write_price="0",
                         reasoning_price="0")
    correct = compute_exact_cost(parsed, prices)
    wrong_subtracted = compute_exact_cost(
        TokenUsage(input_tokens=800, output_tokens=0, cache_read_tokens=200), prices
    )
    assert correct != wrong_subtracted
    # correct: 1000*.001 + 200*.0005 = 1.0 + 0.1 = 1.10
    assert correct == Money(Decimal("1.10"), "USD")


def test_anthropic_falls_back_to_top_level_cache_creation_total() -> None:
    raw = {"input_tokens": 10, "output_tokens": 5, "cache_creation_input_tokens": 70}
    parsed = parse_anthropic_usage(raw)
    assert parsed.cache_write_tokens == 70


# ---- QUIRK 4 (Bedrock): per-1K vs per-1M unit (1000x trap) + cache separate ---- #


def test_bedrock_input_excludes_cache_read_separate() -> None:
    raw = {"inputTokens": 1000, "outputTokens": 500, "cacheReadInputTokens": 300}
    parsed = parse_bedrock_usage(raw)
    # inputTokens already EXCLUDES cache-read — do NOT subtract (separate).
    assert parsed == TokenUsage(input_tokens=1000, output_tokens=500, cache_read_tokens=300)


def test_bedrock_per_1k_row_vs_per_1m_row_no_1000x_error() -> None:
    parsed = parse_bedrock_usage({"inputTokens": 1_000_000, "outputTokens": 0})
    # A per-1K rate of 0.003 over 1M tokens via unit_divisor=1000 -> 3.00.
    per_1k = compute_exact_cost(
        parsed,
        make_prices(input_price="0.003", output_price="0", cache_read_price="0",
                    cache_write_price="0", reasoning_price="0"),
        unit_divisor=1_000,
    )
    # The SAME real price expressed per-1M (3.0) with the WRONG per-1K divisor (1000)
    # would be 1000x too big — the unit_divisor on the row is what prevents it.
    per_1m = compute_exact_cost(
        parsed,
        make_prices(input_price="3.0", output_price="0", cache_read_price="0",
                    cache_write_price="0", reasoning_price="0"),
        unit_divisor=1_000_000,
    )
    assert per_1k == per_1m == Money(Decimal("3.00"), "USD")


# ---- fail-closed parsing: missing required field is NOT a silent zero ---- #


@pytest.mark.parametrize(
    ("parser", "raw"),
    [
        (parse_openai_usage, {"completion_tokens": 5}),  # missing prompt
        (parse_google_usage, {"candidatesTokenCount": 5}),  # missing prompt
        (parse_anthropic_usage, {"output_tokens": 5}),  # missing input
        (parse_bedrock_usage, {"outputTokens": 5}),  # missing input
    ],
)
def test_missing_required_field_fails_closed(parser, raw) -> None:
    with pytest.raises(UsageParseError):
        parser(raw)


def test_negative_or_non_int_count_fails_closed() -> None:
    with pytest.raises(UsageParseError, match="must be >= 0"):
        parse_openai_usage({"prompt_tokens": -1, "completion_tokens": 0})
    with pytest.raises(UsageParseError, match="must be an int"):
        parse_openai_usage({"prompt_tokens": 1.5, "completion_tokens": 0})
    with pytest.raises(UsageParseError, match="must be an int"):
        # a bool is not a valid token count even though bool is an int subclass.
        parse_openai_usage({"prompt_tokens": True, "completion_tokens": 0})
