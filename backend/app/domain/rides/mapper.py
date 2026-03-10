import logging
from typing import Any, Dict
from datetime import datetime

# מודלים ו-Enums
from app.domain.rides.model import Ride
from app.domain.rides.enum import RideStatus
from app.core.exceptions.ride import InvalidRouteError

# לוגיקה ותשתיות
from app.domain.rides.logic import calculate_estimated_arrival
from app.infrastructure.geo.utils import to_geo_point, to_geo_line

logger = logging.getLogger(__name__)


class RideMapper:
    """
    Ride Domain Mapper.
    אחראי על טרנספורמציה וולידציה של נתוני נסיעה בין שכבות (Cache -> DB).
    משתמש ב-Static Methods מכיוון שהוא Stateless.
    """

    @staticmethod
    def map_cache_to_model(cached_data: Dict[str, Any], selected_index: int) -> Ride:
        """
        הפונקציה הראשית (Orchestrator).
        ממירה נתוני חיפוש זמניים מה-Cache לאובייקט Ride קבוע של SQLAlchemy.
        """
        # 1. ולידציה של שלמות הנתונים
        RideMapper._validate_input(cached_data, selected_index)

        try:
            # המסלול שהמשתמש בחר – ממנו לוקחים זמן נסיעה וק"מ לשמירה בטבלה
            route = cached_data["routes"][selected_index]
            departure_time = RideMapper._parse_time(cached_data["departure_time"])

            # זמן נסיעה וק"מ שייכים למסלול הנבחר בלבד (נשמרים בעמודות בטבלת rides)
            duration_min = route.get("duration_min")
            distance_km = route.get("distance_km")
            if duration_min is None:
                duration_min = 0
            if distance_km is None:
                distance_km = 0

            # 2. חישוב נתונים נגזרים (Derived Data)
            estimated_arrival = calculate_estimated_arrival(
                departure_time=departure_time,
                duration_min=int(duration_min) if duration_min is not None else 0,
            )

            # 3. בניית המודל (יצירת אובייקט Ride) – כולל זמן נסיעה וק"מ של המסלול הנבחר
            return Ride(
                driver_id=cached_data["driver_id"],
                departure_time=departure_time,
                estimated_arrival_time=estimated_arrival,
                # המרות גיאוגרפיות (PostGIS)
                origin_geom=to_geo_point(
                    cached_data["origin_lat"], cached_data["origin_lon"]
                ),
                destination_geom=to_geo_point(
                    cached_data["dest_lat"], cached_data["dest_lon"]
                ),
                route_coords=to_geo_line(route.get("coords", [])),
                route_summary=(route.get("summary") or "").strip() or None,
                # נתוני מסלול – מהמסלול שנבחר בלבד (נכנסים לטבלה)
                distance_km=float(distance_km),
                duration_min=float(duration_min),
                # סטטוס התחלתי
                status=RideStatus.OPEN,
                # נתונים נוספים
                price=cached_data.get("price"),
                available_seats=cached_data.get("available_seats"),
                origin_name=cached_data.get("origin_name"),
                destination_name=cached_data.get("destination_name"),
            )

        except Exception as e:
            logger.error(f"Mapping failed for ride: {str(e)}")
            raise InvalidRouteError(detail=f"Failed to map ride data: {str(e)}")

    @staticmethod
    def _validate_input(data: Dict[str, Any], idx: int) -> None:
        """בדיקת תקינות המבנה מה-Cache – כולל זמן נסיעה וק\"מ של המסלול הנבחר"""
        routes = data.get("routes", [])
        if not (0 <= idx < len(routes)):
            raise InvalidRouteError(index=idx)

        required_fields = [
            "origin_lat",
            "origin_lon",
            "dest_lat",
            "dest_lon",
            "departure_time",
            "driver_id",
        ]
        missing = [f for f in required_fields if f not in data]
        if missing:
            raise InvalidRouteError(detail=f"Missing required cache fields: {missing}")

        # וידוא שהמסלול הנבחר כולל זמן נסיעה וק\"מ (יישמרו בטבלת rides)
        selected_route = routes[idx]
        for field in ("duration_min", "distance_km"):
            if field not in selected_route:
                raise InvalidRouteError(
                    detail=f"Missing route field for selected route: {field}"
                )

    @staticmethod
    def _parse_time(departure_time: Any) -> datetime:
        """מבטיח חזרה של אובייקט datetime תקין"""
        if isinstance(departure_time, str):
            try:
                return datetime.fromisoformat(departure_time)
            except ValueError:
                # ניסיון פורמט נוסף אם צריך או זריקת שגיאה
                raise InvalidRouteError(detail="Invalid departure_time format")
        return departure_time
