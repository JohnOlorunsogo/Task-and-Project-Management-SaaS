"""Kafka event consumer helper."""

from __future__ import annotations

import json
import logging
from typing import Any, Callable, Coroutine, Optional

from aiokafka import AIOKafkaConsumer

logger = logging.getLogger(__name__)

EventHandler = Callable[[dict[str, Any]], Coroutine[Any, Any, None]]


class EventConsumer:
    """Async Kafka event consumer."""

    def __init__(self) -> None:
        self._consumer: Optional[AIOKafkaConsumer] = None
        self._handlers: dict[str, list[EventHandler]] = {}

    def on(self, event_type: str, handler: EventHandler) -> None:
        """Register a handler for a specific event type."""
        self._handlers.setdefault(event_type, []).append(handler)

    async def start(
        self,
        bootstrap_servers: str,
        topics: list[str],
        group_id: str,
    ) -> None:
        self._consumer = AIOKafkaConsumer(
            *topics,
            bootstrap_servers=bootstrap_servers,
            group_id=group_id,
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
            auto_offset_reset="earliest",
            enable_auto_commit=True,
        )
        await self._consumer.start()
        logger.info("Kafka consumer started for topics: %s", topics)

    async def stop(self) -> None:
        if self._consumer:
            await self._consumer.stop()
            logger.info("Kafka consumer stopped")

    async def consume(self) -> None:
        """Main consume loop — call from an asyncio task."""
        if not self._consumer:
            raise RuntimeError("Consumer not started")
        async for msg in self._consumer:
            event = msg.value
            event_type = event.get("event_type", "")
            handlers = self._handlers.get(event_type, [])
            if not handlers:
                logger.debug("No handler for event type: %s", event_type)
                continue
            for handler in handlers:
                try:
                    await handler(event)
                except Exception:
                    logger.exception("Error handling event %s", event_type)
