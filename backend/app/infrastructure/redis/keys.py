# תוקף שמירת תצוגת המסלולים (כולל 3 המסלולים) ב-Redis – 24 שעות
RIDE_PREVIEW_TTL = 86400  # 24 שעות (בשניות)

def get_ride_preview_key(session_id: str) -> str:
    return f"ride_preview:{session_id}"


OTP_VERIFICATION_TTL = 600  # 10 דקות

def get_otp_verification_key(user_id: str, event_name: str) -> str:
    """מייצר מפתח אחיד לקוד אימות ב-Redis"""
    return f"otp:{event_name}:{user_id}"