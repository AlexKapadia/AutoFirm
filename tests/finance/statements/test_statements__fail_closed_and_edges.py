"""Fail-closed + degenerate-edge tests for the three statements.

Exercises the nooks an auditor would probe (CLAUDE.md §3.6): empty ledgers, a
firm strong on every axis but with a single excluded cash account, multi-cash
accounts, mixed-counterpart cash entries, and the fail-closed refusals. Designed
to KILL mutants on the guard and classification logic.
"""

from decimal import Decimal

import pytest

from autofirm.finance.ledger.account_types import Account, AccountType
from autofirm.finance.ledger.double_entry_ledger import DoubleEntryLedger
from autofirm.finance.ledger.journal_entry import JournalEntry, Posting, PostingSide
from autofirm.finance.statements.balance_sheet import BalanceSheet
from autofirm.finance.statements.cash_flow_statement import CashFlowStatement
from autofirm.finance.statements.income_statement import IncomeStatement

CASH = Account("1000", "Cash", AccountType.ASSET)
BANK = Account("1010", "Bank", AccountType.ASSET)
EQUIP = Account("1500", "Equipment", AccountType.ASSET)
LOAN = Account("2000", "Bank Loan", AccountType.LIABILITY)
EQUITY = Account("3000", "Common Stock", AccountType.EQUITY)
REVENUE = Account("4000", "Sales", AccountType.REVENUE)
EXPENSE = Account("5000", "Rent", AccountType.EXPENSE)


def _deb(a: Account, m: str) -> Posting:
    return Posting(a, PostingSide.DEBIT, Decimal(m))


def _cre(a: Account, m: str) -> Posting:
    return Posting(a, PostingSide.CREDIT, Decimal(m))


# --------------------------------------------------------------------------- #
# Degenerate inputs.                                                           #
# --------------------------------------------------------------------------- #


def test_empty_ledger_income_statement_is_all_zero() -> None:
    inc = IncomeStatement.from_ledger(DoubleEntryLedger())
    assert inc.total_revenue == Decimal("0.00")
    assert inc.total_expenses == Decimal("0.00")
    assert inc.net_income() == Decimal("0.00")


def test_empty_ledger_balance_sheet_balances_at_zero() -> None:
    bs = BalanceSheet.from_ledger(DoubleEntryLedger())
    assert bs.total_assets == Decimal("0.00")
    assert bs.total_equity_and_liabilities() == Decimal("0.00")


def test_empty_ledger_cash_flow_is_zero_and_ties() -> None:
    cfs = CashFlowStatement.from_ledger(DoubleEntryLedger(), frozenset({"1000"}))
    assert cfs.net_change() == Decimal("0.00")


def test_net_loss_is_negative_retained_earnings() -> None:
    # Expenses exceed revenue -> net loss reduces equity below contributed.
    ledger = DoubleEntryLedger()
    ledger.post(JournalEntry("invest", (_deb(CASH, "1000.00"), _cre(EQUITY, "1000.00"))))
    ledger.post(JournalEntry("sale", (_deb(CASH, "100.00"), _cre(REVENUE, "100.00"))))
    ledger.post(JournalEntry("opex", (_deb(EXPENSE, "300.00"), _cre(CASH, "300.00"))))
    inc = IncomeStatement.from_ledger(ledger)
    bs = BalanceSheet.from_ledger(ledger)
    assert inc.net_income() == Decimal("-200.00")  # 100 - 300
    assert bs.retained_earnings == Decimal("-200.00")
    assert bs.total_equity() == Decimal("800.00")  # 1000 - 200
    assert bs.total_assets == bs.total_equity_and_liabilities()


# --------------------------------------------------------------------------- #
# Cash-flow classification edges + multi-cash accounts.                        #
# --------------------------------------------------------------------------- #


def test_two_cash_accounts_both_count_toward_the_tie() -> None:
    ledger = DoubleEntryLedger()
    ledger.post(JournalEntry("invest", (_deb(CASH, "5000.00"), _cre(EQUITY, "5000.00"))))
    # Move cash to a second cash account (an internal transfer): both are cash,
    # so the net cash delta is unchanged and the statement still ties.
    ledger.post(JournalEntry("transfer", (_deb(BANK, "2000.00"), _cre(CASH, "2000.00"))))
    cfs = CashFlowStatement.from_ledger(ledger, frozenset({"1000", "1010"}))
    total_cash = ledger.balance_of(CASH) + ledger.balance_of(BANK)
    assert cfs.net_change() == total_cash == Decimal("5000.00")


def test_internal_cash_transfer_contributes_zero() -> None:
    # An entry whose only legs are cash<->cash moves zero NET cash; it must not
    # be miscounted into any activity bucket.
    ledger = DoubleEntryLedger()
    ledger.post(JournalEntry("invest", (_deb(CASH, "100.00"), _cre(EQUITY, "100.00"))))
    ledger.post(JournalEntry("transfer", (_deb(BANK, "40.00"), _cre(CASH, "40.00"))))
    cfs = CashFlowStatement.from_ledger(ledger, frozenset({"1000", "1010"}))
    # Only the financing inflow of 100 should appear.
    assert cfs.financing == Decimal("100.00")
    assert cfs.operating == Decimal("0.00")
    assert cfs.investing == Decimal("0.00")
    assert cfs.net_change() == Decimal("100.00")


def test_classification_uses_dominant_non_cash_leg_deterministically() -> None:
    # A cash entry with two non-cash legs of different activity types is
    # classified by the LARGEST leg -> deterministic, repeatable.
    ledger = DoubleEntryLedger()
    # Cash 5000 in; counter legs: revenue 3000 (operating) + loan 2000 (financing).
    ledger.post(
        JournalEntry(
            "mixed",
            (_deb(CASH, "5000.00"), _cre(REVENUE, "3000.00"), _cre(LOAN, "2000.00")),
        )
    )
    cfs = CashFlowStatement.from_ledger(ledger, frozenset({"1000"}))
    # Largest non-cash leg is revenue (3000) -> the whole 5000 goes to operating.
    assert cfs.operating == Decimal("5000.00")
    # The net still ties exactly regardless of bucket choice.
    assert cfs.net_change() == ledger.balance_of(CASH) == Decimal("5000.00")


def test_classification_is_deterministic_across_repeated_builds() -> None:
    ledger = DoubleEntryLedger()
    ledger.post(JournalEntry("invest", (_deb(CASH, "9999.99"), _cre(EQUITY, "9999.99"))))
    ledger.post(JournalEntry("buy", (_deb(EQUIP, "1234.56"), _cre(CASH, "1234.56"))))
    first = CashFlowStatement.from_ledger(ledger, frozenset({"1000"}))
    second = CashFlowStatement.from_ledger(ledger, frozenset({"1000"}))
    assert first == second  # identical input -> identical output (determinism)


# --------------------------------------------------------------------------- #
# Fail-closed refusals.                                                        #
# --------------------------------------------------------------------------- #


def test_cash_flow_requires_a_cash_account() -> None:
    with pytest.raises(ValueError, match="at least one cash account"):
        CashFlowStatement.from_ledger(DoubleEntryLedger(), frozenset())


class _CorruptLedger(DoubleEntryLedger):
    """A ledger that reports a deliberately wrong asset balance.

    Simulates upstream data corruption so the balance sheet's fail-closed
    identity check (A = L + E) is actually exercised — it is otherwise
    unreachable on a correctly-built ledger.
    """

    def balance_of(self, account: Account) -> Decimal:
        base = super().balance_of(account)
        if account.code == EQUIP.code:
            return base + Decimal("0.01")  # inject a one-cent asset overstatement
        return base


def test_balance_sheet_refuses_to_publish_when_it_does_not_balance() -> None:
    # A corrupted ledger overstates assets by a cent; the statement must REFUSE.
    ledger = _CorruptLedger()
    ledger.post(JournalEntry("invest", (_deb(CASH, "100.00"), _cre(EQUITY, "100.00"))))
    ledger.post(JournalEntry("buy", (_deb(EQUIP, "40.00"), _cre(CASH, "40.00"))))
    with pytest.raises(ValueError, match="does not balance"):
        BalanceSheet.from_ledger(ledger)


def test_cash_flow_refuses_when_net_does_not_tie() -> None:
    # Same corruption: cash delta as seen by the statement won't match the
    # classified flows, so the cash-flow tie check must REFUSE.
    ledger = _CorruptLedger()
    ledger.post(JournalEntry("invest", (_deb(CASH, "100.00"), _cre(EQUITY, "100.00"))))
    ledger.post(JournalEntry("buy", (_deb(EQUIP, "40.00"), _cre(CASH, "40.00"))))
    # Corrupt EQUIP only, so CASH balance and classified flows still agree —
    # use a cash-corrupting ledger instead to break the tie.

    class _CashCorruptLedger(DoubleEntryLedger):
        def balance_of(self, account: Account) -> Decimal:
            base = super().balance_of(account)
            if account.code == CASH.code:
                return base + Decimal("0.01")  # overstate cash vs the flows
            return base

    bad = _CashCorruptLedger()
    bad.post(JournalEntry("invest", (_deb(CASH, "100.00"), _cre(EQUITY, "100.00"))))
    with pytest.raises(ValueError, match="does not tie"):
        CashFlowStatement.from_ledger(bad, frozenset({"1000"}))
