"""Discounted-cash-flow valuation — present value, terminal value, DCF.

What this does
--------------
Implements intrinsic valuation by discounting projected free cash flows at a
discount rate (WACC for firm value), plus a Gordon-growth terminal value for the
stable-growth period beyond the explicit horizon. Exposes:

* :func:`present_value` — PV of one cash flow ``CF_t / (1 + r)^t``.
* :func:`terminal_value` — ``CF_{n+1} / (r - g)`` (Gordon growth).
* :func:`discounted_cash_flow_value` — the full DCF: PV of the explicit-period
  cash flows plus the discounted terminal value.

Formulae (research source 01, Damodaran DCF lecture notes)
----------------------------------------------------------
* Intrinsic value: ``Value = sum_{t=1..n} CF_t / (1 + r)^t``.
* FCFF terminal value: ``TV = FCFF_{n+1} / (r - g_n)``, where ``r`` is WACC and
  ``g_n`` is the stable growth rate, with the discipline ``g_n < r`` (a stable
  firm cannot grow faster than its discount rate forever).

Why it exists / where it sits
-----------------------------
The valuation lane of the finance suite (SYNTHESIS §2). All arithmetic is exact
:class:`~decimal.Decimal` at a wide, fixed precision so results are deterministic
and reproducible (CLAUDE.md §3.11). Malformed inputs are refused fail-closed.

Security / compliance invariants upheld
---------------------------------------
Fail-closed guards (CLAUDE.md §5.6): a discount rate <= -1 (division blow-up), a
negative period, a terminal growth >= discount rate (non-convergent perpetuity),
or an empty cash-flow series are refused with ``ValueError``.
"""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal, localcontext

__all__ = [
    "DCF_PRECISION",
    "discounted_cash_flow_value",
    "present_value",
    "terminal_value",
]

# Wide fixed precision for all DCF arithmetic so powers/divisions never silently
# round at the default 28 digits (determinism — CLAUDE.md §3.11).
DCF_PRECISION = 50


def present_value(cash_flow: Decimal, rate: Decimal, period: int) -> Decimal:
    """Present value of a single cash flow: ``CF / (1 + rate) ** period``.

    Source 01 (Damodaran), core intrinsic-value identity. Exact Decimal power.

    Args:
        cash_flow: The cash flow at ``period`` (may be negative).
        rate: The per-period discount rate as a decimal (e.g. ``0.10`` for 10%).
            Must be greater than ``-1`` (else ``1 + rate <= 0`` is undefined).
        period: The period index ``t`` (``0`` = today, undiscounted). Must be >= 0.

    Returns:
        The exact present value as a :class:`~decimal.Decimal`.

    Raises:
        ValueError: If ``period < 0`` or ``rate <= -1`` (fail-closed — §5.6).
    """
    if period < 0:  # fail-closed: no negative time periods
        raise ValueError(f"period must be >= 0, got {period}")
    if rate <= Decimal(-1):  # fail-closed: 1 + rate must be strictly positive
        raise ValueError(f"discount rate must be > -1, got {rate}")
    with localcontext() as ctx:
        ctx.prec = DCF_PRECISION
        discount_factor = (Decimal(1) + rate) ** period
        return cash_flow / discount_factor


def terminal_value(
    final_cash_flow: Decimal, rate: Decimal, growth: Decimal
) -> Decimal:
    """Gordon-growth terminal value: ``CF * (1 + g) / (r - g)``.

    Source 01 (Damodaran), FCFF terminal value. ``CF * (1 + g)`` is the first
    stable-period cash flow ``CF_{n+1}``; dividing by ``(r - g)`` capitalises the
    growing perpetuity. The result is the terminal value *at the end of the
    explicit horizon* (period ``n``) — the caller discounts it back to today.

    Args:
        final_cash_flow: The last explicit-period cash flow ``CF_n``.
        rate: The discount rate ``r`` (WACC). Must exceed ``growth``.
        growth: The stable perpetual growth rate ``g_n``. Must be ``< rate``.

    Returns:
        The terminal value at period ``n`` as an exact :class:`~decimal.Decimal`.

    Raises:
        ValueError: If ``growth >= rate`` — the perpetuity does not converge and
            a stable firm cannot outgrow its discount rate forever (fail-closed,
            Damodaran's stable-growth discipline, §5.6).
    """
    if growth >= rate:  # fail-closed: non-convergent perpetuity (g must be < r)
        raise ValueError(
            f"terminal growth must be strictly less than the discount rate, "
            f"got growth {growth} >= rate {rate}"
        )
    with localcontext() as ctx:
        ctx.prec = DCF_PRECISION
        next_cash_flow = final_cash_flow * (Decimal(1) + growth)  # CF_{n+1}
        return next_cash_flow / (rate - growth)


def discounted_cash_flow_value(
    cash_flows: Sequence[Decimal],
    rate: Decimal,
    terminal_growth: Decimal | None = None,
) -> Decimal:
    """Full DCF value: PV of explicit cash flows plus discounted terminal value.

    ``cash_flows[0]`` is the period-1 cash flow, ``cash_flows[-1]`` is the final
    explicit period ``n``. When ``terminal_growth`` is given, a Gordon-growth
    terminal value is computed at period ``n`` and discounted back to today over
    ``n`` periods, then added to the explicit-period present values.

    Args:
        cash_flows: One or more projected per-period cash flows, period 1..n.
        rate: The per-period discount rate (WACC for firm value).
        terminal_growth: Optional stable growth ``g_n`` for a terminal value;
            ``None`` for a finite-horizon valuation.

    Returns:
        The exact total DCF value as a :class:`~decimal.Decimal`.

    Raises:
        ValueError: If ``cash_flows`` is empty, or any guard in
            :func:`present_value` / :func:`terminal_value` fires (fail-closed).
    """
    if not cash_flows:  # fail-closed: nothing to value
        raise ValueError("cash_flows must contain at least one period")
    with localcontext() as ctx:
        ctx.prec = DCF_PRECISION
        total = Decimal(0)
        for index, cash_flow in enumerate(cash_flows):
            period = index + 1  # cash_flows[0] is period 1, not period 0
            total += present_value(cash_flow, rate, period)
        if terminal_growth is not None:
            horizon = len(cash_flows)  # the explicit period n
            tv = terminal_value(cash_flows[-1], rate, terminal_growth)
            total += present_value(tv, rate, horizon)  # discount TV back from period n
        return total
