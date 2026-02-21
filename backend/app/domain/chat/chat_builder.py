"""
Builder ל-context של מייל סיכום שיחה.
"""
from typing import Dict, Any
from app.domain.chat.schema_ai import RideSummary


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
