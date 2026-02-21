from .base import LinkupError
from typing import Optional
from fastapi import HTTPException, status


class InvalidEmailError(LinkupError):
    status_code = 400
    error_code = "VAL_INVALID_EMAIL"
    message = "כתובת האימייל שהוזנה אינה תקינה"
    def __init__(self, email: Optional[str] = None):
        super().__init__(message=self.message, status_code=self.status_code, error_code=self.error_code, payload={"email": email})

class InvalidPhoneError(LinkupError):
    status_code = 400
    error_code = "VAL_INVALID_PHONE"
    message = "מספר הטלפון שהוזן אינו תקין"
    def __init__(self, phone: Optional[str] = None):
        super().__init__(message=self.message, status_code=self.status_code, error_code=self.error_code, payload={"phone": phone})

class PasswordTooWeakError(LinkupError):
    status_code = 400
    error_code = "VAL_PASSWORD_TOO_WEAK"
    message = "הסיסמה חלשה מדי"
    def __init__(self, details: str = None):
        description = details or "על הסיסמה להכיל לפחות 8 תווים, אות גדולה, קטנה, מספר ותו מיוחד"
        super().__init__(message=f"{self.message}: {description}", status_code=self.status_code, error_code=self.error_code)

class InvalidFileTypeError(LinkupError):
    status_code = 400
    error_code = "VAL_INVALID_FILE_TYPE"
    message = "סוג הקובץ אינו נתמך. יש להשתמש ב-JPG, PNG או WebP"
    def __init__(self, content_type: Optional[str] = None):
        super().__init__(message=self.message, status_code=self.status_code, error_code=self.error_code, payload={"received_type": content_type})

class FileTooLargeError(LinkupError):
    status_code = 413
    error_code = "VAL_FILE_TOO_LARGE"
    message = "הקובץ גדול מדי עבור השרת"
    def __init__(self, max_size_mb: int, current_size_mb: Optional[float] = None):
        super().__init__(message=self.message, status_code=self.status_code, error_code=self.error_code, payload={"max_size_mb": max_size_mb, "current_size_mb": current_size_mb})

from fastapi import HTTPException, status

class InvalidEmailError(LinkupError):
    def __init__(self, email: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": f"כתובת האימייל שהוזנה אינה תקינה: {email}",
                "error_code": "AUTH_INVALID_EMAIL",
                "payload": {"email": email}
            }
        )

class InvalidPhoneError(LinkupError):
    def __init__(self, phone: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": f"מספר הטלפון אינו תקין (נדרש מספר ישראלי תקני): {phone}",
                "error_code": "AUTH_INVALID_PHONE",
                "payload": {"phone": phone}
            }
        )


from app.core.exceptions.base import LinkupError # או מאיפה שאתה מייבא את ה-Base

class InvalidLocationError(LinkupError):
    status_code = 400
    error_code = "INVALID_LOCATION"
    message = "המיקום שהוזן אינו תקין או מחוץ לטווח"

    def __init__(self, lat: float, lon: float, detail: str = None):
        # בונה הודעה שמפרטת מה הבעיה
        full_message = f"{self.message} ({lat}, {lon})"
        if detail:
            full_message += f": {detail}"
            
        super().__init__(
            message=full_message,
            payload={
                "latitude": lat, 
                "longitude": lon, 
                "detail": detail
            }
        )


from app.core.exceptions.base import LinkupError
from fastapi import status

class InvalidLocationError(LinkupError):
    """
    נזרקת כאשר כתובת או קואורדינטות אינן תקינות 
    או שלא ניתן למצוא עבורן מסלול במפות.
    """
    def __init__(self, detail: str = "מיקום לא תקין או לא נמצא"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            error_code="INVALID_LOCATION"
        )

class InsufficientSeatsError(LinkupError):
    """
    דוגמה לשגיאת ולידציה נוספת שתצטרך בהמשך - 
    נזרקת כשמנסים להזמין יותר מקומות ממה שיש בנסיעה.
    """
    def __init__(self, detail: str = "אין מספיק מקומות פנויים בנסיעה זו"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            error_code="INSUFFICIENT_SEATS"
        )


class SameOriginDestinationError(LinkupError):
    status_code = 400
    error_code = "VAL_SAME_ORIGIN_DESTINATION"
    message = "מוצא ויעד אינם יכולים להיות זהים"

    def __init__(self, location_name: Optional[str] = None):
        super().__init__(
            message=self.message,
            status_code=self.status_code,
            error_code=self.error_code,
            payload={"location": location_name} if location_name else None
        )