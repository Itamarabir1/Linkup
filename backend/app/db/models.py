# app/infrastructure/database/models.py
from app.db.base import Base
from app.domain.users.model import User
from app.domain.rides.model import Ride
from app.domain.bookings.model import Booking
from app.domain.passengers.model  import PassengerRequest

# הקובץ הזה לא מכיל לוגיקה, רק מבטיח שכל המודלים "רשומים" ב-Base