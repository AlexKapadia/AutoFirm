"""AnyIO implementation of the saga ``RuntimeAdapter`` (structured concurrency).

What this does
--------------
Implements the runtime seam on **AnyIO**, which layers Trio-style structured
concurrency over an asyncio (or Trio) backend. Child ownership is an
:func:`anyio.create_task_group` ("task group" = nursery): on exit it joins all
children, and on cancellation it cancels and joins them — orphan-free by
construction. Cancellation is delivered at AnyIO checkpoints
(:func:`anyio.lowlevel.checkpoint`) and surfaces as :class:`anyio.get_cancelled_exc_class`'s
type (the backend's native cancel exception), which must be re-raised.

Why it exists / where it sits
-----------------------------
This is candidate **AnyIO** in the ADR-001 §7 fork. It buys Trio-grade structured
cancellation (cancel scopes, guaranteed join) while running on the asyncio
backend the rest of the platform already targets — the "and, not either/or"
hybrid sweet spot (CLAUDE.md §3.5): structured-concurrency guarantees without
abandoning the asyncio ecosystem (``psycopg3``, ``httpx``).

Security / compliance invariants upheld
---------------------------------------
``checkpoint`` is a real AnyIO cancellation point, so a pending cancel is
delivered deterministically at the step boundary (fail-closed). No I/O, no secrets.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Callable, Coroutine
from contextlib import asynccontextmanager
from typing import Any, TypeVar

import anyio
import anyio.lowlevel

from ..runtime_adapter import Scope

__all__ = ["AnyioAdapter"]

_T = TypeVar("_T")


class _AnyioScope:
    """Wraps an AnyIO task group (nursery) as the adapter's structured scope."""

    def __init__(self, task_group: anyio.abc.TaskGroup) -> None:
        self._task_group = task_group

    def start(self, fn: Callable[[], Coroutine[Any, Any, Any]]) -> None:
        """Start a child task owned by the nursery (cancelled+joined on teardown)."""
        self._task_group.start_soon(fn)

    def cancel(self) -> None:
        """Fire the AnyIO cancel scope; delivered at the next checkpoint (real cancel)."""
        self._task_group.cancel_scope.cancel()


class AnyioAdapter:
    """RuntimeAdapter backed by AnyIO structured concurrency (asyncio backend)."""

    name = "anyio"
    # AnyIO's default backend is asyncio, whose cancellation exception is
    # asyncio.CancelledError. Resolving it statically (rather than via
    # get_cancelled_exc_class(), which needs a running loop) keeps the adapter
    # usable before run() is entered and matches the asyncio backend exactly.
    cancelled_exc: type[BaseException] = asyncio.CancelledError

    def run(self, main: Callable[[], Coroutine[Any, Any, _T]]) -> _T:
        """Drive ``main`` on AnyIO's default (asyncio) backend."""
        return anyio.run(main)

    @asynccontextmanager
    async def open_scope(self) -> AsyncIterator[Scope]:
        """Open an AnyIO task group (nursery) as a structured scope."""
        async with anyio.create_task_group() as task_group:
            yield _AnyioScope(task_group)

    async def spawn(self, scope: Scope, fn: Callable[[], Coroutine[Any, Any, Any]]) -> None:
        """Start ``fn`` inside the AnyIO nursery owned by ``scope``."""
        assert isinstance(scope, _AnyioScope)
        scope.start(fn)

    async def checkpoint(self, scope: Scope) -> None:
        """AnyIO cancellation checkpoint — a fired cancel scope raises here."""
        await anyio.lowlevel.checkpoint()

    @asynccontextmanager
    async def shielded(self) -> AsyncIterator[None]:
        """Shield the body from ambient cancellation via a shielded cancel scope.

        Lets compensation run to completion even after the saga's cancel scope has
        fired (exactly-once compensation must not be interrupted — fail-closed).
        """
        with anyio.CancelScope(shield=True):
            yield
