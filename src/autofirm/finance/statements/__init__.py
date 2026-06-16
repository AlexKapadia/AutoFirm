"""The three core financial statements, derived deterministically from the ledger.

Income statement (revenue - expenses = net income), balance sheet (Assets =
Liabilities + Equity, with net income flowing into retained earnings), and the
cash-flow statement (operating/investing/financing, whose net ties exactly to
the balance-sheet cash delta). Every cross-statement identity is enforced
fail-closed to the cent (CLAUDE.md §3.11).
"""
