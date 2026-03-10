"""
Builder ל-context של מייל סיכום שיחה.
"""
from typing import Any, Dict
from app.domain.notifications.core.builders.base import BaseContextBuilder


def build_email_context(
    conversation_id: int,
    user_id_1: int,
    user_id_2: int,
    driver_name: str,
    passenger_name: str,
    pickup_location: str,
    meeting_time: str,
    summary_hebrew: str,
) -> Dict[str, Any]:
    """
    בונה context למייל סיכום שיחה.

    Args:
        conversation_id: מזהה השיחה
        user_id_1: מזהה משתמש ראשון
        user_id_2: מזהה משתמש שני
        driver_name: שם הנהג
        passenger_name: שם הנוסע
        pickup_location: מיקום איסוף
        meeting_time: זמן פגישה
        summary_hebrew: סיכום בעברית

    Returns:
        Dict עם כל הנתונים למייל
    """
    return {
        "conversation_id": conversation_id,
        "user_id_1": user_id_1,
        "user_id_2": user_id_2,
        "driver_name": driver_name,
        "passenger_name": passenger_name,
        "pickup_location": pickup_location,
        "meeting_time": meeting_time,
        "summary_hebrew": summary_hebrew,
    }


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
