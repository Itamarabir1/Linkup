import firebase_admin
from firebase_admin import credentials
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

def initialize_firebase():
    """מאתחל את Firebase פעם אחת עבור כל האפליקציה"""
    try:
        if not firebase_admin._apps:
            cred = credentials.Certificate(settings.FIREBASE_SERVICE_ACCOUNT_PATH)
            firebase_admin.initialize_app(cred)
            logger.info("✅ Firebase Admin SDK initialized in Core")
    except Exception as e:
        logger.error(f"❌ Failed to initialize Firebase in Core: {e}")

# מריצים את האתחול מיד כשמייבאים את הקובץ
initialize_firebase()