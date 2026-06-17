"""The PURE, exact cost function ``(TokenUsage, PriceVector) -> Money`` — Layer A.

What this does
--------------
Computes the exact :class:`~autofirm.foundation.money.Money` cost of one model call
from its provider-attested :class:`~autofirm.costledger.usage_cost_record.TokenUsage`
and the frozen :class:`~autofirm.costledger.usage_cost_record.PriceVector`, using
only :class:`decimal.Decimal` arithmetic — never ``float``. Per-bucket products are
summed at full precision and quantised to the currency minor unit ONCE at the end
(research folder 08). Tiered pricing (Google >200k-prompt) and the per-1K-vs-per-1M
``unit_divisor`` (Bedrock) are applied boundary-exactly.

THE HONEST ACCURACY BAR THIS IMPLEMENTS (CRO research, accuracy-bar-and-golden-set.md)
--------------------------------------------------------------------------------------
* **Layer A — computation exactness (THIS module; FULLY achievable, the §3.11 bar):**
  for a given ``(usage, price snapshot)`` the computed ``Decimal`` cost equals the
  mathematically correct value EXACTLY, to the currency minor unit, on every input,
  deterministically, with zero arithmetic/logic error. A single wrong cent is
  unacceptable. We own this completely — there is no external uncertainty.
* **Layer B — zero-drift reconciliation (see ``provider_billing_reconciliation``):**
  Σ(our computed costs over a CLOSED period) == the provider's own reported total,
  gross-vs-gross, with credits itemised separately — never silently absorbed.
* **Layer C — provider usage trusted as ground truth (see ``provider_usage_adapters``):**
  we record the provider's usage object verbatim and never re-tokenise to "correct"
  it (folder 07 shows local re-counting is LESS accurate).

Why it exists / where it sits
-----------------------------
This is the mutation-critical core of W5 (data-contracts.md §8). It is a pure
function (no clock, no IO, no globals) so it is trivially deterministic and
property-testable. The ledger calls it to fill ``UsageCostRecord.cost`` on the
``price_map_computed`` path; on the ``provider_reported`` path it is the
reconciliation cross-check.

Security / compliance invariants upheld
---------------------------------------
* **Zero float (folder 08, §3.11):** all arithmetic is ``Decimal``; the only
  rounding is the single banker's quantisation at the ledger boundary.
* **No intermediate rounding:** every per-bucket product is summed at full
  precision; rounding each product first would lose pennies.
* **Boundary-exact tiering (folder 03):** the >threshold rate applies iff the PROMPT
  strictly exceeds the threshold — on/just-over/just-under are distinct.
* **Currency-correct quantisation (folder 09):** the result is quantised to the
  per-currency minor unit (USD 2dp, JPY 0dp, BHD 3dp), unknown currency fails closed.
"""

from __future__ import annotations

from decimal import Decimal

from autofirm.costledger.usage_cost_record import PriceVector, TokenUsage
from autofirm.foundation.money.money_amount import Money

__all__ = ["compute_exact_cost"]


def compute_exact_cost(
    usage: TokenUsage,
    prices: PriceVector,
    *,
    unit_divisor: int = 1,
) -> Money:
    """Compute the exact, quantised ``Money`` cost of one call (PURE, zero float).

    The cost is ``Σ_bucket (tokens[bucket] x rate[bucket]) / unit_divisor``, summed at
    full ``Decimal`` precision and quantised to the currency minor unit ONCE at the
    end. Input and output buckets use the tiered rate when ``prices`` declares a
    threshold and the PROMPT (``input_tokens + cache_read_tokens``) strictly exceeds
    it (boundary-exact, folder 03). The ``unit_divisor`` scales per-1K / per-1M rate
    rows to a per-token figure with no rounding (folder 04 — no 1000x error).

    Args:
        usage: The provider-attested token counts (already provider-decomposed).
        prices: The frozen per-``unit_divisor`` price vector (Decimal rates).
        unit_divisor: Tokens per quoted rate (1 per-token, 1000 per-1K, 1_000_000
            per-1M). Must be > 0.

    Returns:
        The exact ``Money`` cost, quantised to the price vector's currency minor unit.

    Raises:
        ValueError: If ``unit_divisor`` <= 0 (fail-closed: would divide-by-zero or
            invert the sign).
    """
    if unit_divisor <= 0:  # fail-closed: an invalid scale must not silently price 0/∞
        raise ValueError("unit_divisor must be > 0 (tokens per quoted rate)")

    input_rate, output_rate = _effective_input_output_rates(usage, prices)
    divisor = Decimal(unit_divisor)

    # Each bucket priced at full precision; NO intermediate rounding (folder 08).
    # Prompt-cache read/write and reasoning are priced at their own dedicated rates.
    total = (
        Decimal(usage.input_tokens) * input_rate
        + Decimal(usage.output_tokens) * output_rate
        + Decimal(usage.cache_read_tokens) * prices.cache_read_price
        + Decimal(usage.cache_write_tokens) * prices.cache_write_price
        + Decimal(usage.reasoning_tokens) * prices.reasoning_price
    ) / divisor

    # Quantise to the currency minor unit ONCE, at the boundary (folder 08/09):
    # Money.quantize applies the per-currency exponent with banker's rounding.
    return Money(total, prices.currency).quantize()


def _effective_input_output_rates(
    usage: TokenUsage, prices: PriceVector
) -> tuple[Decimal, Decimal]:
    """Return the (input_rate, output_rate) to apply, honouring tiering boundary-exactly.

    Tiering (Google >200k-prompt, folder 03) is keyed on the PROMPT size — the base
    input plus the cache-read tokens that made up the prompt — NOT the per-call total.
    The higher rate applies iff the prompt STRICTLY exceeds the threshold, so a prompt
    exactly AT the threshold stays on the base rate (on/just-over/just-under distinct).
    """
    if prices.tier_threshold_tokens is None:
        # No tiering declared: the flat input/output rates apply to every token.
        return prices.input_price, prices.output_price

    # The validated PriceVector guarantees all three tier fields are set together
    # (its all-or-none model_validator). We re-check fail-closed rather than assume,
    # so a mutated/forged vector that slipped a half-spec through is refused, not
    # priced at the wrong rate.
    above_input = prices.input_price_above_threshold
    above_output = prices.output_price_above_threshold
    if above_input is None or above_output is None:  # fail-closed: half-specified tier
        raise ValueError("tiered price vector missing an above-threshold rate")
    prompt_tokens = usage.input_tokens + usage.cache_read_tokens
    if prompt_tokens > prices.tier_threshold_tokens:
        # STRICTLY above the boundary → the uplift rate (boundary-exact, folder 03).
        return above_input, above_output
    return prices.input_price, prices.output_price
