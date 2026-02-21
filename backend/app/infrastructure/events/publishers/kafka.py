import logging
from backend.app.infrastructure.outbox.model import Event, DispatchTarget
from backend.app.infrastructure.events.publishers.base import EventPublisher

logger = logging.getLogger(__name__)

class KafkaPublisher(EventPublisher):
    def __init__(self, kafka_producer):
        self._producer = kafka_producer
    
    async def publish(self, event: Event) -> bool:
        try:
            topic = event.metadata.get("topic", "linkup_events")
            # שליפת המפתח מהמטא-דאטה (למשל user_id)
            partition_key = event.metadata.get("partition_key") 
            
            await self._producer.send_event(
                topic=topic,
                key=partition_key, # <--- קריטי לסדר של קפקא
                value={
                    "event": event.name,
                    "payload": event.payload,
                }
            )
            return True
        except Exception as e:
            logger.warning(f"⚠️ Kafka failed: {e}")
            return False