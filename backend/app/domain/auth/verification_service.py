# app/domain/auth/verification_service.py
import random
import string
import logging
from app.infrastructure.redis.client import redis_client
from app.infrastructure.redis.keys import OTP_VERIFICATION_TTL, get_otp_verification_key
from app.core.exceptions.auth import (
    InvalidVerificationCodeError,
    VerificationCodeExpiredError,
)

logger = logging.getLogger(__name__)


class VerificationService:
    @staticmethod
    def generate_otp(length: int = 6) -> str:
        return "".join(random.choices(string.digits, k=length))

    async def create_verification_event(self, user_id: str, event_name: str) -> str:
        code = self.generate_otp()
        redis_key = get_otp_verification_key(user_id, event_name)
        # שמירה גנרית לכל סוגי האירועים (מייל, סיסמה וכו')
        await redis_client.save(key=redis_key, data=code, expire=OTP_VERIFICATION_TTL)
        return code

    async def verify_otp(self, user_id: str, event_name: str, input_code: str) -> None:
        """מאמת קוד וזורק שגיאה מתאימה אם נכשל"""
        redis_key = get_otp_verification_key(user_id, event_name)
        stored_code = await redis_client.get(redis_key)

        if not stored_code:
            raise VerificationCodeExpiredError()  # יורש מ-LinkupError

        if str(stored_code) != str(input_code):
            raise InvalidVerificationCodeError()

        await redis_client.delete(redis_key)


verification_service = VerificationService()
