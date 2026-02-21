"""
ניהול cache של הודעות שיחה ב-Redis.
"""
import json
import logging
from typing import Dict, Optional

import redis.asyncio as redis

from .config import CONVERSATION_CACHE_PREFIX, CACHE_MAX_MESSAGES, CACHE_TTL_SECONDS

logger = logging.getLogger(__name__)


class ConversationCache:
    """ניהול cache של הודעות שיחה ב-Redis."""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis_client = redis_client
    
    async def get_conversation_history(self, conversation_id: int) -> str:
        """
        אוסף את ההיסטוריה של השיחה מה-cache ב-Redis.
        מחזיר טקסט שיחה בפורמט: "שם1: הודעה1\nשם2: הודעה2\n..."
        """
        cache_key = f"{CONVERSATION_CACHE_PREFIX}{conversation_id}"
        messages_json = await self.redis_client.lrange(cache_key, 0, CACHE_MAX_MESSAGES - 1)
        
        if not messages_json:
            return ""
        
        # ממיר JSON strings חזרה ל-dicts ובונה טקסט שיחה
        conversation_lines = []
        for msg_json in reversed(messages_json):  # מהראשון לאחרון
            try:
                msg = json.loads(msg_json)
                sender_id = msg.get("sender_id", "Unknown")
                body = msg.get("body", "")
                conversation_lines.append(f"User_{sender_id}: {body}")
            except json.JSONDecodeError:
                continue
        
        return "\n".join(conversation_lines)
    
    async def cache_message(self, conversation_id: int, message: Dict):
        """
        שומר הודעה ב-cache של השיחה (רשימה ב-Redis).
        שומר רק את CACHE_MAX_MESSAGES האחרונות.
        """
        cache_key = f"{CONVERSATION_CACHE_PREFIX}{conversation_id}"
        message_json = json.dumps(message, ensure_ascii=False)
        
        # מוסיף לתחילת הרשימה (LPUSH)
        await self.redis_client.lpush(cache_key, message_json)
        # שומר רק את CACHE_MAX_MESSAGES האחרונות
        await self.redis_client.ltrim(cache_key, 0, CACHE_MAX_MESSAGES - 1)
        # TTL של 7 ימים (אחרי זה ה-cache נמחק)
        await self.redis_client.expire(cache_key, CACHE_TTL_SECONDS)
