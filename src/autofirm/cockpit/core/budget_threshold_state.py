"""The budget-band classifier: (spent, budget) -> OK / WARN_50 / WARN_80 / CRIT_95.

What this does
--------------
:func:`classify_budget_band` is a PURE, boundary-exact classifier mapping a cumulative
spend and a budget (both :class:`~autofirm.foundation.money.money_amount.Money`) onto one
of four warning bands at the 50 / 80 / 95 % cutoffs. It uses **integer
cross-multiplication** on the underlying ``Decimal`` amounts — never a float ratio — so the
classic ``0.1 + 0.2`` drift can never push a spend onto the wrong side of an edge
(cockpit-research/PLAN.md §1.1; the ~100% mutation target).

Why it exists / where it sits
-----------------------------
The spend rollup presenter attaches a band to every node so the operator sees at a glance
who is approaching their budget. Keeping the classifier a tiny pure function makes the
exact-edge behaviour trivially enumerable by the test suite and mutmut. Sits in the pure
core; depends only on the foundation ``Money`` type (Decimal-backed, no I/O).

Security / compliance invariants upheld
---------------------------------------
* **Zero float (CLAUDE.md §3.11):** the percentage comparison is ``spent.amount * 100``
  vs ``threshold * budget.amount`` in ``Decimal`` — no division, no float, no rounding, so
  an exactly-50% spend lands deterministically in ``WARN_50``.
* **Inclusive-from-below edges:** a band is entered the instant spend REACHES the
  threshold (``>=``), so on/just-over/just-under are distinct and exact.
* **Fail-closed (§5.6):** a non-positive budget (division-by-zero / undefined %), a
  negative spend, a cross-currency comparison, or a non-``Money`` argument is refused.
"""

from __future__ import annotations

from decimal import Decimal
from enum import IntEnum

from autofirm.foundation.money.money_amount import Money

__all__ = ["BudgetBand", "classify_budget_band"]


class BudgetBand(IntEnum):
    """The four budget-utilisation bands, ordered least → most severe.

    ``IntEnum`` so callers (and the monotonicity property test) can compare severity.
    """

    OK = 0  # under 50% of budget consumed
    WARN_50 = 1  # at/over 50%, under 80%
    WARN_80 = 2  # at/over 80%, under 95%
    CRIT_95 = 3  # at/over 95% (includes at- and over-budget)


# The band cutoffs as integer percents. Cross-multiplying by these (rather than dividing
# spend by budget) keeps the comparison exact in Decimal with no float and no rounding.
_CUTOFF_PERCENTS: tuple[tuple[int, BudgetBand], ...] = (
    (95, BudgetBand.CRIT_95),  # checked high→low so the most severe matching band wins
    (80, BudgetBand.WARN_80),
    (50, BudgetBand.WARN_50),
)
_HUNDRED = Decimal(100)


def classify_budget_band(spent: Money, budget: Money) -> BudgetBand:
    """Classify cumulative ``spent`` against ``budget`` into a :class:`BudgetBand` (PURE).

    The comparison is exact integer cross-multiplication: spend is in band *b* iff
    ``spent.amount * 100 >= cutoff_percent * budget.amount``. Edges are inclusive from
    below, so a spend EXACTLY at a cutoff enters the more-severe band.

    Args:
        spent: The cumulative amount spent so far (``>= 0``, same currency as ``budget``).
        budget: The budget ceiling (``> 0``).

    Returns:
        The most severe band whose cutoff ``spent`` has reached, or :data:`BudgetBand.OK`.

    Raises:
        TypeError: If either argument is not a :class:`Money` (fail-closed).
        ValueError: If ``budget`` is not strictly positive, ``spent`` is negative, or the
            two amounts are different currencies (fail-closed — an undefined comparison).
    """
    # fail-closed: refuse non-Money so a bare Decimal/float/str can never be compared as money
    if not isinstance(spent, Money):
        raise TypeError(f"spent must be Money, not {type(spent).__name__}")
    if not isinstance(budget, Money):
        raise TypeError(f"budget must be Money, not {type(budget).__name__}")
    # fail-closed: cross-currency % is meaningless — refuse rather than compare raw amounts
    if spent.currency != budget.currency:
        raise ValueError(
            f"cannot compare {spent.currency} spend against {budget.currency} budget"
        )
    # fail-closed: a non-positive budget makes "% of budget" undefined (div-by-zero / sign
    # inversion); refuse rather than silently classify.
    if budget.amount <= 0:
        raise ValueError("budget must be strictly positive to classify a band")
    # fail-closed: a negative cumulative spend is nonsensical for utilisation; refuse it.
    if spent.amount < 0:
        raise ValueError("spent must be non-negative to classify a band")

    scaled_spent = spent.amount * _HUNDRED  # exact Decimal; no division anywhere
    for cutoff_percent, band in _CUTOFF_PERCENTS:
        # Inclusive-from-below: reaching the cutoff (>=) enters the band. Cross-multiplied
        # so the test is exact: spent% >= cutoff  ⇔  spent*100 >= cutoff*budget.
        if scaled_spent >= cutoff_percent * budget.amount:
            return band
    return BudgetBand.OK
