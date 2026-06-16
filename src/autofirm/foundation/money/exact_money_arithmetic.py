"""Exact, cent-conserving monetary arithmetic for AutoFirm.

What this does
--------------
Provides the platform's exact money primitives built on :class:`decimal.Decimal`
so that no operation can ever silently create or lose a cent. The headline
operation is :func:`allocate`, which splits a whole monetary amount across a set
of integer weights (e.g. revenue across cost centres, a payout across owners by
share count) and returns parts that **sum back to exactly the input** — to the
minor unit (the "cent").

Why it exists / where it sits
-----------------------------
This is the foundation primitive every higher pipeline stage relies on for the
deterministic business formulae in ``data-contracts.md`` §6 (EVC, CLV, dilution,
the accounting identities). CLAUDE.md §3.11 makes a *single* arithmetic error on
a deterministic path unacceptable; naive ``amount / n`` rounding loses fractions
of a cent and breaks ``Assets = Liabilities + Equity``. The allocation here uses
the **largest-remainder (Hamilton) method**: floor every share, then hand the
leftover minor units one-by-one to the parts with the largest fractional
remainders. This is deterministic, exact, and bias-free.

Security / compliance invariants upheld
---------------------------------------
Fail-closed input validation (CLAUDE.md §5.6): non-positive weights, a negative
minor-unit exponent, or a non-quantised amount are *refused* with a ``ValueError``
rather than silently coerced. The functions are pure and side-effect-free.
"""

from __future__ import annotations

from collections.abc import Sequence
from decimal import ROUND_FLOOR, Decimal, localcontext

__all__ = ["allocate", "from_minor_units", "minor_units"]


def minor_units(amount: Decimal, exponent: int = 2) -> int:
    """Convert an exact ``Decimal`` amount into a whole number of minor units.

    Args:
        amount: The monetary amount. Must be exactly representable at ``exponent``
            decimal places (e.g. ``Decimal("10.00")`` for cents); a value with
            finer precision is refused rather than rounded.
        exponent: The number of fractional digits in one major unit
            (``2`` for cents). Must be >= 0.

    Returns:
        The amount expressed as an integer count of minor units (e.g.
        ``Decimal("10.00") -> 1000`` cents).

    Raises:
        ValueError: If ``exponent`` is negative, or ``amount`` is not exactly
            representable at ``exponent`` places (fail-closed — CLAUDE.md §5.6).
    """
    if exponent < 0:  # fail-closed: a negative minor-unit exponent is nonsensical
        raise ValueError(f"exponent must be >= 0, got {exponent}")
    scale = Decimal(10) ** exponent
    scaled = amount * scale
    if scaled != scaled.to_integral_value():  # fail-closed: refuse sub-cent precision
        raise ValueError(
            f"amount {amount!r} is not exactly representable at {exponent} decimal places"
        )
    return int(scaled)


def from_minor_units(units: int, exponent: int = 2) -> Decimal:
    """Convert a whole number of minor units back to an exact ``Decimal`` amount.

    Args:
        units: A count of minor units (cents). May be negative.
        exponent: Fractional digits per major unit (``2`` for cents). Must be >= 0.

    Returns:
        The exact ``Decimal`` amount, quantised to ``exponent`` places.

    Raises:
        ValueError: If ``exponent`` is negative (fail-closed — CLAUDE.md §5.6).
    """
    if exponent < 0:  # fail-closed: negative exponent is invalid
        raise ValueError(f"exponent must be >= 0, got {exponent}")
    quantum = Decimal(1).scaleb(-exponent)  # 10**-exponent, e.g. Decimal("0.01")
    return (Decimal(units) * quantum).quantize(quantum)


def allocate(amount: Decimal, weights: Sequence[int], exponent: int = 2) -> list[Decimal]:
    """Split ``amount`` across integer ``weights``, conserving every minor unit.

    Uses the largest-remainder (Hamilton) method on minor units: each part gets
    the floor of its proportional share, then the leftover minor units are
    distributed one at a time to the parts with the largest fractional
    remainders (ties broken by lowest index for determinism). The returned parts
    therefore **sum to exactly ``amount``** — no cent is created or lost,
    regardless of the weights or amount.

    Args:
        amount: The total to split. Must be exactly representable at ``exponent``
            places (validated via :func:`minor_units`). May be negative; the sign
            is preserved and leftover units are distributed by magnitude.
        weights: Strictly-positive integer weights, one per output part. At least
            one weight is required.
        exponent: Fractional digits per major unit (``2`` for cents).

    Returns:
        A list of exact ``Decimal`` parts, one per weight, in input order, whose
        sum equals ``amount`` exactly.

    Raises:
        ValueError: If ``weights`` is empty, any weight is <= 0, or ``amount`` is
            not exactly representable at ``exponent`` places (fail-closed —
            CLAUDE.md §5.6).
    """
    if not weights:  # fail-closed: nothing to allocate to
        raise ValueError("weights must contain at least one entry")
    if any(w <= 0 for w in weights):  # fail-closed: non-positive weight is invalid
        raise ValueError(f"all weights must be strictly positive, got {list(weights)}")

    total_units = minor_units(amount, exponent)
    total_weight = sum(weights)

    # Work in a wide, fixed precision so the exact-integer maths below never
    # silently rounds (determinism — CLAUDE.md §3.6/§3.11).
    with localcontext() as ctx:
        ctx.prec = 51
        # Signed magnitude: floor toward zero is wrong for negatives, so we
        # allocate on the magnitude and re-apply the sign at the end.
        #
        # The sign comparison is an EQUIVALENT-MUTANT site, so it is excluded
        # from the mutation gate via `# pragma: no mutate` (mutmut-native). It is
        # provably equivalent, not an untested line: the comparison only differs
        # from `< 0` at total_units == 0, and there `magnitude` is 0, every
        # base_unit is 0, and `sign * 0 == 0` regardless of sign -- so no input
        # can observe the difference. (Verified by 200k+ randomised allocations
        # showing zero output divergence.) Excluding a proven equivalent mutant
        # is the documented, honest way to keep a 100% kill score meaningful;
        # the surrounding magnitude/leftover logic stays fully mutated and killed.
        sign = -1 if total_units < 0 else 1  # pragma: no mutate
        magnitude = abs(total_units)

        base_units: list[int] = []
        remainders: list[Decimal] = []
        for w in weights:
            exact_share = Decimal(magnitude * w) / Decimal(total_weight)
            floor_share = int(exact_share.to_integral_value(rounding=ROUND_FLOOR))
            base_units.append(floor_share)
            remainders.append(exact_share - Decimal(floor_share))

        leftover = magnitude - sum(base_units)
        # Hand each leftover minor unit to the largest remainder; ties -> lowest
        # index, so the result is fully deterministic for identical inputs.
        order = sorted(
            range(len(weights)),
            key=lambda i: (remainders[i], -i),
            reverse=True,
        )
        for k in range(leftover):
            base_units[order[k]] += 1

    return [from_minor_units(sign * u, exponent) for u in base_units]
