"""
In-process event bus. Start simple — evolve to Redis Pub/Sub or Kafka when needed.

The interface stays the same regardless of transport. Services emit events,
handlers react. No handler knows about any other handler.
"""
from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from typing import Any, Callable, Coroutine, Dict, List

logger = logging.getLogger("tradeloop.events")

Handler = Callable[..., Coroutine[Any, Any, None]]


class EventBus:
    """Async in-process event bus with fire-and-forget semantics."""

    def __init__(self) -> None:
        self._handlers: Dict[str, List[Handler]] = defaultdict(list)

    def on(self, event_name: str, handler: Handler) -> None:
        self._handlers[event_name].append(handler)
        logger.debug("Handler registered for event: %s", event_name)

    async def emit(self, event_name: str, **kwargs: Any) -> None:
        handlers = self._handlers.get(event_name, [])
        if not handlers:
            return
        logger.info("Event emitted: %s (handlers=%d)", event_name, len(handlers))
        for handler in handlers:
            try:
                await handler(**kwargs)
            except Exception:
                logger.exception("Handler failed for event %s", event_name)


# Singleton — import this everywhere
event_bus = EventBus()
