"""Investment appraisal metrics — NPV and IRR.

What this does
--------------
* :func:`net_present_value` — NPV of a cash-flow series where ``cash_flows[0]``
  is the period-0 flow (typically the initial outlay, negative). Sum of
  ``CF_t / (1 + rate) ** t`` over ``t = 0..n``.
* :func:`internal_rate_of_return` — the IRR: the discount rate at which NPV is
  zero, found by deterministic bisection to a configurable tolerance.

Formulae (research source 01, Damodaran; standard capital-budgeting identities)
-------------------------------------------------------------------------------
* ``NPV = sum_{t=0..n} CF_t / (1 + r)^t`` (the intrinsic-value identity with a
  period-0 term).
* IRR solves ``NPV(IRR) = 0``. There is no closed form for n > 4, so IRR is
  found numerically; bisection is chosen because it is **deterministic** and
  cannot diverge (unlike Newton-Raphson), provided NPV changes sign across the
  bracket — which is the standard "conventional cash flow" precondition.

Why it exists / where it sits
-----------------------------
The investment-appraisal companion to the DCF engine (SYNTHESIS §2). NPV reuses
:func:`~autofirm.finance.valuation.discounted_cash_flow.present_value` so the
discounting convention is identical and exact (CLAUDE.md §3.11).

Security / compliance invariants upheld
---------------------------------------
Fail-closed (CLAUDE.md §5.6): an empty series, a non-positive tolerance, a
non-positive iteration cap, or a bracket over which NPV does not change sign
(no IRR in range) are refused with ``ValueError`` rather than returning a
silently-wrong rate.
"""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal, localcontext

from autofirm.finance.valuation.discounted_cash_flow import DCF_PRECISION, present_value

__all__ = ["internal_rate_of_return", "net_present_value"]


def net_present_value(cash_flows: Sequence[Decimal], rate: Decimal) -> Decimal:
    """NPV with a period-0 term: ``sum_{t=0..n} CF_t / (1 + rate) ** t``.

    Args:
        cash_flows: ``cash_flows[0]`` is the period-0 flow (often the negative
            initial investment); subsequent entries are periods 1..n.
        rate: The per-period discount rate.

    Returns:
        The exact NPV as a :class:`~decimal.Decimal`.

    Raises:
        ValueError: If ``cash_flows`` is empty (fail-closed — §5.6).
    """
    if not cash_flows:  # fail-closed: nothing to evaluate
        raise ValueError("cash_flows must contain at least one period")
    with localcontext() as ctx:
        ctx.prec = DCF_PRECISION
        total = Decimal(0)
        for period, cash_flow in enumerate(cash_flows):
            # period starts at 0: CF_0 is undiscounted (present_value with t=0).
            total += present_value(cash_flow, rate, period)
        return total


def internal_rate_of_return(
    cash_flows: Sequence[Decimal],
    *,
    low: Decimal = Decimal("-0.9999"),
    high: Decimal = Decimal("10"),
    tolerance: Decimal = Decimal("1e-12"),
    max_iterations: int = 200,
) -> Decimal:
    """Internal rate of return: the rate where NPV crosses zero (bisection).

    Bisection is deterministic and convergent: given a bracket ``[low, high]``
    across which NPV changes sign, it halves the interval each step until the NPV
    magnitude is within ``tolerance``, or ``max_iterations`` is reached. The
    bracket default spans -99.99% to +1000%, covering conventional projects.

    Args:
        cash_flows: A conventional cash-flow series (period 0..n) with at least
            one sign change, so an IRR exists.
        low: Lower bracket bound (> -1). Default ``-0.9999``.
        high: Upper bracket bound. Default ``10`` (1000%).
        tolerance: Convergence threshold on ``|NPV|``. Must be > 0.
        max_iterations: Hard cap on bisection steps (bounds the loop so no
            mutant can hang the gate). Must be > 0.

    Returns:
        The IRR as an exact-to-tolerance :class:`~decimal.Decimal`.

    Raises:
        ValueError: If ``cash_flows`` is empty, ``tolerance <= 0``,
            ``max_iterations <= 0``, or NPV does not change sign across
            ``[low, high]`` (no IRR in range — fail-closed, §5.6).
    """
    if not cash_flows:  # fail-closed: nothing to solve
        raise ValueError("cash_flows must contain at least one period")
    if tolerance <= Decimal(0):  # fail-closed: tolerance must be positive
        raise ValueError(f"tolerance must be > 0, got {tolerance}")
    if max_iterations <= 0:  # fail-closed: need at least one iteration
        raise ValueError(f"max_iterations must be > 0, got {max_iterations}")

    with localcontext() as ctx:
        ctx.prec = DCF_PRECISION
        npv_low = net_present_value(cash_flows, low)
        npv_high = net_present_value(cash_flows, high)
        # fail-closed: bisection needs NPV to straddle zero across the bracket.
        if npv_low == Decimal(0):
            return low
        if npv_high == Decimal(0):
            return high
        if (npv_low > 0) == (npv_high > 0):  # same sign -> no root bracketed
            raise ValueError(
                "NPV does not change sign across the bracket; no IRR in "
                f"[{low}, {high}] for the given cash flows"
            )

        lo, hi = low, high
        # Bounded loop (<= max_iterations): a mutated bound cannot hang the gate.
        for _ in range(max_iterations):
            mid = (lo + hi) / Decimal(2)
            npv_mid = net_present_value(cash_flows, mid)
            if abs(npv_mid) <= tolerance:  # converged to within tolerance
                return mid
            # Keep the half-interval that still brackets the sign change.
            if (npv_mid > 0) == (npv_low > 0):
                lo = mid
            else:
                hi = mid
        # Exhausted the iteration budget: return the best midpoint estimate. The
        # bracket has been halved max_iterations times, so this is tight.
        return (lo + hi) / Decimal(2)
