import logging
from typing import Optional, Dict, List
from datetime import datetime, timedelta

from app.infrastructure.geo.client import geo_client
from app.domain.geo.schema import GeoLocation, RouteOptionData

logger = logging.getLogger(__name__)

class RoutingService:
    @staticmethod
    def get_full_routing_data(origin_name: str, dest_name: str) -> Optional[Dict]:
        """
        מתזמר שליפת נתונים מ-API חיצוני (Google/OSRM) והמרתם לסכימות פנימיות.
        """
        # 1. המרת כתובות לקואורדינטות דרך ה-Client
        lat_o, lon_o = geo_client.fetch_coordinates(origin_name)
        lat_d, lon_d = geo_client.fetch_coordinates(dest_name)
        
        if lat_o is None or lat_d is None:
            logger.warning(f"Could not find coordinates for: {origin_name} or {dest_name}")
            return None

        # 2. שליפת מסלולים גולמיים
        raw_routes = geo_client.fetch_raw_routes((lat_o, lon_o), (lat_d, lon_d))
        
        if not raw_routes:
            return None
        
        # 3. עיבוד הנתונים לתוך סכימות (Data Transformation)
        processed_routes = [
            RouteOptionData(
                summary=r.get("summary", "Main Route"),
                duration_min=round(r.get("duration", 0) / 60, 1),
                distance_km=round(r.get("distance", 0) / 1000, 1),
                # המרת קואורדינטות לפורמט [lat, lon] עבור ה-Frontend
                coords=[[c[1], c[0]] for c in r.get("geometry", {}).get("coordinates", [])]
            ) for r in raw_routes
        ]

        return {
            "origin": GeoLocation(lat=lat_o, lon=lon_o),
            "dest": GeoLocation(lat=lat_d, lon=lon_d),
            "routes": processed_routes
        }

    @staticmethod
    def calculate_eta(duration_seconds: float, buffer_percent: float = 0.15) -> str:
        """
        מחשבת שעת הגעה משוערת כולל בופר של זמן.
        """
        total_seconds = duration_seconds * (1 + buffer_percent)
        eta_datetime = datetime.now() + timedelta(seconds=total_seconds)
        return eta_datetime.strftime("%H:%M")