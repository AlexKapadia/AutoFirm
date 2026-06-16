"""Trio implementation of the saga ``RuntimeAdapter`` (native structured concurrency).

What this does
--------------
Implements the runtime seam on **Trio**, the reference structured-concurrency
runtime. Child ownership is a :func:`trio.open_nursery`: a nursery cannot be
exited until every child it spawned has finished, and on cancellation the nursery
cancels and joins all children — orphan-free is a *language-level* guarantee, not
a convention. Cancellation is delivered at Trio checkpoints
(:func:`trio.lowlevel.checkpoint`) and raised as :class:`trio.Cancelled`, which
Trio enforces you must let propagate (re-raising a stray ``Cancelled`` is a
runtime error) — the strongest compile-/structure-level cancellation guarantee of
the three candidates.

Why it exists / where it sits
-----------------------------
This is candidate **Trio** in the ADR-001 §7 fork: the gold standard for the
"no orphaned tasks on cancel" property, at the cost of a separate event-loop
ecosystem (no native asyncio-library interop without a bridge).

Security / compliance invariants upheld
---------------------------------------
``checkpoint`` is a real Trio cancellation point (fail-closed cancel delivery at
the step boundary). No I/O, no secrets — a pure shim.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Callable, Coroutine
from contextlib import asynccontextmanager
from typing import Any, TypeVar

import trio
import trio.lowlevel

from ..runtime_adapter import Scope

__all__ = ["TrioAdapter"]

_T = TypeVar("_T")


class _TrioScope:
    """Wraps a Trio nursery as the adapter's structured scope."""

    def __init__(self, nursery: trio.Nursery) -> None:
        self._nursery = nursery

    def start(self, fn: Callable[[], Coroutine[Any, Any, Any]]) -> None:
        """Start a child task owned by the nursery (joined-or-cancelled on exit)."""
        self._nursery.start_soon(fn)

    def cancel(self) -> None:
        """Fire the Trio cancel scope; delivered at the next checkpoint (real cancel).

        Trio forbids manually raising/catching ``trio.Cancelled``; cancellation
        MUST originate from a cancel scope. This is the faithful Trio cancel path.
        """
        self._nursery.cancel_scope.cancel()


class TrioAdapter:
    """RuntimeAdapter backed by Trio's native structured concurrency."""

    name = "trio"
    cancelled_exc: type[BaseException] = trio.Cancelled

    def run(self, main: Callable[[], Coroutine[Any, Any, _T]]) -> _T:
        """Drive ``main`` on the Trio event loop."""
        return trio.run(main)

    @asynccontextmanager
    async def open_scope(self) -> AsyncIterator[Scope]:
        """Open a Trio nursery as a structured scope (cancel+join on exit)."""
        async with trio.open_nursery() as nursery:
            yield _TrioScope(nursery)

    async def spawn(self, scope: Scope, fn: Callable[[], Coroutine[Any, Any, Any]]) -> None:
        """Start ``fn`` inside the Trio nursery owned by ``scope``."""
        assert isinstance(scope, _TrioScope)
        scope.start(fn)

    async def checkpoint(self, scope: Scope) -> None:
        """Trio cancellation checkpoint — a fired cancel scope raises here."""
        await trio.lowlevel.checkpoint()

    async def sleep(self, seconds: float) -> None:
        """Cancellable sleep modelling in-step work."""
        await trio.sleep(seconds)

    @asynccontextmanager
    async def shielded(self) -> AsyncIterator[None]:
        """Shield the body from ambient cancellation via a shielded cancel scope.

        Trio's ``CancelScope(shield=True)`` lets compensation run to completion
        even though the saga's cancel scope has fired — required so exactly-once
        compensation is never interrupted half-way (fail-closed).
        """
        with trio.CancelScope(shield=True):
            yield
