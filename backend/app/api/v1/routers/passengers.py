from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
import logging
from datetime import datetime
from typing import List, Optional


from app.db.session import get_db
from app.domain.passengers.schema import (
    PassengerRequestCreate,
    PassengerRequestResponse,
    PassengerRequestWithMatches,
    PassengerRequestUpdateNotifications,
    RideSearchRequest,
    RequestRideFromSearch,
    RideSearchResponse,
)
from app.domain.rides.schema import RideResponse, DriverInfoResponse
from app.domain.bookings.schema import BookingResponse
from app.domain.passengers.service import PassengerService
from app.domain.users.model import User
from app.api.dependencies.auth import get_current_user, get_current_user_optional

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/passengers", tags=["Passengers"])

# Sub-router for passenger-facing ride endpoints: /passenger/rides/...
passenger_rides_router = APIRouter(prefix="/rides", tags=["Passenger"])


# 0. הבקשות שלי (כנוסע)
@router.get("/me", response_model=List[PassengerRequestResponse])
async def get_my_requests(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    status: Optional[str] = Query(
        None,
        description="סנן לפי סטטוס: pending, approved, cancelled, matched, expired, completed, rejected",
    ),
):
    """רשימת הבקשות שלי כנוסע."""
    return await PassengerService.get_my_requests(
        db, current_user.user_id, status=status
    )


# 1. רישום בקשה רשמית (הסוכן החכם)
@router.post(
    "/",
    response_model=PassengerRequestWithMatches,
    status_code=status.HTTP_201_CREATED,
    summary="רישום נוסע לטרמפ (יצירת בקשה קבועה)",
)
def create_new_request(
    request: PassengerRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return PassengerService.create_passenger_request(
            db=db, request_in=request, passenger_id=current_user.user_id
        )
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error in create_new_request: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="שגיאת שרת פנימית ביצירת הבקשה")


# 2. עדכון הגדרות התראה
@router.patch(
    "/{request_id}/notifications",
    response_model=PassengerRequestResponse,
    summary="עדכון סטטוס התראות לסוכן החכם",
)
def update_notification_status(
    request_id: int,
    update_data: PassengerRequestUpdateNotifications,
    db: Session = Depends(get_db),
):
    """
    מעדכן האם הנוסע מעוניין לקבל התראות אקטיביות עבור בקשה זו.
    """
    return PassengerService.toggle_request_notifications(db, request_id, update_data)


# --- Passenger rides sub-router: GET /passenger/rides/{ride_id}/driver-info ---
@passenger_rides_router.get(
    "/{ride_id}/driver-info",
    response_model=DriverInfoResponse,
    summary="פרטי נהג לנסיעה (רק כשלחיצה על 'הצג פרטי הנהג')",
)
async def get_ride_driver_info(
    ride_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """מחזיר שם וטלפון של הנהג – רק לנסיעות פתוחות. דורש התחברות."""
    try:
        return await db.run_sync(
            lambda sync_db: PassengerService.get_ride_driver_info(sync_db, ride_id)
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# --- בקשת הצטרפות מתוך חיפוש ---
@router.post(
    "/request-ride-from-search",
    response_model=BookingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="שלח בקשה להצטרפות לנסיעה מתוך תוצאות חיפוש",
)
async def request_ride_from_search(
    body: RequestRideFromSearch,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """משתמש ב-request_id מהחיפוש (אם קיים) או יוצר חדש. יוצר Booking, כותב אירוע ל-Outbox; ה-Worker שולח מייל לנהג."""
    import logging

    _log = logging.getLogger(__name__)
    print(
        f"[NOTIF] API: request_ride_from_search START ride_id={body.ride_id}, request_id={body.request_id}",
        flush=True,
    )
    _log.info(
        "[NOTIF] API: request_ride_from_search called ride_id=%s, request_id=%s",
        body.ride_id,
        body.request_id,
    )
    from app.domain.bookings.service import BookingService
    from app.core.exceptions.booking import (
        RideNotAvailableError,
        BookingAlreadyExistsError,
        PassengerRequestNotFoundError,
    )
    from app.core.exceptions.infrastructure import GeocodingError

    try:
        request_id = body.request_id
        # אם אין request_id, יצור אחד (edge case - לא אמור לקרות אם החיפוש עובד נכון)
        if not request_id:
            new_request = await db.run_sync(
                lambda sync_db: PassengerService.create_passenger_request_for_ride_search(
                    sync_db,
                    passenger_id=current_user.user_id,
                    pickup_name=body.pickup_name,
                    destination_name=body.destination_name,
                    num_seats=body.num_seats,
                )
            )
            request_id = new_request.request_id

        return await BookingService.request_to_join(
            db,
            ride_id=body.ride_id,
            request_id=request_id,
            num_seats=body.num_seats,
            current_user_id=current_user.user_id,
        )
    except GeocodingError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RideNotAvailableError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except BookingAlreadyExistsError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except PassengerRequestNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


# 3. חיפוש חופשי (אם המשתמש מחובר, נשמרת בקשה ב-DB)
@router.get(
    "/search-rides",
    response_model=RideSearchResponse,
    summary="חיפוש טרמפים (אם מחובר, נשמרת בקשה ב-DB)",
)
async def search_available_rides(
    pickup_name: str,
    destination_name: str,
    search_radius: int = Query(
        1000, ge=100, description="רדיוס חיפוש במטרים (אחיד עם יצירת בקשה)"
    ),
    departure_time: Optional[datetime] = Query(
        None, description="אם ריק – יחפש מעכשיו"
    ),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    try:
        search_data = RideSearchRequest(
            passenger_id=current_user.user_id if current_user else None,
            pickup_name=pickup_name,
            destination_name=destination_name,
            search_radius=search_radius,
            departure_time=departure_time,
        )
        # המרת AsyncSession ל-Session sync באמצעות run_sync
        result = await db.run_sync(
            lambda sync_db: PassengerService.search_rides_for_passenger(
                sync_db, search_data
            )
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in search_available_rides: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"שגיאה בחיפוש נסיעות: {str(e)}")


# 4. ביטול בקשה
@router.delete("/{request_id}/cancel", summary="ביטול בקשת נסיעה ושחרור שריונים")
async def cancel_request(
    request_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """מבטל את הבקשה ומשחרר אוטומטית את כל המושבים שנתפסו מול נהגים (רק לבעל הבקשה)."""
    from app.core.exceptions.booking import (
        PassengerRequestNotFoundError,
        ForbiddenRideActionError,
    )

    try:
        return await db.run_sync(
            lambda sess: PassengerService.cancel_request(
                sess, request_id, current_user.user_id
            )
        )
    except PassengerRequestNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ForbiddenRideActionError as e:
        raise HTTPException(status_code=403, detail=str(e))


# 5. מציאת התאמות לבקשה קיימת
@router.get(
    "/{request_id}/matches",
    response_model=List[RideResponse],
    summary="שליפת התאמות עדכניות לבקשה קיימת",
)
def get_latest_matches(request_id: int, db: Session = Depends(get_db)):
    return PassengerService.get_matches_by_request_id(db, request_id)


@router.get(
    "/all", response_model=List[RideResponse], summary="תצוגת כל הנסיעות (ניהול ובקרה)"
)
def get_all_rides_admin(
    status: str = Query(None, description="סנן לפי סטטוס: open, cancelled, completed"),
    db: Session = Depends(get_db),
):
    """
    מחזיר את כל הנסיעות במערכת.
    אם נשלח סטטוס, יחזיר רק נסיעות בסטטוס הזה.
    """
    return PassengerService.get_all_rides_for_admin(db, status=status)
