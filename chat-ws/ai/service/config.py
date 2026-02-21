"""
קונפיגורציה וקבועים לשירות ניתוח AI.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ערוץ Redis לשיחות צ'אט
CHAT_CHANNEL_PATTERN = "chat:conversation:*"
# ערוץ Redis לתוצאות ניתוח
ANALYSIS_CHANNEL_PREFIX = "chat:analysis:"

# Redis URL (אותו כמו ב-backend)
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Cache של הודעות אחרונות לכל שיחה (לניתוח של כל השיחה, לא רק הודעה אחת)
# מפתח: conversation_id, ערך: רשימת הודעות (JSON)
CONVERSATION_CACHE_PREFIX = "chat:conversation_cache:"
CACHE_MAX_MESSAGES = 50  # כמה הודעות אחרונות לשמור לכל שיחה
CACHE_TTL_SECONDS = 7 * 24 * 60 * 60  # TTL של 7 ימים
