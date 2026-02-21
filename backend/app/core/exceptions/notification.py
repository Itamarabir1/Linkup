# app/core/exceptions/notifications.py
from .base import LinkupError

class NotificationError(LinkupError):
    """שגיאת בסיס לכל עולם ההתראות"""
    status_code = 500
    error_code = "NOTIFICATION_GENERAL_ERROR"
    message = "שגיאה בתהליך ההתראות"

    def __init__(self, message=None, status_code=None, error_code=None):
        super().__init__(
            message=message or self.message,
            status_code=status_code or self.status_code,
            error_code=error_code or self.error_code
        )

class RecipientResolverError(NotificationError):
    """שגיאה כשלא ניתן למצוא נמען (טלפון/מייל) להתראה"""
    status_code = 404
    error_code = "NOTIFICATION_RECIPIENT_NOT_FOUND"
    message = "לא נמצא נמען תקין לשליחת ההתראה"

    def __init__(self, detail: str = ""):
        full_message = f"{self.message}: {detail}" if detail else self.message
        super().__init__(
            message=full_message,
            status_code=self.status_code,
            error_code=self.error_code
        )

class ContextBuilderError(NotificationError):
    """שגיאה כשבניית הנתונים (Context) נכשלה"""
    status_code = 500
    error_code = "NOTIFICATION_CONTEXT_FAILED"
    message = "כשל בהכנת נתוני ההתראה"