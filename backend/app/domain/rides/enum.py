import enum


class RideStatus(str, enum.Enum):
    """
    מצב נסיעה (4 מצבים). קונבנציה: שם באותיות גדולות, ערך באותיות קטנות (PostgreSQL).
    """
    OPEN = "open"
    FULL = "full"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class RideBroadcastAction(str, enum.Enum):
    """
    אירוע שידור WebSocket (לא מצב ב-DB). נסיעה חדשה / עדכון ברשימה.
    """
    CREATED = "CREATED"
    UPDATED = "UPDATED"
