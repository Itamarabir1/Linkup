"""
Builder ל-context של מייל סיכום שיחה.
"""
from typing import Any, Dict
from app.domain.notifications.core.builders.base import BaseContextBuilder


class ChatBuilder(BaseContextBuilder):
    """
    מטפל באירוע chat.conversation.completed.
    בונה context למייל סיכום שיחה עם פרטי הנסיעה והסיכום בעברית.
    """

    def build(self, payload: Dict[str, Any], event_key: str) -> Dict[str, Any]:
        """
        בונה context למייל סיכום שיחה.
        
        Args:
            payload: נתוני האירוע מ-RabbitMQ (מכיל conversation_id, user_id_1, user_id_2, driver_name, passenger_name, pickup_location, meeting_time, summary_hebrew)
            event_key: שם האירוע (chat.conversation.completed)
            
        Returns:
            Dict עם כל הנתונים למייל
        """
        context = {
            "conversation_id": payload.get("conversation_id"),
            "user_id_1": payload.get("user_id_1"),
            "user_id_2": payload.get("user_id_2"),
            "driver_name": payload.get("driver_name", "לא צוין"),
            "passenger_name": payload.get("passenger_name", "לא צוין"),
            "pickup_location": payload.get("pickup_location", "לא צוין"),
            "meeting_time": payload.get("meeting_time", "לא צוין"),
            "summary_hebrew": payload.get("summary_hebrew", "לא זמין"),
            "subject": "סיכום שיחה - LinkUp",
            "color": self._determine_color(event_key),
        }
        
        return context
