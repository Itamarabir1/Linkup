import json
import logging
from typing import Dict, Any
from uuid import UUID

from app.infrastructure.redis.broadcast import broadcast
from app.domain.rides.enum import RideStatus, RideBroadcastAction

logger = logging.getLogger(__name__)

# ערוץ Redis לרשימת נסיעות – כל המנויים (כולל שרת WS) מקבלים עדכוני נסיעות חדשות/עודכנות
RIDES_LIST_CHANNEL = "rides:list"


class RideNotificationFactory:
    """
    Utility Class האחראי על פורמט ההודעות לכל ערוצי ההפצה (WebSocket, Push, וכו').
    מרכז את כל ה"צבעים" והטקסטים במקום אחד. צבע יצירה = ירוק (נסיעה חדשה).
    """

    # מפת קונפיגורציה: RideBroadcastAction (שידור) + RideStatus (ביטול/השלמה)
    _CONFIG = {
        RideBroadcastAction.CREATED.value: {
            "color": "green",
            "message": "נסיעה חדשה זמינה כעת!",
            "event_prefix": "RIDE_CREATED",
        },
        RideBroadcastAction.UPDATED.value: {
            "color": "orange",
            "message": "עדכון בנסיעה (למשל מקום תפוס)",
            "event_prefix": "RIDE_UPDATED",
        },
        RideStatus.CANCELLED.value: {
            "color": "red",
            "message": "הנסיעה בוטלה על ידי הנהג",
            "event_prefix": "RIDE_CANCELLED",
        },
        RideStatus.COMPLETED.value: {
            "color": "green",
            "message": "הנסיעה הסתיימה בהצלחה",
            "event_prefix": "RIDE_COMPLETED",
        },
    }

    @classmethod
    def create_broadcast_payload(cls, ride, action: str) -> Dict[str, Any]:
        """מייצר Payload אחיד לשידור WebSocket (event, ride_id, status, color, message)."""
        config = cls._CONFIG.get(
            action,
            {
                "color": "gray",
                "message": "עדכון בנסיעה",
                "event_prefix": "RIDE_UPDATED",
            },
        )
        return {
            "event": config["event_prefix"],
            "ride_id": str(ride.ride_id),
            "status": ride.status.value
            if hasattr(ride.status, "value")
            else str(ride.status),
            "color": config["color"],
            "message": f"{config['message']} (מ-{ride.origin_name} ל-{ride.destination_name})",
        }


async def publish_ride_update(ride_id: UUID, message_data: dict) -> None:
    """פרסום עדכונים לערוץ ה-Realtime של הנסיעה (WebSocket)."""
    channel_name = f"ride_{ride_id}"
    payload = (
        json.dumps(message_data) if isinstance(message_data, dict) else message_data
    )
    await broadcast.publish(channel_name, payload)
