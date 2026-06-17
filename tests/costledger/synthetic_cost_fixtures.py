"""Synthetic builders + Hypothesis strategies for the cost-ledger tests (no real data).

100% synthetic, public-data-only (CLAUDE.md §3.12/§5.5). Provides small factories
for the cost-ledger value types and Hypothesis strategies that generate WIDE,
randomized-but-valid usage objects and price vectors, so the property tests exercise
the general problem (anti-overfit, §3.9) rather than a handful of fixed cases.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from hypothesis import strategies as st

from autofirm.costledger.usage_cost_record import PriceVector, TokenUsage
from autofirm.foundation.money.money_amount import Money
from autofirm.modelgateway.model_reference import ModelProvider, ModelRef, UseCaseId
from autofirm.org.org_identifiers import RoleId

FIXED_INSTANT = datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)


def make_usage(
    *,
    input_tokens: int = 1000,
    output_tokens: int = 500,
    cache_read_tokens: int = 0,
    cache_write_tokens: int = 0,
    reasoning_tokens: int = 0,
) -> TokenUsage:
    """Build a synthetic ``TokenUsage`` (defaults are a plain input+output call)."""
    return TokenUsage(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cache_read_tokens=cache_read_tokens,
        cache_write_tokens=cache_write_tokens,
        reasoning_tokens=reasoning_tokens,
    )


def make_prices(  # noqa: PLR0913 -- a price builder mirrors the wide PriceVector
    *,
    currency: str = "USD",
    input_price: str = "0.000003",
    output_price: str = "0.000015",
    cache_read_price: str = "0.0000003",
    cache_write_price: str = "0.00000375",
    reasoning_price: str = "0.000015",
    tier_threshold_tokens: int | None = None,
    input_price_above_threshold: str | None = None,
    output_price_above_threshold: str | None = None,
) -> PriceVector:
    """Build a synthetic per-token ``PriceVector`` from exact Decimal STRINGS (folder 08)."""
    return PriceVector(
        currency=currency,
        input_price=Decimal(input_price),
        output_price=Decimal(output_price),
        cache_read_price=Decimal(cache_read_price),
        cache_write_price=Decimal(cache_write_price),
        reasoning_price=Decimal(reasoning_price),
        tier_threshold_tokens=tier_threshold_tokens,
        input_price_above_threshold=(
            None if input_price_above_threshold is None else Decimal(input_price_above_threshold)
        ),
        output_price_above_threshold=(
            None if output_price_above_threshold is None else Decimal(output_price_above_threshold)
        ),
    )


def make_model(
    provider: ModelProvider = ModelProvider.OPENAI, model_name: str = "gpt-synthetic"
) -> ModelRef:
    """Build a synthetic ``ModelRef``."""
    return ModelRef(provider=provider, model_name=model_name)


def money(amount: str, currency: str = "USD") -> Money:
    """Build ``Money`` from a Decimal STRING (never a float)."""
    return Money(Decimal(amount), currency)


def role(name: str = "role-synthetic") -> RoleId:
    """Build a synthetic ``RoleId``."""
    return RoleId(name)


def use_case(name: str = "uc-synthetic") -> UseCaseId:
    """Build a synthetic ``UseCaseId``."""
    return UseCaseId(name)


def corr(n: int) -> UUID:
    """A deterministic synthetic correlation UUID from an int seed."""
    return UUID(int=n)


# --------------------------- Hypothesis strategies --------------------------- #

# Token counts span degenerate (0) through a generous maximum so boundary and
# large-context behaviour is exercised. Bounded so products stay fast to verify.
token_counts = st.integers(min_value=0, max_value=2_000_000)

# Per-token prices as exact 2-or-fewer-significant-digit Decimals scaled tiny, built
# from STRINGS so no float ever enters (folder 08). Non-negative by construction.
_price_mantissa = st.integers(min_value=0, max_value=999_999)
_price_scale = st.integers(min_value=2, max_value=9)  # 10**-scale: tiny per-token rates
price_decimals = st.builds(
    lambda m, s: Decimal(m).scaleb(-s), _price_mantissa, _price_scale
)


@st.composite
def usage_strategy(draw: st.DrawFn) -> TokenUsage:
    """Generate a wide, valid ``TokenUsage`` over the full bucket space."""
    return TokenUsage(
        input_tokens=draw(token_counts),
        output_tokens=draw(token_counts),
        cache_read_tokens=draw(token_counts),
        cache_write_tokens=draw(token_counts),
        reasoning_tokens=draw(token_counts),
    )


@st.composite
def price_vector_strategy(draw: st.DrawFn, *, currency: str = "USD") -> PriceVector:
    """Generate a wide, valid NON-tiered ``PriceVector`` (Decimal rates from strings)."""
    return PriceVector(
        currency=currency,
        input_price=draw(price_decimals),
        output_price=draw(price_decimals),
        cache_read_price=draw(price_decimals),
        cache_write_price=draw(price_decimals),
        reasoning_price=draw(price_decimals),
    )
