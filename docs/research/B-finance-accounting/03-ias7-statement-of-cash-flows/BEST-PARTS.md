# BEST-PARTS — IAS 7 / Cash-flow standard

## What AutoFirm ADOPTS (and the build implication)

1. **The cash-flow statement is a derived, three-bucket structure: Operating / Investing / Financing.** Build implication for `L2.B4`: AutoFirm's 3-statement model represents CFS as a typed object `CashFlowStatement { cfo, cfi, cff }` whose total equals the period change in `cash_and_equivalents` on the balance sheet. This becomes a **hard articulation invariant** (see #3).

2. **Indirect method as the engineering default, direct method supported.** Real-world filings (SEC/EDGAR data, source 05) overwhelmingly use the indirect method. Build implication: CFO is built as `net_income + non_cash_adjustments (D&A, etc.) +/- changes_in_working_capital`. This is also exactly the bridge the FCFF/FCFE formulae (source 01) consume — so the CFS and the DCF engine share one working-capital and D&A representation (no double bookkeeping).

3. **Articulation = the fail-closed correctness invariant of the whole finance suite.** From IAS 7 + the three-statement linkage: (a) ending cash on CFS == cash on balance sheet; (b) net income flows to retained earnings in equity; (c) CFS total == delta(cash). Build implication: a deterministic checker `assert balance_sheet.balances() and cfs.ties_to_cash_delta()` runs on every model; **a single failed tie is a fail-closed error** (CLAUDE §3.11 zero-numerical-error). This is the single highest-value adversarial/property test in the finance branch: generate random but internally-consistent transactions and assert Assets == Liabilities + Equity and the cash tie hold to the cent.

4. **Standard-defined definitions remove ambiguity and overfitting.** Using IAS 7's exact category definitions (and FASB ASC 230 as the US cross-check) means the model classifies line items by a cited rule, not by taste -> generality across IFRS- and GAAP-reporting companies on the industry panel.

5. **2016 financing-liabilities reconciliation** -> a disclosure the model can auto-produce when debt schedules change, supporting the "explain every decision" report (CLAUDE §3.11).

## What AutoFirm REJECTS (and why)
- **Reject treating the cash balance as a free input.** It must be the residual of the articulated model; hard-coding it breaks the tie-out invariant and is a classic spreadsheet bug.
- **Reject method lock-in to direct-only.** IAS 7 encourages direct, but forcing it would diverge from the indirect-method data AutoFirm actually ingests from filings; support both, default indirect.

## Generality check
The three-bucket structure and the articulation invariants are standard-defined and apply identically to a SaaS firm, a manufacturer, a restaurant, or a bank-adjacent fintech (the fixed industry panel). Industry differences appear only in *which line items* populate each bucket, never in the invariant.
