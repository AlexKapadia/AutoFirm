"""Operate-phase finance checks: three statements articulate + DCF valuation.

Seeds a double-entry ledger from a scenario's public-style figures, articulates
the three statements, and asserts the cross-statement invariants hold to the cent
(the balance sheet balances; the cash-flow net ties to the cash delta), then
values the firm by DCF. These are EFFICACY checks (CLAUDE.md §3.6): they assert
the real numbers are correct/sensible, not merely that the call returned.
"""

from __future__ import annotations

from decimal import Decimal

from autofirm.e2e.public_company_scenarios import PublicCompanyScenario
from autofirm.e2e.scenario_result_contract import (
    FeatureCheck,
    FeatureName,
    FeatureStatus,
)
from autofirm.finance.ledger.account_types import Account, AccountType
from autofirm.finance.ledger.double_entry_ledger import DoubleEntryLedger
from autofirm.finance.ledger.journal_entry import JournalEntry, Posting, PostingSide
from autofirm.finance.statements.balance_sheet import BalanceSheet
from autofirm.finance.statements.cash_flow_statement import CashFlowStatement
from autofirm.finance.statements.income_statement import IncomeStatement
from autofirm.finance.valuation.discounted_cash_flow import discounted_cash_flow_value

# A fixed synthetic chart of accounts (public-style; no real PII). Cash code 1000
# is the single cash account the cash-flow statement classifies against.
_CASH = Account("1000", "Cash", AccountType.ASSET)
_EQUIP = Account("1500", "Equipment", AccountType.ASSET)
_LOAN = Account("2000", "Bank Loan", AccountType.LIABILITY)
_EQUITY = Account("3000", "Common Stock", AccountType.EQUITY)
_REVENUE = Account("4000", "Revenue", AccountType.REVENUE)
_EXPENSE = Account("5000", "Operating Expense", AccountType.EXPENSE)
_CASH_CODES = frozenset({"1000"})


def _deb(account: Account, amount: Decimal) -> Posting:
    return Posting(account, PostingSide.DEBIT, amount)


def _cre(account: Account, amount: Decimal) -> Posting:
    return Posting(account, PostingSide.CREDIT, amount)


def _seed_ledger(scenario: PublicCompanyScenario) -> DoubleEntryLedger:
    """Build a balanced double-entry ledger from the scenario's public figures."""
    ledger = DoubleEntryLedger()
    equity, loan = scenario.equity_invested, scenario.loan_principal
    revenue, opex = scenario.revenue, scenario.operating_expense
    ledger.post(JournalEntry("invest", (_deb(_CASH, equity), _cre(_EQUITY, equity))))
    ledger.post(JournalEntry("loan", (_deb(_CASH, loan), _cre(_LOAN, loan))))
    ledger.post(JournalEntry("capex", (_deb(_EQUIP, scenario.capex), _cre(_CASH, scenario.capex))))
    ledger.post(JournalEntry("revenue", (_deb(_CASH, revenue), _cre(_REVENUE, revenue))))
    ledger.post(JournalEntry("opex", (_deb(_EXPENSE, opex), _cre(_CASH, opex))))
    return ledger


def check_finance_statements(scenario: PublicCompanyScenario) -> FeatureCheck:
    """Articulate the three statements and assert the cross-statement ties hold."""
    ledger = _seed_ledger(scenario)
    income = IncomeStatement.from_ledger(ledger)
    balance = BalanceSheet.from_ledger(ledger)
    cash_flow = CashFlowStatement.from_ledger(ledger, _CASH_CODES)

    expected_net_income = scenario.revenue - scenario.operating_expense
    # The cash delta equals every cash leg: +equity +loan -capex +revenue -opex.
    expected_cash = (
        scenario.equity_invested
        + scenario.loan_principal
        - scenario.capex
        + scenario.revenue
        - scenario.operating_expense
    )
    correct = (
        income.net_income() == expected_net_income
        and balance.total_assets == balance.total_equity_and_liabilities()  # balances
        and cash_flow.net_change() == expected_cash  # cash-flow ties to cash delta
    )
    return FeatureCheck(
        feature=FeatureName.FINANCE_STATEMENTS,
        phase="operate",
        status=FeatureStatus.PASSED if correct else FeatureStatus.FAILED,
        detail="3 statements articulate; balance sheet balances; cash-flow ties",
        evidence={
            "net_income": str(income.net_income()),
            "total_assets": str(balance.total_assets),
            "cash_net_change": str(cash_flow.net_change()),
        },
    )


def check_finance_valuation(scenario: PublicCompanyScenario) -> FeatureCheck:
    """Value the firm by DCF; assert a positive, deterministic, exact result.

    Re-runs the valuation to assert determinism (identical inputs -> identical
    value) and checks the value is strictly positive for a profitable projection,
    which is the real-world-sensible expectation (a domain expert's smell test).
    """
    value = discounted_cash_flow_value(
        scenario.projected_cash_flows,
        scenario.discount_rate,
        terminal_growth=scenario.terminal_growth,
    )
    rerun = discounted_cash_flow_value(
        scenario.projected_cash_flows,
        scenario.discount_rate,
        terminal_growth=scenario.terminal_growth,
    )
    sensible = value > Decimal("0") and value == rerun
    return FeatureCheck(
        feature=FeatureName.FINANCE_VALUATION,
        phase="operate",
        status=FeatureStatus.PASSED if sensible else FeatureStatus.FAILED,
        detail="DCF firm value computed (positive, deterministic)",
        evidence={"dcf_value": str(value.quantize(Decimal("1")))},
    )
