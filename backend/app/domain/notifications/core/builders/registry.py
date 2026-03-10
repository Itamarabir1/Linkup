from .ride_builder import RideContextBuilder
from .booking_builder import BookingContextBuilder

CONTEXT_MAP = {
    # אירועי נסיעה - כולם משתמשים ב-RideContextBuilder כי הם מקבלים אובייקט Ride
    "ride_cancelled": RideContextBuilder(),
    "new_ride_request": RideContextBuilder(),
    "ride_started": RideContextBuilder(),
    # אירועי הזמנה - כולם משתמשים ב-BookingContextBuilder כי הם מקבלים אובייקט Booking
    "booking_confirmed": BookingContextBuilder(),
    "booking_rejected": BookingContextBuilder(),
    "booking_reminder": BookingContextBuilder(),
}
