import json
import logging
from typing import Any, Dict
from app.domain.notifications.providers.base import BaseNotificationProvider
from app.infrastructure.redis.broadcast import broadcast

logger = logging.getLogger(__name__)


class WebSocketProvider(BaseNotificationProvider):
    """
    WebSocket Provider (Real-time UI Updates).
    מתרגם אירועי דומיין לפקודות ויזואליות עבור הפרונטנד.
    """

    def can_send(self, user: Any) -> bool:
        """
        וובסוקט תמיד אפשר "לנסות" לשלוח.
        הבדיקה אם המשתמש באמת מחובר קורית בתוך ה-Broadcast/Socket Manager.
        """
        return bool(user and hasattr(user, "id"))

    async def send(
        self, user: Any, config: Dict[str, Any], context: Dict[str, Any]
    ) -> None:
        user_id = getattr(user, "id", None)
        if not user_id:
            logger.error("❌ [WS Provider] User object has no ID")
            return

        # 1. בניית ה-Payload מהקונפיג והקונטקסט
        # אנחנו נותנים עדיפות לערכים דינמיים מהקונטקסט, ואז לערכים קבועים מהקונפיג
        payload = {
            "type": "UI_UPDATE",
            "event": context.get("event_key"),
            "ride_id": str(
                context.get("ride_id", "")
            ),  # המרה ל-string למניעת בעיות JSON
            "data": {
                "color": context.get("color") or config.get("color", "green"),
                "status": context.get("status") or config.get("status", "updated"),
                "message": context.get("message")
                or config.get("message", "עדכון נסיעה"),
                "timestamp": context.get("timestamp"),
            },
        }

        channel = f"user_{user_id}"

        try:
            # 2. שליחה ל-Redis
            # סניור משתמש ב-default=str כדי שכל אובייקט (כמו UUID) יומר למחרוזת בבטחה
            message_json = json.dumps(payload, ensure_ascii=False, default=str)

            await broadcast.publish(channel=channel, message=message_json)
            logger.debug(f"📡 [WS Provider] Published to {channel}")

        except Exception as e:
            logger.error(f"❌ [WS Provider] Redis Publish Failed: {str(e)}")
            # לא זורקים שגיאה כדי שכישלון ב-WS לא יפיל שליחת מייל או פוש
