# app/api/v1/endpoints/bookings.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.db.session import get_db
from app.api.dependencies.auth import get_current_user
from app.domain.users.model import User
from app.domain.bookings.service import BookingService
from app.domain.bookings.schema import BookingResponse, BookingCreate, BookingManifestItem, RideManifestResponse

router = APIRouter(tags=["Bookings"])


@router.post("/request-to-join", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
async def request_to_join(
    booking_in: BookingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """בקשת הצטרפות לנסיעה. request_id חייב להיות של המשתמש המחובר."""
    try:
        return await BookingService.request_to_join(
            db,
            ride_id=booking_in.ride_id,
            request_id=booking_in.request_id,
            num_seats=booking_in.num_seats,
            current_user_id=current_user.user_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{booking_id}/approve", response_model=BookingResponse)
async def approve_booking(booking_id: int, driver_id: int, db: AsyncSession = Depends(get_db)):
    return await BookingService.approve_booking(db, booking_id, driver_id)


@router.patch("/{booking_id}/reject", response_model=BookingResponse)
async def reject_booking(booking_id: int, driver_id: int, db: AsyncSession = Depends(get_db)):
    try:
        return await BookingService.reject_booking(db, booking_id=booking_id, driver_id=driver_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{booking_id}/cancel", response_model=BookingResponse)
async def cancel_booking(
    booking_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await BookingService.cancel_booking(db, booking_id, current_user.user_id)


@router.get("/my-bookings", response_model=List[BookingResponse])
async def get_user_bookings(
    user_id: int,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    return await BookingService.get_user_bookings(db, user_id=user_id, status=status)


@router.get("/ride/{ride_id}/manifest", response_model=RideManifestResponse)
async def get_ride_manifest(ride_id: int, driver_id: int, db: AsyncSession = Depends(get_db)):
    return await BookingService.get_ride_manifest(db, ride_id, driver_id)


@router.get("/ride/{ride_id}/pending", response_model=List[BookingResponse])
async def get_pending_requests(ride_id: int, driver_id: int, db: AsyncSession = Depends(get_db)):
    return await BookingService.get_pending_requests(db, ride_id, driver_id)


@router.get("/{booking_id}", response_model=BookingResponse)
async def get_booking(booking_id: int, db: AsyncSession = Depends(get_db)):
    return await BookingService.get_booking(db, booking_id)



# @router.post("/report_locations", status_code=status.HTTP_204_NO_CONTENT)
# async def report_location_update(
#     # location_in: LocationUpdate,
#     # בהמשך יגיע מה-Token
#     user_id: int = 123 
# ):
#     """
#     הנהג מדווח על המיקום הנוכחי שלו בתוך נסיעה (booking).
#     השרת דואג להפיץ את הדיווח הזה לנוסע שממתין.
#     """
#     await location_service.broadcast_location(
#         location_in=location_in, 
#         ride_id=user_id
#     )
#     return

# @router.get("/me/history", response_model=List[RideResponse])
# async def get_my_ride_history(
#     limit: int = 20,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     return await UserService.get_user_activity_history(db, user_id=current_user.user_id, limit=limit)

