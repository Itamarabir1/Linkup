import json
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any

from app.api.websockets.notifications import broadcast
from app.domain.geo.schema import LocationUpdate

logger = logging.getLogger(__name__)


async def broadcast_location_to_participants(
    location_in: LocationUpdate, ride_id: int, involved_bookings: List[int]
) -> Dict[str, Any]:
    """
    מפיץ את המיקום בזמן אמת לכל הנוסעים הרשומים לנסיעה דרך ה-WebSockets.

    אחריות:
    1. יצירת הודעת JSON סטנדרטית.
    2. שימוש ב-Timestamp מבוסס UTC (Timezone-aware).
    3. הפצה לכל ערוצי הבוקינג הרלוונטיים ב-Redis.
    """

    # הכנת גוף ההודעה - שימוש ב-datetime.now(timezone.utc) במקום utcnow() המיושן
    payload = {
        "type": "location_update",
        "ride_id": ride_id,
        "lat": location_in.latitude,
        "lng": location_in.longitude,
        "heading": location_in.heading or 0.0,
        "speed": location_in.speed,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    message_json = json.dumps(payload)

    try:
        # לולאה על כל הבוקינגים הפעילים בנסיעה הזו
        for booking_id in involved_bookings:
            channel_name = f"booking_{booking_id}"

            # פרסום ל-Redis Pub/Sub דרך ה-Broadcast manager
            await broadcast.publish(channel=channel_name, message=message_json)

        return payload

    except Exception as e:
        logger.error(f"❌ Failed to broadcast location for ride {ride_id}: {e}")
        # ב-Real-time עדיף להיכשל שקט ולא להפיל את כל ה-Request
        return payload
