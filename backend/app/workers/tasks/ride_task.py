import logging
from typing import Dict, Any
from app.db.session import SessionLocal
from app.domain.rides.services.maps_service import maps_service
from app.domain.rides.crud import crud_ride
# TODO: dispatch function does not exist — EventDispatcher.dispatch is a method, not a module-level function
from app.infrastructure.events.dispatcher.dispatcher import dispatch
from app.core.exceptions import InfrastructureError

logger = logging.getLogger(__name__)

async def handle_map_tasks(payload: Dict[str, Any], routing_key: str):
    """
    מנתב משימות מפות לפי ה-routing_key.
    דוגמה למפתח: ride.maps.calculate_route
    """
    if routing_key == "ride.maps.calculate_route":
        await calculate_ride_route_task(payload)

async def calculate_ride_route_task(data: Dict[str, Any]):
    """
    משימה כבדה: פנייה ל-Google Maps, עדכון DB והפצת אירוע סיום.
    """
    ride_id = data.get("ride_id")
    origin = data.get("origin")
    destination = data.get("destination")

    if not all([ride_id, origin, destination]):
        logger.error(f"❌ Missing data for route calculation: {data}")
        return

    logger.info(f"🗺️ Calculating route for Ride {ride_id}...")

    # שימוש ב-Context Manager של סניור לניהול ה-DB
    with SessionLocal() as db:
        try:
            # 1. פנייה ל-API חיצוני (משימה שלוקחת זמן)
            route_result = await maps_service.get_directions(origin, destination)
            
            # 2. עדכון הנתונים ב-Database
            crud_ride.update_route_details(
                db, 
                ride_id=ride_id, 
                route_data=route_result
            )

            logger.info(f"✅ Route updated for Ride {ride_id}")

            # 3. סניור לא שולח וובסוקט מכאן! הוא מפיץ אירוע שהמסלול מוכן.
            # ה-NotificationHandler כבר יחליט אם לשלוח פוש או וובסוקט.
            await dispatch("RIDE_ROUTE_READY", {
                "ride_id": ride_id,
                "user_id": data.get("user_id"),
                "distance": route_result.get("distance"),
                "duration": route_result.get("duration")
            })

        except InfrastructureError as e:
            # שגיאה מה-LinkupError שלך (למשל גוגל מפות למטה)
            logger.error(f"⚠️ Maps API failure for ride {ride_id}: {e.message}")
            raise  # גורם ל-RabbitMQ לנסות שוב (Retry) בעוד כמה דקות
            
        except Exception as e:
            logger.error(f"🔥 Unexpected error in ride task: {str(e)}", exc_info=True)
            # בשגיאת קוד לא עושים Retry אוטומטי כדי לא להיכנס ללופ