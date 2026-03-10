"""
שירות אימות Google OAuth - אימות ID tokens מ-Google Sign-In.
מאמת את ה-ID token עם Google ומחזיר את ה-payload (email, name, picture, sub).
"""

import logging
from typing import Dict, Any
from google.auth.transport import requests
from google.oauth2 import id_token
from app.core.config import settings

logger = logging.getLogger(__name__)


def verify_google_id_token(id_token_str: str) -> Dict[str, Any]:
    """
    מאמת ID token מ-Google Sign-In.

    בודקת:
    - Signature (חתימה דיגיטלית)
    - Expiration (תוקף)
    - Audience (GOOGLE_CLIENT_ID)
    - Issuer (accounts.google.com)

    מחזירה את ה-payload (email, name, picture, sub, וכו').

    Raises:
        ValueError: אם ה-token לא תקין או לא מאומת
    """
    if not settings.GOOGLE_CLIENT_ID:
        raise ValueError("GOOGLE_CLIENT_ID not configured")

    try:
        # אימות ה-ID token עם Google
        # request_object נדרש ל-google-auth כדי לבצע HTTP requests
        request = requests.Request()

        # verify_oauth2_token מאמת את ה-token ומחזיר את ה-payload
        # זה יכול לקחת זמן אם צריך להוריד public keys מ-Google
        logger.info("Verifying Google ID token...")
        idinfo = id_token.verify_oauth2_token(
            id_token_str, request, settings.GOOGLE_CLIENT_ID
        )
        logger.info("Google ID token verified successfully")

        # בדיקה נוספת שה-issuer הוא Google
        if idinfo["iss"] not in ["accounts.google.com", "https://accounts.google.com"]:
            raise ValueError("Wrong issuer.")

        # החזרת ה-payload
        return {
            "sub": idinfo.get("sub"),  # Google user ID
            "email": idinfo.get("email"),
            "email_verified": idinfo.get("email_verified", False),
            "name": idinfo.get("name"),
            "picture": idinfo.get("picture"),
            "given_name": idinfo.get("given_name"),
            "family_name": idinfo.get("family_name"),
        }

    except ValueError as e:
        logger.error(f"Google ID token verification failed: {e}")
        raise ValueError(f"Invalid Google ID token: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error verifying Google ID token: {e}", exc_info=True)
        raise ValueError(f"Failed to verify Google ID token: {str(e)}")
