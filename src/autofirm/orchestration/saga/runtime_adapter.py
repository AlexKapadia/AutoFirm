"""The thin runtime seam the saga executor is written against (bake-off boundary).

What this does
--------------
Defines the minimal ``RuntimeAdapter`` protocol that abstracts the *only* things a
saga executor needs from an async concurrency runtime, so the saga semantics
(``saga_executor``) are written **once** and the runtime is swapped underneath.
The seam is deliberately tiny — exactly the primitives where asyncio, AnyIO, and
Trio differ in cancellation/structured-concurrency behaviour:

  * ``run(coro)``        — enter the runtime's event loop and drive ``coro`` to done.
  * ``open_scope()``     — an async context manager giving a *structured* child
                           scope (a nursery / task group). On normal exit it joins
                           all children; on cancellation it cancels and joins them
                           — the guarantee under test (no orphaned tasks).
  * ``spawn(scope, fn)`` — start a child task inside ``scope``.
  * ``checkpoint()``     — a cancellation checkpoint (yield to the scheduler so a
                           pending cancel can be delivered at a step boundary).
  * ``cancelled_exc``    — the runtime's cancellation exception type, so the
                           executor can re-raise it (never swallow a cancel —
                           that is the classic structured-concurrency violation).

Why it exists / where it sits
-----------------------------
ADR-001 §7 escalates the runtime choice as a genuine fork because "structured
concurrency's cancellation-scope guarantees may materially harden the
compensator/idempotent-replay invariants against orphaned tasks on cancellation —
a correctness, not style, question." This protocol is the apples-to-apples
boundary: identical saga logic, three adapters. Where a guarantee is *structural*
(a compile-/scope-level property of a nursery) rather than runtime-call-shaped,
the adapter cannot capture it; that residue is measured separately as the
clarity/structure proxy in the results doc, exactly as the experiment brief allows.

Security / compliance invariants upheld
---------------------------------------
The executor must re-raise ``cancelled_exc`` so a cancellation always propagates
(fail-closed: never convert a cancel into a silent success). Adapters perform no
I/O and hold no secrets; they are pure scheduling shims.
"""

from __future__ import annotations

from collections.abc import Callable, Coroutine
from contextlib import AbstractAsyncContextManager
from typing import Any, Protocol, TypeVar, runtime_checkable

__all__ = ["RuntimeAdapter", "Scope"]

_T = TypeVar("_T")


@runtime_checkable
class Scope(Protocol):
    """A structured child scope (nursery / task group) opened by an adapter.

    Spawning happens via ``RuntimeAdapter.spawn`` so the spawn call shape is
    uniform across runtimes whose nursery APIs differ. ``cancel`` requests a
    *real* cancellation of the scope — the faithful, per-runtime cancel path the
    bake-off needs (raising the runtime's cancel exception by hand is illegal in
    Trio, so cancellation MUST originate from the scope itself).
    """

    def cancel(self) -> None:
        """Request real cancellation of this scope (delivered at the next checkpoint)."""
        ...


@runtime_checkable
class RuntimeAdapter(Protocol):
    """Minimal async-runtime seam the saga executor depends on (the bake-off API).

    Implementations: ``runtimes/asyncio_adapter.py``, ``anyio_adapter.py``,
    ``trio_adapter.py``. Each must uphold the documented cancellation/join
    semantics so the saga invariants hold identically regardless of runtime.
    """

    name: str
    cancelled_exc: type[BaseException]

    def run(self, main: Callable[[], Coroutine[Any, Any, _T]]) -> _T:
        """Enter the runtime's event loop, drive ``main`` to completion, return it."""
        ...

    def open_scope(self) -> AbstractAsyncContextManager[Scope]:
        """Open a structured child scope that joins (or cancels+joins) on exit."""
        ...

    async def spawn(self, scope: Scope, fn: Callable[[], Coroutine[Any, Any, Any]]) -> None:
        """Start ``fn`` as a child task inside ``scope`` (structured ownership)."""
        ...

    async def checkpoint(self, scope: Scope) -> None:
        """Cancellation checkpoint: deliver a pending cancel for ``scope`` here.

        Structured runtimes (AnyIO/Trio) ignore ``scope`` and rely on their fired
        cancel scope; asyncio polls ``scope``'s cancel flag because the stdlib has
        no scope-level cancel object.
        """
        ...

    async def sleep(self, seconds: float) -> None:
        """Cancellable sleep (used to model in-step work that a cancel can interrupt)."""
        ...

    def shielded(self) -> AbstractAsyncContextManager[None]:
        """A scope that shields its body from ambient cancellation.

        Compensation MUST run to completion even though the saga was cancelled: a
        rollback interrupted half-way would leave inconsistent state and violate
        exactly-once compensation (fail-closed — CLAUDE.md §5.6). AnyIO/Trio give
        a real ``CancelScope(shield=True)``; asyncio has no scope shield, so its
        adapter runs the body via ``asyncio.shield`` semantics.
        """
        ...
