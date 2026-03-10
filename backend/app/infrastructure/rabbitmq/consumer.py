import aio_pika
import json
import logging
from typing import Callable, Awaitable, Dict, Any, Optional, List

logger = logging.getLogger(__name__)


class RabbitMQConsumer:
    """
    צרכן RabbitMQ. אם מועברת רשימת exchanges – התור נקשרת לכולם (תור אחד לכל המיילים/פוש).
    """

    def __init__(
        self,
        rabbit_client,
        queue_name: str,
        exchange_name: Optional[str] = None,
        exchange_names: Optional[List[str]] = None,
    ):
        self._client = rabbit_client
        self.queue_name = queue_name
        if exchange_names is not None:
            self._exchange_names = exchange_names
        else:
            self._exchange_names = [exchange_name or "system_events"]

    async def _setup(self) -> aio_pika.abc.AbstractQueue:
        """מכריז על תור וקושר אותו לכל ה-exchanges (תור אחד מקבל הודעות מכל הדומיינים)."""
        channel = await self._client.get_channel()
        await channel.set_qos(prefetch_count=10)

        queue = await channel.declare_queue(self.queue_name, durable=True)
        for ex_name in self._exchange_names:
            exchange = await channel.declare_exchange(
                ex_name, aio_pika.ExchangeType.TOPIC, durable=True
            )
            await queue.bind(exchange, routing_key="#")
            logger.debug("Queue %s bound to exchange %s", self.queue_name, ex_name)
        return queue

    async def consume(self, callback: Callable[[Dict[str, Any], str], Awaitable[None]]):
        """אחראי רק על לופ ההאזנה והעברת הודעות ל-Callback"""
        queue = await self._setup()
        logger.info(f"✅ Consumer ready on '{self.queue_name}'")

        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                await self._process_message(message, callback)

    async def _process_message(self, message, callback):
        """ניהול לוגיקת העיבוד של הודעה בודדת.
        בהצלחה: ack. בכישלון: nack עם requeue=True – ההודעה חוזרת לתור (התנהגות סטנדרטית)."""
        try:
            payload = json.loads(message.body)
            logger.info(
                "[NOTIF] RabbitMQ: received routing_key=%s payload_keys=%s",
                message.routing_key,
                list(payload.keys()) if isinstance(payload, dict) else "?",
            )
            await callback(payload, message.routing_key)
            await message.ack()
        except Exception as e:
            logger.error(
                "Failed to process message (nack with requeue): %s", e, exc_info=True
            )
            await message.nack(requeue=True)
