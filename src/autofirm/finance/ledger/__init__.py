"""Double-entry ledger core — typed accounts and balanced journal entries.

The ledger is the single source of truth the three statements are derived from.
Its defining invariant — every journal entry has ``debits == credits`` — is
enforced fail-closed at construction, so the trial balance is always exactly
zero and the accounting identities reconcile to the cent.
"""
