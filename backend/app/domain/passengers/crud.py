"""
CRUD לבקשות נוסעים – מקור אמת יחיד, API עקבי.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from geoalchemy2 import Geography, Geometry
from geoalchemy2.shape import from_shape
from shapely.geometry import LineString

from app.domain.passengers.model import PassengerRequest
from app.domain.passengers.enum import PassengerStatus
from app.domain.passengers.schema import PassengerRequestCreate
from app.domain.rides.model import Ride
from app.domain.rides.enum import RideStatus

logger = logging.getLogger(__name__)


class CRUDPassenger:
    """
    ניהול גישה לבקשות נוסעים (PassengerRequest).
    כל הפעולות תחת מחלקה אחת – אין פונקציות מפוזרות.
    """

    # --- שליפה ---

    def get_by_id(self, db: Session, request_id: int) -> Optional[PassengerRequest]:
        """שליפת בקשה לפי request_id (Session סינכרוני)."""
        return db.get(PassengerRequest, request_id)

    async def get(self, db: AsyncSession, *, id: int) -> Optional[PassengerRequest]:
        """שליפת בקשה לפי request_id (AsyncSession – לשימוש ב־handler). חתימה: get(db, id=...)."""
        return await db.get(PassengerRequest, id)

    async def get_by_passenger_id(
        self,
        db: AsyncSession,
        passenger_id: int,
        status: Optional[PassengerStatus] = None,
    ) -> List[PassengerRequest]:
        """שליפת בקשות לפי נוסע (למסך 'הבקשות שלי')."""
        stmt = select(PassengerRequest).where(
            PassengerRequest.passenger_id == passenger_id
        )
        if status is not None:
            stmt = stmt.where(PassengerRequest.status == status)
        stmt = stmt.order_by(PassengerRequest.requested_departure_time.desc())
        result = await db.execute(stmt)
        return list(result.scalars().all())

    # --- יצירה ---

    def create(
        self,
        db: Session,
        request: PassengerRequestCreate,
        p_lat: float,
        p_lon: float,
        d_lat: float,
        d_lon: float,
        passenger_id: int,
    ) -> PassengerRequest:
        """יצירת בקשה חדשה. passenger_id מהשרת (טוקן), לא מהגוף."""
        from datetime import timezone

        req_time = request.requested_departure_time
        if req_time is None:
            req_time = datetime.now(timezone.utc)
        # DB column is TIMESTAMP WITHOUT TIME ZONE – pass naive UTC to avoid asyncpg error
        if getattr(req_time, "tzinfo", None) is not None:
            req_time = req_time.astimezone(timezone.utc).replace(tzinfo=None)
        db_request = PassengerRequest(
            passenger_id=passenger_id,
            num_passengers=request.num_passengers,
            pickup_name=request.pickup_name,
            destination_name=request.destination_name,
            requested_departure_time=req_time,
            search_radius_meters=request.search_radius,
            is_auto_generated=request.is_auto_generated,
            is_notification_active=request.is_notification_active,
            pickup_geom=func.ST_SetSRID(func.ST_MakePoint(p_lon, p_lat), 4326),
            destination_geom=func.ST_SetSRID(func.ST_MakePoint(d_lon, d_lat), 4326),
            status=PassengerStatus.ACTIVE,
        )
        db.add(db_request)
        db.commit()
        db.refresh(db_request)
        return db_request

    # --- חיפוש נסיעות עבור נוסע ---

    def find_rides_by_coordinates(
        self,
        db: Session,
        p_lat: float,
        p_lon: float,
        d_lat: float,
        d_lon: float,
        radius: int,
    ) -> List[Ride]:
        """מנוע חיפוש נסיעות לפי קואורדינטות ורדיוס, עם כיווניות על המסלול."""
        pickup_geo = func.ST_SetSRID(func.ST_MakePoint(p_lon, p_lat), 4326)
        dest_geo = func.ST_SetSRID(func.ST_MakePoint(d_lon, d_lat), 4326)
        return (
            db.query(Ride)
            .filter(
                and_(
                    Ride.status == RideStatus.OPEN,
                    Ride.available_seats > 0,
                    func.ST_DWithin(
                        cast(Ride.route_coords, Geography),
                        cast(pickup_geo, Geography),
                        radius,
                    ),
                    func.ST_DWithin(
                        cast(Ride.route_coords, Geography),
                        cast(dest_geo, Geography),
                        radius,
                    ),
                    func.ST_LineLocatePoint(
                        cast(Ride.route_coords, Geometry), cast(pickup_geo, Geometry)
                    )
                    < func.ST_LineLocatePoint(
                        cast(Ride.route_coords, Geometry), cast(dest_geo, Geometry)
                    ),
                )
            )
            .all()
        )

    # --- חיפוש נוסעים עבור נהג ---

    def find_passengers_on_route(
        self,
        db: Session,
        route_coords: list,
        radius_meters: int = 2000,
    ) -> List[PassengerRequest]:
        """נהג מחפש נוסעים לאורך המסלול שלו."""
        if not route_coords or len(route_coords) < 2:
            return []
        now = datetime.now()
        try:
            line = LineString([(p[1], p[0]) for p in route_coords])
            route_geom = from_shape(line, srid=4326)
            return (
                db.query(PassengerRequest)
                .filter(
                    and_(
                        PassengerRequest.status == PassengerStatus.ACTIVE,
                        PassengerRequest.requested_departure_time > now,
                        func.ST_DWithin(
                            cast(PassengerRequest.pickup_geom, Geography),
                            cast(route_geom, Geography),
                            radius_meters,
                        ),
                    )
                )
                .all()
            )
        except Exception as e:
            logger.error("Error searching passengers on route: %s", e)
            return []

    def find_passengers_by_start_end(
        self,
        db: Session,
        origin_lat: float,
        origin_lon: float,
        dest_lat: float,
        dest_lon: float,
        radius: int,
    ) -> List[PassengerRequest]:
        """חיפוש נוסעים לפי מוצא ויעד של נהג."""
        now = datetime.now()
        driver_origin = func.ST_SetSRID(func.ST_MakePoint(origin_lon, origin_lat), 4326)
        driver_dest = func.ST_SetSRID(func.ST_MakePoint(dest_lon, dest_lat), 4326)
        return (
            db.query(PassengerRequest)
            .filter(
                and_(
                    PassengerRequest.status == PassengerStatus.ACTIVE,
                    PassengerRequest.requested_departure_time > now,
                    func.ST_DWithin(
                        cast(PassengerRequest.pickup_geom, Geography),
                        cast(driver_origin, Geography),
                        radius,
                    ),
                    func.ST_DWithin(
                        cast(PassengerRequest.destination_geom, Geography),
                        cast(driver_dest, Geography),
                        radius,
                    ),
                )
            )
            .all()
        )

    def find_passengers_for_ride_notification(
        self,
        db: Session,
        ride: "Ride",
        radius_destination_m: int = 5000,
        radius_pickup_m: int = 2000,
        limit: int = 200,
    ) -> List[PassengerRequest]:
        """
        נוסעים רלוונטיים להתראה על נסיעה חדשה.
        סדר פילטרים: סטטוס+זמן (אינדקס) → לא הנהג → אופט-אין → יעד 5km → מוצא על המסלול.
        """
        now = datetime.now()
        ride_date = (
            ride.departure_time.date()
            if getattr(ride, "departure_time", None)
            else None
        )
        if not ride_date:
            logger.warning(
                "find_passengers_for_ride_notification: no ride_date for ride_id=%s",
                getattr(ride, "ride_id", None),
            )
            return []

        # שימוש ב-route_coords ישירות מהמסד (לא המרה לרשימה וחזרה) – כמו ב-find_rides_by_coordinates
        route_geom = getattr(ride, "route_coords", None)
        if not route_geom:
            logger.warning(
                "find_passengers_for_ride_notification: no route_coords for ride_id=%s",
                getattr(ride, "ride_id", None),
            )
            return []

        driver_id = getattr(ride, "driver_id", None)
        dest_geom = getattr(ride, "destination_geom", None)
        if not dest_geom:
            logger.warning(
                "find_passengers_for_ride_notification: no destination_geom for ride_id=%s",
                getattr(ride, "ride_id", None),
            )
            return []

        # חישוב טווח תאריכים גמיש (עד 7 ימים קדימה, עד יום אחד אחורה)
        min_date = ride_date - timedelta(days=1)
        max_date = ride_date + timedelta(days=7)

        # ספירת נוסעים לפני סינון גיאוגרפי (לדיבוג)
        total_active = (
            db.query(PassengerRequest)
            .filter(
                PassengerRequest.status == PassengerStatus.ACTIVE,
                PassengerRequest.requested_departure_time > now,
                func.date(PassengerRequest.requested_departure_time) <= max_date,
                func.date(PassengerRequest.requested_departure_time) >= min_date,
                PassengerRequest.passenger_id != driver_id,
                PassengerRequest.is_notification_active == True,
            )
            .count()
        )
        logger.info(
            "find_passengers_for_ride_notification: ride_id=%s, ride_date=%s, date_range=[%s, %s], total_active_passengers=%d (before geo filter)",
            getattr(ride, "ride_id", None),
            ride_date,
            min_date,
            max_date,
            total_active,
        )

        # מוצא הנוסע חייב להיות במרחק עד 2 ק"מ מהמסלול של הנסיעה (route)
        q = (
            db.query(PassengerRequest)
            .filter(
                PassengerRequest.status == PassengerStatus.ACTIVE,
                PassengerRequest.requested_departure_time > now,
                func.date(PassengerRequest.requested_departure_time) <= max_date,
                func.date(PassengerRequest.requested_departure_time) >= min_date,
                PassengerRequest.passenger_id != driver_id,
                PassengerRequest.is_notification_active == True,
                # יעד בטווח של 5 ק"מ מהיעד של הנסיעה
                func.ST_DWithin(
                    cast(PassengerRequest.destination_geom, Geography),
                    cast(dest_geom, Geography),
                    radius_destination_m,
                ),
                # מוצא הנוסע: במרחק עד 2 ק"מ מהמסלול של הנסיעה בלבד
                func.ST_DWithin(
                    cast(PassengerRequest.pickup_geom, Geography),
                    cast(route_geom, Geography),
                    radius_pickup_m,
                ),
            )
            .limit(limit)
        )
        results = q.all()
        logger.info(
            "find_passengers_for_ride_notification: ride_id=%s, found %d matching passengers after all filters",
            getattr(ride, "ride_id", None),
            len(results),
        )
        if results:
            logger.info(
                "find_passengers_for_ride_notification: matching passenger_ids=%s",
                [r.passenger_id for r in results],
            )
        return results

    # --- נסיעות (שליפה לצורך UI/רשימות) ---

    def get_multi_rides(
        self,
        db: Session,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Ride]:
        """שליפת רשימת נסיעות עם סינון אופציונלי לפי סטטוס."""
        query = db.query(Ride)
        if status:
            query = query.filter(Ride.status == status)
        return query.offset(skip).limit(limit).all()

    # --- תחזוקה ---

    def close_expired_requests(self, db: Session, now: datetime) -> int:
        """סגירת בקשות שזמן היציאה עבר ולא שובצו. מחזיר מספר רשומות שעודכנו."""
        result = (
            db.query(PassengerRequest)
            .filter(
                PassengerRequest.status == PassengerStatus.ACTIVE,
                PassengerRequest.requested_departure_time < now,
            )
            .update(
                {PassengerRequest.status: PassengerStatus.EXPIRED.value},
                synchronize_session=False,
            )
        )
        return result


# Singleton לשימוש באפליקציה
crud_passenger = CRUDPassenger()
