"""Balance sheet — Assets = Liabilities + Equity, enforced exactly.

What this does
--------------
Derives the balance sheet from the ledger and enforces the fundamental
accounting identity **Assets = Liabilities + Equity** to the cent. Equity is the
sum of contributed equity (the ledger's equity accounts) **plus retained
earnings**, where retained earnings is net income from the income statement.
This is how net income flows from the income statement into equity, closing the
articulation loop.

Why it exists / where it sits
-----------------------------
The balance sheet is statement two of the three-statement articulation. Because
every journal entry balanced and revenue/expense balances close into retained
earnings, ``Assets = Liabilities + Equity`` holds by construction. The identity
is re-checked fail-closed on every build: if it ever fails to the cent, the
statement is *refused* rather than published (CLAUDE.md §3.11 zero-numerical-
error, §5.6 fail-closed).

Security / compliance invariants upheld
---------------------------------------
Read-only over the ledger. The identity check raises rather than returning a
silently-wrong statement — a balance sheet that does not balance is never
emitted.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from autofirm.finance.ledger.account_types import AccountType
from autofirm.finance.ledger.double_entry_ledger import DoubleEntryLedger
from autofirm.finance.statements.income_statement import IncomeStatement

__all__ = ["BalanceSheet"]


@dataclass(frozen=True, slots=True)
class BalanceSheet:
    """A point-in-time balance sheet that satisfies ``A = L + E`` exactly.

    Attributes:
        total_assets: Sum of all asset balances (exact Decimal).
        total_liabilities: Sum of all liability balances (exact Decimal).
        contributed_equity: Sum of equity-account balances (paid-in capital).
        retained_earnings: Net income carried into equity (exact Decimal).
    """

    total_assets: Decimal
    total_liabilities: Decimal
    contributed_equity: Decimal
    retained_earnings: Decimal

    @classmethod
    def from_ledger(cls, ledger: DoubleEntryLedger) -> BalanceSheet:
        """Build the balance sheet and enforce ``A = L + E`` fail-closed.

        Retained earnings is taken from the income statement derived from the
        same ledger, so net income flows into equity exactly. The identity is
        re-verified to the cent before the statement is returned.

        Args:
            ledger: The double-entry ledger to read.

        Returns:
            A balanced :class:`BalanceSheet`.

        Raises:
            ValueError: If ``Assets != Liabilities + Equity`` to the cent
                (fail-closed — should be unreachable on a balanced ledger, so a
                breach signals a real defect and is refused — CLAUDE.md §5.6).
        """
        total_assets = Decimal("0.00")
        total_liabilities = Decimal("0.00")
        contributed_equity = Decimal("0.00")
        for account in ledger.accounts():
            balance = ledger.balance_of(account)
            if account.type is AccountType.ASSET:
                total_assets += balance
            elif account.type is AccountType.LIABILITY:
                total_liabilities += balance
            elif account.type is AccountType.EQUITY:
                contributed_equity += balance
        # Net income closes into retained earnings -> the income statement feeds
        # equity. This is the articulation link the property tests assert.
        retained_earnings = IncomeStatement.from_ledger(ledger).net_income()

        sheet = cls(
            total_assets=total_assets,
            total_liabilities=total_liabilities,
            contributed_equity=contributed_equity,
            retained_earnings=retained_earnings,
        )
        # fail-closed: refuse to publish a balance sheet that does not balance to
        # the cent. On a correctly-built ledger this can never fire; if it does,
        # something upstream is wrong and we must NOT emit a wrong statement.
        if sheet.total_assets != sheet.total_equity_and_liabilities():
            raise ValueError(
                "balance sheet does not balance: "
                f"assets {sheet.total_assets} != L+E {sheet.total_equity_and_liabilities()}"
            )
        return sheet

    def total_equity(self) -> Decimal:
        """Equity == contributed equity + retained earnings (exact Decimal)."""
        return self.contributed_equity + self.retained_earnings

    def total_equity_and_liabilities(self) -> Decimal:
        """The right-hand side of the identity: ``L + E`` (exact Decimal)."""
        return self.total_liabilities + self.total_equity()
