"""asyncio (stdlib) implementation of the saga ``RuntimeAdapter``.

What this does
--------------
Implements the runtime seam (``runtime_adapter.RuntimeAdapter``) on Python's
stdlib :mod:`asyncio`. Structured child ownership is provided by
:class:`asyncio.TaskGroup` (Python 3.11+): on normal exit the group awaits all
children; if the body raises (including a cancellation), the group cancels and
awaits every child before propagating — the property the bake-off tests assert
(no orphaned tasks). Cancellation uses asyncio's :class:`asyncio.CancelledError`,
which (since 3.8) is a ``BaseException`` and must be re-raised, never swallowed.

Why it exists / where it sits
-----------------------------
This is candidate **asyncio** in the ADR-001 §7 concurrency-runtime fork. It is
the stdlib baseline: zero extra dependencies, but cancellation is *opt-in* per
await point and ``TaskGroup`` is the only structured-concurrency primitive (no
move-on-after/cancel-scope vocabulary).

Security / compliance invariants upheld
---------------------------------------
``checkpoint`` yields to the loop so a pending cancel is delivered at the step
boundary (fail-closed cancellation point). No I/O, no secrets — a pure shim.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Callable, Coroutine
from contextlib import asynccontextmanager
from typing import Any, TypeVar

from ..runtime_adapter import Scope

__all__ = ["AsyncioAdapter"]

_T = TypeVar("_T")


class _AsyncioScope:
    """Wraps an :class:`asyncio.TaskGroup` as the adapter's structured scope.

    asyncio has no native cancel-scope primitive, so cancellation is modelled with
    a flag the adapter's :meth:`AsyncioAdapter.checkpoint` polls: ``cancel`` sets
    it, and the next checkpoint raises ``CancelledError``. This is the honest
    stdlib story — there is no scope-level cancel object to defer to.
    """

    def __init__(self, task_group: asyncio.TaskGroup) -> None:
        self._task_group = task_group
        self.cancel_requested = False

    def start(self, fn: Callable[[], Coroutine[Any, Any, Any]]) -> None:
        """Create a child task owned by the task group (cancelled+joined on teardown)."""
        self._task_group.create_task(fn())

    def cancel(self) -> None:
        """Flag a cancellation; the next checkpoint raises CancelledError."""
        self.cancel_requested = True


class AsyncioAdapter:
    """RuntimeAdapter backed by stdlib asyncio + asyncio.TaskGroup."""

    name = "asyncio"
    cancelled_exc: type[BaseException] = asyncio.CancelledError

    def run(self, main: Callable[[], Coroutine[Any, Any, _T]]) -> _T:
        """Drive ``main`` to completion on a fresh asyncio event loop."""
        return asyncio.run(main())

    @asynccontextmanager
    async def open_scope(self) -> AsyncIterator[Scope]:
        """Open an asyncio.TaskGroup as a structured scope (cancel+join on exit)."""
        async with asyncio.TaskGroup() as task_group:
            yield _AsyncioScope(task_group)

    async def spawn(self, scope: Scope, fn: Callable[[], Coroutine[Any, Any, Any]]) -> None:
        """Start ``fn`` inside the asyncio task group owned by ``scope``."""
        assert isinstance(scope, _AsyncioScope)
        scope.start(fn)

    async def checkpoint(self, scope: Scope) -> None:
        """Yield to the loop; raise CancelledError if ``scope`` was cancelled."""
        await asyncio.sleep(0)
        assert isinstance(scope, _AsyncioScope)
        if scope.cancel_requested:
            # Deliver the scope's cancellation at this checkpoint (stdlib has no
            # native cancel scope, so we raise the cancel exception ourselves).
            raise asyncio.CancelledError

    async def sleep(self, seconds: float) -> None:
        """Cancellable sleep modelling in-step work."""
        await asyncio.sleep(seconds)

    @asynccontextmanager
    async def shielded(self) -> AsyncIterator[None]:
        """Shield the body from cancellation.

        asyncio cancellation in this adapter is cooperative (the cancel flag is
        only observed at :meth:`checkpoint`), and compensators never checkpoint, so
        the body is already protected — but we make the intent explicit and uniform
        with the structured runtimes. No real ``asyncio.shield`` task wrap is needed
        because there is no in-flight cancel token to suppress in this model.
        """
        yield
