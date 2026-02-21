"""
פרסום תוצאות ניתוח AI ל-Redis.
"""
import asyncio
import json
import logging
from typing import Optional

import redis.asyncio as redis

from ..analyzer.schema import RideSummary
from .config import ANALYSIS_CHANNEL_PREFIX

logger = logging.getLogger(__name__)


class AnalysisPublisher:
    """פרסום תוצאות ניתוח AI ל-Redis."""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis_client = redis_client
    
    async def publish_analysis(self, conversation_id: int, analysis: RideSummary):
        """
        מפרסם תוצאות ניתוח ל-Redis (chat:analysis:{conversation_id}).
        """
        channel = f"{ANALYSIS_CHANNEL_PREFIX}{conversation_id}"
        payload = {
            "conversation_id": conversation_id,
            "analysis": analysis.model_dump(),
            "timestamp": asyncio.get_event_loop().time(),
        }
        message = json.dumps(payload, ensure_ascii=False, default=str)
        
        count = await self.redis_client.publish(channel, message)
        logger.debug(f"Published analysis to {channel} ({count} subscriber(s))")
