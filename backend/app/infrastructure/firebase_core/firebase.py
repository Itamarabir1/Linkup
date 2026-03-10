"""
Firebase Admin SDK initialization.
For local development, create firebase-credentials.json from
firebase-credentials.example.json and fill in your service account values.
Do not commit real credentials; the real file is in .gitignore.
"""
import os
import json
import logging
import firebase_admin
from firebase_admin import credentials
from app.core.config import settings

logger = logging.getLogger(__name__)


def initialize_firebase():
    """מאתחל את Firebase פעם אחת עבור כל האפליקציה"""
    try:
        if not firebase_admin._apps:
            credentials_json = os.getenv("FIREBASE_CREDENTIALS_JSON")
            if credentials_json:
                # Production: load from environment variable
                credentials_dict = json.loads(credentials_json)
                cred = credentials.Certificate(credentials_dict)
            else:
                # Local development: load from file path
                cred = credentials.Certificate(settings.FIREBASE_SERVICE_ACCOUNT_PATH)
            firebase_admin.initialize_app(cred)
            logger.info("✅ Firebase Admin SDK initialized in Core")
    except Exception as e:
        logger.error(f"❌ Failed to initialize Firebase in Core: {e}")


# מריצים את האתחול מיד כשמייבאים את הקובץ
initialize_firebase()