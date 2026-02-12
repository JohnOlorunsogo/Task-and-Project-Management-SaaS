"""Kafka event producer helper."""

from __future__ import annotations

import json
import logging
from typing import Any, Optional

from aiokafka import AIOKafkaProducer

logger = logging.getLogger(__name__)


class EventProducer:
    """Async Kafka event producer."""

    def __init__(self) -> None:
        self._producer: Optional[AIOKafkaProducer] = None

    async def start(self, bootstrap_servers: str) -> None:
        self._producer = AIOKafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            key_serializer=lambda k: k.encode("utf-8") if k else None,
        )
        await self._producer.start()
        logger.info("Kafka producer started")

    async def stop(self) -> None:
        if self._producer:
            await self._producer.stop()
            logger.info("Kafka producer stopped")

    async def publish(
        self,
        topic: str,
        event: dict[str, Any],
        key: Optional[str] = None,
    ) -> None:
        if not self._producer:
            logger.warning("Kafka producer not started, skipping event: %s", topic)
            return
        try:
            await self._producer.send_and_wait(topic, value=event, key=key)
            logger.info("Published event to %s: %s", topic, event.get("event_type", "unknown"))
        except Exception:
            logger.exception("Failed to publish event to %s", topic)


# Global instance
event_producer = EventProducer()
