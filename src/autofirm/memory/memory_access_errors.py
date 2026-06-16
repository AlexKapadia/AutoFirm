"""Fail-closed error types for the memory layer (A4.4 governance).

What this does
--------------
Defines the small, explicit exception hierarchy the memory store raises when a
governance primitive refuses an operation. Distinct types let callers (and tests)
assert *which* control fired -- an unauthorised write (WA), a cross-owner read
attempt (PS), or an operation on a missing/forgotten record (VF) -- rather than
catching a generic error.

Why it exists / where it sits
-----------------------------
Per ``docs/research/A4-memory-and-learning-infra/SYNTHESIS.md`` L1.A4.4 the memory
layer is "fail-closed by default and enforces all five primitives". A refusal is a
*security event*, not a soft failure, so it surfaces as a typed exception the
audit/comms planes can record -- never a silent no-op that would let a poisoned or
cross-tenant operation proceed.

Security / compliance invariants upheld
---------------------------------------
* **Fail closed (§5.6):** every governance refusal is an exception; the store
  never returns a partial/empty success in place of a refusal.
"""

from __future__ import annotations

__all__ = [
    "MemoryAccessError",
    "MemoryWriteAuthorizationError",
    "PrincipalScopeViolationError",
    "RecordNotFoundError",
]


class MemoryAccessError(Exception):
    """Base class for every fail-closed memory governance refusal."""


class MemoryWriteAuthorizationError(MemoryAccessError):
    """WA: a write was refused because the author is not authorised for the scope.

    Raised when ``written_by`` does not equal the target ``owner`` and the write
    is not an explicitly-permitted shared-scope write -- no write without an
    authenticated, authorised source (A4.4 WA).
    """


class PrincipalScopeViolationError(MemoryAccessError):
    """PS: a read/operation was refused because the principal is out of scope.

    Raised when a principal attempts to reach another owner's PRIVATE record --
    retrieval is principal-scoped in the data layer, not by convention (A4.4 PS).
    """


class RecordNotFoundError(MemoryAccessError):
    """VF/RB: an operation referenced a memory id that is absent or forgotten.

    Raised by supersede/delete/get when the target id was never written or has
    been exactly deleted (VF) -- the store fails closed rather than fabricating a
    record.
    """
