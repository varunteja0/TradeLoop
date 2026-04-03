"""
In-process event bus. Start simple — evolve to Redis Pub/Sub or Kafka when needed.

The interface stays the same regardless of transport. Services emit events,
handlers react. No handler knows about any other handler.

Handlers run as fire-and-forget tasks — they do NOT block the emitter.
"""
from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from typing import Any, Callable, Coroutine, Dict, List

logger = logging.getLogger("tradeloop.events")

Handler = Callable[..., Coroutine[Any, Any, None]]


class EventBus:
    """Async in-process event bus with non-blocking fire-and-forget semantics."""

    def __init__(self) -> None:
        self._handlers: Dict[str, List[Handler]] = defaultdict(list)

    def on(self, event_name: str, handler: Handler) -> None:
        self._handlers[event_name].append(handler)

    async def emit(self, event_name: str, **kwargs: Any) -> None:
        handlers = self._handlers.get(event_name, [])
        if not handlers:
            return
        logger.info("Event emitted: %s (handlers=%d)", event_name, len(handlers))
        for handler in handlers:
            asyncio.create_task(_safe_run(handler, event_name, **kwargs))


async def _safe_run(handler: Handler, event_name: str, **kwargs: Any) -> None:
    try:
        await handler(**kwargs)
    except Exception:
        logger.exception("Handler failed for event %s", event_name)


event_bus = EventBus()
