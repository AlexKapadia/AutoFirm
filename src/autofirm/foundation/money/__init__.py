"""Money primitives — exact, cent-conserving monetary arithmetic.

All monetary maths in AutoFirm flows through this package so that the
"zero numerical errors on deterministic paths" invariant (CLAUDE.md §3.11)
and the exact accounting identities of ``data-contracts.md`` §6 hold by
construction. IEEE-754 floats are deliberately never used for money.

* :mod:`~autofirm.foundation.money.exact_money_arithmetic` — exact minor-unit
  allocation (largest-remainder) that never creates or loses a cent.
* :mod:`~autofirm.foundation.money.money_amount` — the currency-aware
  :class:`Money` value type (Decimal amount + ISO-4217 currency, fail-closed).
"""

from __future__ import annotations

from autofirm.foundation.money.exact_money_arithmetic import (
    allocate,
    from_minor_units,
    minor_units,
)
from autofirm.foundation.money.money_amount import (
    ISO4217_MINOR_UNIT_EXPONENT,
    LEDGER_ROUNDING,
    Money,
    minor_unit_exponent,
)

__all__ = [
    "ISO4217_MINOR_UNIT_EXPONENT",
    "LEDGER_ROUNDING",
    "Money",
    "allocate",
    "from_minor_units",
    "minor_unit_exponent",
    "minor_units",
]
