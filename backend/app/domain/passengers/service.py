import logging
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from geoalchemy2.shape import to_shape

from app.core.exceptions.booking import PassengerRequestNotFoundError
from app.core.exceptions.infrastructure import GeocodingError
from app.domain.passengers.crud import crud_passenger
from app.domain.bookings.service import BookingService
from app.domain.passengers.enum import PassengerStatus
from app.domain.passengers.schema import (
    PassengerRequestCreate,
    PassengerRequestResponse,
    RideSearchRequest,
    PassengerRequestUpdateNotifications,
)
from app.domain.rides.crud import crud_ride
from app.domain.rides.enum import RideStatus
from app.domain.rides.schema import DriverInfoResponse
from app.infrastructure.geo.utils import get_coords_from_address

# הגדרת לוגר
logger = logging.getLogger(__name__)


class PassengerService:
    @staticmethod
    def create_passenger_request(
        db: Session, request_in: PassengerRequestCreate, passenger_id: UUID
    ):
        """יוצר בקשה (מודעה) ומחפש נהגים תואמים מיד. passenger_id מהטוקן (API)."""
        try:
            if request_in.pickup_lat is not None and request_in.pickup_lon is not None:
                p_lat, p_lon = request_in.pickup_lat, request_in.pickup_lon
            else:
                p_lat, p_lon = get_coords_from_address(request_in.pickup_name)
            d_lat, d_lon = get_coords_from_address(request_in.destination_name)

            if p_lat is None or d_lat is None:
                raise GeocodingError(
                    address=request_in.pickup_name or request_in.destination_name
                )

            new_request = crud_passenger.create(
                db, request_in, p_lat, p_lon, d_lat, d_lon, passenger_id=passenger_id
            )

            # 3. מציאת נהגים רלוונטיים באופן מיידי
            matches = crud_passenger.find_rides_by_coordinates(
                db, p_lat, p_lon, d_lat, d_lon, request_in.search_radius
            )

            # הוספת התוצאות לאובייקט החוזר
            new_request.matching_rides = matches
            return new_request

        except Exception as e:
            logger.error(f"Error in create_passenger_request: {e}")
            raise e

    @staticmethod
    def toggle_request_notifications(
        db: Session, request_id: UUID, update_data: PassengerRequestUpdateNotifications
    ):
        """עדכון כפתור ההתראות (הסוכן החכם) לבקשה ספציפית"""
        p_req = crud_passenger.get_by_id(db, request_id)
        if not p_req:
            raise PassengerRequestNotFoundError(request_id=str(request_id))

        p_req.is_notification_active = update_data.is_notification_active
        db.commit()
        db.refresh(p_req)

        status_text = "מופעלות" if p_req.is_notification_active else "מבוטלות"
        logger.info(f"Notifications for request {request_id} are now {status_text}")
        return p_req

    @staticmethod
    def cancel_request(db: Session, request_id: UUID, passenger_id: UUID):
        """ביטול הבקשה ושחרור כל ההזמנות הקשורות אליה (רק לבעל הבקשה)."""
        p_req = crud_passenger.get_by_id(db, request_id)
        if not p_req:
            raise PassengerRequestNotFoundError(request_id=str(request_id))

        # הרשאות: רק בעל הבקשה יכול לבטל
        if p_req.passenger_id != passenger_id:
            from app.core.exceptions.booking import ForbiddenRideActionError

            raise ForbiddenRideActionError("גישה חסומה")

        # 1. ביטול כל ההזמנות ושחרור מושבים
        BookingService.cancel_all_bookings_for_request(db, request_id)

        # 2. עדכון סטטוס הבקשה עצמה
        p_req.status = PassengerStatus.CANCELLED

        db.commit()
        return {"message": "הבקשה בוטלה וכל השריונים מול הנהגים שוחררו."}

    @staticmethod
    async def get_my_requests(
        db: AsyncSession,
        passenger_id: UUID,
        status: Optional[str] = None,
    ) -> List[PassengerRequestResponse]:
        """רשימת הבקשות שלי כנוסע (הבקשות שלי)."""
        status_enum = PassengerStatus(status) if status else None
        requests = await crud_passenger.get_by_passenger_id(
            db, passenger_id, status_enum
        )
        return [PassengerRequestResponse.model_validate(r) for r in requests]

    @staticmethod
    def get_matches_by_request_id(db: Session, request_id: UUID):
        """שליפת התאמות חדשות לבקשה קיימת"""
        p_req = crud_passenger.get_by_id(db, request_id)
        if not p_req:
            raise PassengerRequestNotFoundError(request_id=str(request_id))

        try:
            origin_point = to_shape(p_req.pickup_geom)
            dest_point = to_shape(p_req.destination_geom)

            p_lat, p_lon = origin_point.y, origin_point.x
            d_lat, d_lon = dest_point.y, dest_point.x
        except Exception as e:
            logger.error(f"Error parsing coordinates for request {request_id}: {e}")
            raise GeocodingError(address=str(request_id))

        radius = getattr(p_req, "search_radius_meters", None) or getattr(
            p_req, "search_radius", 1000
        )
        return crud_passenger.find_rides_by_coordinates(
            db, p_lat, p_lon, d_lat, d_lon, radius
        )

    @staticmethod
    def search_rides_for_passenger(db: Session, search_data: RideSearchRequest):
        """חיפוש נסיעות פעיל לפי קואורדינטות של כתובות. אם המשתמש מחובר, יוצר/מעדכן בקשה ב-DB."""
        from app.domain.passengers.schema import (
            RideSearchResponse,
            PassengerRequestCreate,
        )
        from app.domain.rides.schema import RideResponse

        try:
            p_lat, p_lon = get_coords_from_address(search_data.pickup_name)
            d_lat, d_lon = get_coords_from_address(search_data.destination_name)

            if p_lat is None or d_lat is None:
                raise GeocodingError(
                    address=search_data.pickup_name or search_data.destination_name
                )

            radius = getattr(search_data, "search_radius", None) or getattr(
                search_data, "radius", 1000
            )

            # אם המשתמש מחובר, יצור/עדכן בקשה ב-DB
            request_id = None
            if search_data.passenger_id:
                request_in = PassengerRequestCreate(
                    pickup_name=search_data.pickup_name,
                    destination_name=search_data.destination_name,
                    num_passengers=1,  # ברירת מחדל, יכול להיות מותאם בעתיד
                    requested_departure_time=search_data.departure_time,
                    search_radius=radius,
                    is_notification_active=True,
                    is_auto_generated=True,  # בקשה שנוצרה מחיפוש
                )
                # יצירת בקשה חדשה (תמיד ליצור חדשה לפי העדפת המשתמש)
                passenger_request = crud_passenger.create(
                    db,
                    request_in,
                    p_lat,
                    p_lon,
                    d_lat,
                    d_lon,
                    passenger_id=search_data.passenger_id,
                )
                request_id = passenger_request.request_id

            matches = crud_passenger.find_rides_by_coordinates(
                db, p_lat, p_lon, d_lat, d_lon, radius
            )

            if search_data.departure_time:
                matches = [
                    r for r in matches if r.departure_time >= search_data.departure_time
                ]

            # החזר תמיד RideSearchResponse (עם request_id אם המשתמש מחובר)
            return RideSearchResponse(
                rides=[RideResponse.model_validate(r) for r in matches],
                request_id=request_id,
            )

        except Exception as e:
            logger.error(f"Error in search_rides_for_passenger: {e}")
            raise e

    @staticmethod
    def get_all_rides_for_admin(db: Session, status: str = None):
        """שליפת כל הנסיעות עם פילטר אופציונלי (בתוך ה-Class)"""
        return crud_passenger.get_multi_rides(db, status=status)

    @staticmethod
    def get_ride_driver_info(db: Session, ride_id: UUID) -> DriverInfoResponse:
        """פרטי נהג של נסיעה – רק לנסיעות פתוחות (OPEN/FULL). מחזיר 404 אם לא נמצא או לא רלוונטי."""
        ride = crud_ride.get_with_driver(db, ride_id)
        if not ride:
            raise ValueError("נסיעה לא נמצאה")
        if ride.status not in (RideStatus.OPEN, RideStatus.FULL):
            raise ValueError("הנסיעה אינה פתוחה להצטרפות")
        driver = ride.driver
        if not driver:
            raise ValueError("פרטי נהג לא זמינים")
        return DriverInfoResponse(
            full_name=driver.full_name or "נהג",
            phone_number=getattr(driver, "phone_number", None),
        )

    @staticmethod
    def create_passenger_request_for_ride_search(
        db: Session,
        passenger_id: UUID,
        pickup_name: str,
        destination_name: str,
        num_seats: int = 1,
    ):
        """יוצר PassengerRequest מינימלי מבקשת הצטרפות מחיפוש; מחזיר את הבקשה (עם request_id)."""
        p_lat, p_lon = get_coords_from_address(pickup_name)
        d_lat, d_lon = get_coords_from_address(destination_name)
        if p_lat is None or d_lat is None:
            raise GeocodingError(address=pickup_name or destination_name)
        request_in = PassengerRequestCreate(
            pickup_name=pickup_name,
            destination_name=destination_name,
            num_passengers=num_seats,
            search_radius=1000,
            is_notification_active=True,
            is_auto_generated=True,
        )
        return crud_passenger.create(
            db, request_in, p_lat, p_lon, d_lat, d_lon, passenger_id=passenger_id
        )
