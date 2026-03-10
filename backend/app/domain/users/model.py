from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base
from geoalchemy2 import Geography  # שימוש ב-Geography עבור PostGIS


class User(Base):
    """
    User Entity - Senior Edition.
    הישות המרכזית במערכת. משתמש יכול להיות נהג, נוסע או שניהם.
    """

    __tablename__ = "users"

    # מזהה ייחודי
    user_id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(100), nullable=False)
    phone_number = Column(String(20), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=True)
    hashed_password = Column(String(255), nullable=False)

    # אימות וניהול חשבון
    is_verified = Column(Boolean, default=False, nullable=False, server_default="false")
    is_active = Column(Boolean, default=True, server_default="true")
    is_admin = Column(Boolean, default=False, server_default="false")

    # פרופיל (נהוג לשמור קישור מלא ל-S3, למשל https://bucket.s3.region.amazonaws.com/avatars/...)
    avatar_url = Column(String(255), nullable=True)
    fcm_token = Column(Text, nullable=True)
    # Refresh Token (ארוך תוקף) – נשמר ב-DB כדי לאפשר ביטול (logout מכל המכשירים)
    refresh_token = Column(Text, nullable=True)

    # מיקום אחרון (PostGIS Geography) - לחישובי מרחק במטרים
    last_location = Column(Geography(geometry_type="POINT", srid=4326), nullable=True)

    # זמנים (Best Practice: שימוש ב-UTC)
    last_login = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # --- Relationships (The "Glue" of the System) ---

    # 1. נסיעות שהמשתמש יצר (כנהג)
    # מתחבר ל-Ride.driver
    rides_as_driver = relationship(
        "Ride",
        back_populates="driver",
        cascade="all, delete-orphan",
        passive_deletes=True,  # אופטימיזציה לביצועי מחיקה ב-DB
    )

    # 2. בקשות חיפוש (כנוסע מחפש / סוכן חכם)
    # מתחבר ל-PassengerRequest.user
    passenger_requests = relationship(
        "PassengerRequest",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    # 3. הזמנות מאושרות (כנוסע רשום בנסיעה)
    # מתחבר ל-Booking.passenger
    bookings = relationship(
        "Booking",
        back_populates="passenger",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self):
        return f"<User(user_id={self.user_id}, full_name='{self.full_name}', phone='{self.phone_number}')>"

    # --- Senior Helpers ---

    @property
    def is_driver(self) -> bool:
        """האם המשתמש העלה פעם נסיעה כנהג?"""
        return len(self.rides_as_driver) > 0

    @property
    def active_bookings_count(self) -> int:
        """כמה הזמנות פעילות יש למשתמש כרגע"""
        return sum(1 for b in self.bookings if b.status == "confirmed")

    def to_event_payload(self) -> dict:
        """
        מרכז את הלוגיקה של 'איזה נתונים יוצאים החוצה'.
        עכשיו השדות יזוהו כי הפונקציה מוזחת (Tab) פנימה לתוך ה-Class.
        """
        return {
            "user_id": self.user_id,
            "full_name": self.full_name,
            "email": self.email,
            "phone": self.phone_number,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "is_verified": self.is_verified,
        }

    # בתוך class User במודל שלך
