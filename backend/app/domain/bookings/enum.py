import enum


class BookingStatus(str, enum.Enum):
    PENDING = "pending_approval"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    # סטטוסים לנסיעה פעילה (נהג עם נוסע)
    EN_ROUTE = "en_route"  # בדרך לנוסע
    ARRIVED = "arrived"  # הגיע לאיסוף
    TRIP_IN_PROGRESS = "trip_in_progress"  # הנוסע בפנים
