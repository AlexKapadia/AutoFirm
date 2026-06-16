"""Money primitives — exact, cent-conserving monetary arithmetic.

All monetary maths in AutoFirm flows through this package so that the
"zero numerical errors on deterministic paths" invariant (CLAUDE.md §3.11)
and the exact accounting identities of ``data-contracts.md`` §6 hold by
construction. IEEE-754 floats are deliberately never used for money.
"""
