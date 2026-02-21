from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from datetime import datetime

from backend.app.domain.bookings.model import Booking
from backend.app.models.rides.ride import Ride
from backend.app.domain.passengers.model import PassengerRequest
from app.models.enums import BookingStatus, RequestStatus, RideStatus

class CRUDBooking:
    """
    אחריות: ניהול הגישה למסד הנתונים עבור ישות ההזמנות (Booking).
    מרכז את כל פונקציות השליפה והכתיבה שסופקו.
    """

    # --- שליפות (Queries) ---

    def get_booking_by_id(self, db: Session, booking_id: int) -> Optional[Booking]:
        """עדכון שליפת בוקינג בודד (למשל לאישור הזמנה)"""
        return db.query(Booking).options(
            joinedload(Booking.ride).joinedload(Ride.driver), # מביא נסיעה ונהג
            joinedload(Booking.passenger_request).joinedload(PassengerRequest.user) # מביא בקשה ונוסע
        ).filter(Booking.booking_id == booking_id).first()

    def get_bookings_by_ride(self, db: Session, ride_id: int) -> List[Booking]:
        """עדכון שליפת כל הבוקינגס של נסיעה (למשל לביטול נסיעה ע"י נהג)"""
        return db.query(Booking).options(
            joinedload(Booking.ride).joinedload(Ride.driver),
            joinedload(Booking.passenger_request).joinedload(PassengerRequest.user)
        ).filter(
            Booking.ride_id == ride_id,
            Booking.status == BookingStatus.CONFIRMED
        ).all()

    def get_ride_for_update(self, db: Session, ride_id: int) -> Optional[Ride]:
        return db.query(Ride).filter(Ride.ride_id == ride_id).with_for_update().first()

    def get_existing_booking(self, db: Session, ride_id: int, request_id: int) -> Optional[Booking]:
        return db.query(Booking).filter(
            Booking.ride_id == ride_id,
            Booking.request_id == request_id,
            Booking.status != BookingStatus.CANCELLED
        ).first()

    # --- פעולות כתיבה (Operations) ---

    def create_booking_entry(self, db: Session, ride_id: int, request_id: int, passenger_id: int, num_seats: int) -> Booking:
        db_booking = Booking(
            ride_id=ride_id,
            request_id=request_id,
            passenger_id=passenger_id,
            num_seats=num_seats,
            status=BookingStatus.PENDING
        )
        db.add(db_booking)
        
        p_req = db.get(PassengerRequest, request_id)
        if p_req:
            p_req.status = RequestStatus.APPROVED
        
        db.flush()
        return db_booking

    def execute_booking_approval(self, db: Session, booking: Booking):
        ride = booking.ride
        booking.status = BookingStatus.CONFIRMED
        
        ride.available_seats -= booking.num_seats
        if ride.available_seats <= 0:
            ride.status = RideStatus.FULL
        
        if booking.request_id:
            p_req = db.get(PassengerRequest, booking.request_id)
            if p_req:
                p_req.status = RequestStatus.COMPLETED

    def execute_booking_rejection(self, db: Session, booking: Booking):
        booking.status = BookingStatus.REJECTED
        if booking.request_id:
            p_req = db.get(PassengerRequest, booking.request_id)
            if p_req:
                p_req.status = RequestStatus.PENDING

    def execute_booking_cancellation(self, db: Session, booking: Booking):
        if booking.status == BookingStatus.CONFIRMED:
            ride = booking.ride
            ride.available_seats += booking.num_seats
            ride.status = RideStatus.OPEN
            
        booking.status = BookingStatus.CANCELLED
        if booking.request_id:
            p_req = db.get(PassengerRequest, booking.request_id)
            if p_req:
                p_req.status = RequestStatus.PENDING

    def cancel_all_bookings_for_ride(self, db: Session, ride_id: int):
        """
        ביטול רוחבי ומקצועי:
        1. מבטל את כל ההזמנות (Bookings) של הנסיעה.
        2. מחזיר את כל בקשות הנוסעים (PassengerRequests) לסטטוס PENDING.
        """
        target_request_ids = db.query(Booking.request_id).filter(
            Booking.ride_id == ride_id,
            Booking.request_id.isnot(None)
        ).all()
        
        request_ids = [r[0] for r in target_request_ids]

        if request_ids:
            db.query(PassengerRequest).filter(
                PassengerRequest.request_id.in_(request_ids)
            ).update(
                {PassengerRequest.status: RequestStatus.PENDING},
                synchronize_session='fetch'
            )

        db.query(Booking).filter(Booking.ride_id == ride_id).update(
            {Booking.status: BookingStatus.CANCELLED},
            synchronize_session='fetch'
        )

        db.query(Ride).filter(Ride.ride_id == ride_id).update(
            {Ride.status: RideStatus.CANCELLED},
            synchronize_session='fetch'
        )

        db.flush()

    # --- פונקציות נוספות שנדרשות על ידי ה-BookingService ---

    def get_user_bookings_filtered(self, db: Session, user_id: int, status_filter: Optional[str] = None) -> List[Booking]:
        """שליפת כל ההזמנות שמשתמש ביצע (כנוסע)"""
        query = db.query(Booking).filter(Booking.passenger_id == user_id)
        if status_filter:
            query = query.filter(Booking.status == status_filter)
        return query.order_by(Booking.created_at.desc()).all()

    def get_ride_bookings_by_status(self, db: Session, ride_id: int, booking_status: str) -> List[Booking]:
        """שליפת הזמנות עבור נסיעה ספציפית לפי סטטוס"""
        return db.query(Booking).filter(
            Booking.ride_id == ride_id,
            Booking.status == booking_status
        ).all()

    def get_request_ids_for_ride(self, db: Session, ride_id: int) -> list[int]:
        results = db.query(Booking.request_id).filter(Booking.ride_id == ride_id, Booking.request_id.isnot(None)).all()
        return [r[0] for r in results]

    def bulk_update_bookings_status(self, db: Session, ride_id: int, new_status: BookingStatus):
        db.query(Booking).filter(Booking.ride_id == ride_id).update({Booking.status: new_status}, synchronize_session='fetch')

    def bulk_update_requests_status(self, db: Session, request_ids: list[int], new_status: RequestStatus):
        db.query(PassengerRequest).filter(PassengerRequest.request_id.in_(request_ids)).update({PassengerRequest.status: new_status}, synchronize_session='fetch')

    def complete_bookings_by_ride_ids(self, db: Session, ride_ids: list[int]):
        """מעדכן סטטוס לכל הבוקינגס ששייכים לרשימת נסיעות"""
        return db.query(Booking).filter(
            Booking.ride_id.in_(ride_ids),
            Booking.status == BookingStatus.CONFIRMED
        ).update({"status": BookingStatus.COMPLETED}, synchronize_session=False)

# יצירת מופע יחיד (Singleton) לשימוש ב-Service
crud_booking = CRUDBooking()