"""Income statement — revenue minus expenses equals net income, exactly.

What this does
--------------
Derives the income statement from the ledger: total revenue, total expenses, and
**net income == revenue - expenses** (exact Decimal). Net income is the figure
that flows to retained earnings on the balance sheet, closing the articulation
loop between the two statements.

Why it exists / where it sits
-----------------------------
The income statement is statement one of the three-statement articulation
(SYNTHESIS §1: income statement -> balance sheet -> cash-flow statement). It is
derived purely from the ledger's revenue and expense balances, so it is
deterministic and reconciles to the cent (CLAUDE.md §3.11). It exposes
:meth:`net_income` for the balance sheet's retained-earnings line.

Security / compliance invariants upheld
---------------------------------------
Read-only over the ledger; it never mutates balances. All sums are exact Decimal
(never float), so ``revenue - expenses`` is exact to the cent.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from autofirm.finance.ledger.account_types import AccountType
from autofirm.finance.ledger.double_entry_ledger import DoubleEntryLedger

__all__ = ["IncomeStatement"]


@dataclass(frozen=True, slots=True)
class IncomeStatement:
    """A point-in-time income statement derived from a ledger.

    Attributes:
        total_revenue: Sum of all credit-normal revenue balances (exact Decimal).
        total_expenses: Sum of all debit-normal expense balances (exact Decimal).
    """

    total_revenue: Decimal
    total_expenses: Decimal

    @classmethod
    def from_ledger(cls, ledger: DoubleEntryLedger) -> IncomeStatement:
        """Build the income statement from the ledger's revenue/expense accounts.

        Revenue accounts are credit-normal and expense accounts debit-normal, so
        each account's stored balance is already its positive statement figure.

        Args:
            ledger: The double-entry ledger to read.

        Returns:
            An :class:`IncomeStatement` with totals summed exactly.
        """
        total_revenue = Decimal("0.00")
        total_expenses = Decimal("0.00")
        for account in ledger.accounts():
            balance = ledger.balance_of(account)
            if account.type is AccountType.REVENUE:
                total_revenue += balance  # credit-normal: balance is already positive revenue
            elif account.type is AccountType.EXPENSE:
                total_expenses += balance  # debit-normal: balance is already positive expense
        return cls(total_revenue=total_revenue, total_expenses=total_expenses)

    def net_income(self) -> Decimal:
        """Return ``revenue - expenses`` exactly (the figure feeding equity).

        This is the deterministic, zero-error core of the statement: a single
        exact Decimal subtraction (CLAUDE.md §3.11).
        """
        return self.total_revenue - self.total_expenses
