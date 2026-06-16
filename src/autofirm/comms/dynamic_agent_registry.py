"""Dynamic agent/topic registry for a runtime-changing org topology (A2).

What this does
--------------
Maps directed addresses (agent id / role) and pub-sub topics to their async
message handlers, and lets agents/teams be registered and DEregistered at
runtime -- the dynamic topology the synthesis calls for. The bus asks the
registry to resolve a destination; an unknown directed recipient resolves to
*nothing* (the bus then dead-letters, fail-closed), and a topic resolves to the
current set of subscribers (possibly empty).

Why it exists / where it sits
-----------------------------
"Agents/teams are added/removed at runtime" + "unknown recipient -> fail-closed
to dead-letter". The registry is the single source of truth for the live
topology; routing is pure resolution against it. Directed delivery is 1:1;
topic delivery is fan-out to every current subscriber (pub-sub).

Security / compliance invariants upheld
---------------------------------------
* **Least privilege (§5.6):** each handler is registered under exactly the
  address(es) it owns; there is no wildcard god-handler. Resolution returns only
  the handlers explicitly registered for the destination.
* **Fail-closed on unknown (§5.6):** :meth:`resolve_directed` returns ``None``
  for an unregistered recipient -- the caller MUST dead-letter, never invent a
  fallback recipient.
* **Deregistration is total:** removing an agent unsubscribes it from every topic
  in the same call, so a removed agent can never keep receiving fan-out (no
  dangling subscription leak).
"""

from __future__ import annotations

from collections.abc import Callable, Coroutine
from typing import Any

from autofirm.comms.message_envelope_contract import MessageEnvelope

__all__ = ["DynamicAgentRegistry", "MessageHandler"]

# An async handler invoked with the envelope; it performs the agent's reaction.
# Its return is ignored -- success is "returned without raising"; a raise drives
# the bus's HANDLER_ERROR dead-letter path. Typed as a coroutine function (not a
# bare Awaitable) to match AnyIO's ``start_soon`` contract used by the bus.
MessageHandler = Callable[[MessageEnvelope], Coroutine[Any, Any, None]]


class DynamicAgentRegistry:
    """Live directory of directed handlers + topic subscriptions (single-writer)."""

    def __init__(self) -> None:
        """Create an empty registry (no agents, no topics)."""
        self._directed: dict[str, MessageHandler] = {}
        # topic -> {agent_id -> handler}. agent_id keys let deregistration remove
        # an agent from every topic without scanning handler identities.
        self._topics: dict[str, dict[str, MessageHandler]] = {}

    def register_agent(self, agent_id: str, handler: MessageHandler) -> None:
        """Register (or replace) the directed handler for ``agent_id``.

        Re-registering the same id replaces the handler (a redeploy of the agent);
        this is deliberate and idempotent in effect, not an error.
        """
        if not agent_id:
            raise ValueError("agent_id must be non-empty")  # fail-closed: no anon agent
        self._directed[agent_id] = handler

    def deregister_agent(self, agent_id: str) -> None:
        """Remove an agent's directed handler AND all its topic subscriptions.

        Total removal (§5.6): after this, the agent resolves to nothing directed
        and receives no topic fan-out. Removing an unknown agent is a no-op (not an
        error) so deregistration is idempotent.
        """
        self._directed.pop(agent_id, None)
        for subscribers in self._topics.values():
            # Unsubscribe from every topic so no dangling subscription remains.
            subscribers.pop(agent_id, None)

    def subscribe(self, topic: str, agent_id: str, handler: MessageHandler) -> None:
        """Subscribe ``agent_id`` to ``topic`` with ``handler`` (pub-sub fan-out)."""
        if not topic or not agent_id:
            raise ValueError("topic and agent_id must be non-empty")  # fail-closed
        self._topics.setdefault(topic, {})[agent_id] = handler

    def unsubscribe(self, topic: str, agent_id: str) -> None:
        """Remove ``agent_id`` from ``topic`` (idempotent; unknown => no-op)."""
        subscribers = self._topics.get(topic)
        if subscribers is not None:
            subscribers.pop(agent_id, None)

    def resolve_directed(self, recipient: str) -> MessageHandler | None:
        """Return the handler for ``recipient``, or None if unregistered.

        None is the fail-closed signal: the caller dead-letters an unknown
        recipient rather than delivering it anywhere (§5.6).
        """
        return self._directed.get(recipient)

    def resolve_topic(self, topic: str) -> tuple[MessageHandler, ...]:
        """Return the current subscribers' handlers for ``topic`` (maybe empty).

        An empty tuple means the topic has no subscribers; the caller dead-letters
        with NO_TOPIC_SUBSCRIBERS so the message is never silently dropped.
        """
        subscribers = self._topics.get(topic)
        if not subscribers:
            return ()
        return tuple(subscribers.values())
