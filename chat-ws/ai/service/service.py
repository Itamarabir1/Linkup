"""
שירות ניתוח AI לשיחות צ'אט – מאזין ל-Redis ומנתח כל הודעה.
שירות נפרד שרץ במקביל לשרת Go WebSocket.
"""
import asyncio
import json
import logging
from typing import Dict, Optional

import redis.asyncio as redis

from ..analyzer.analyzer import analyze_ride
from ..analyzer.schema import RideSummary
from .config import CHAT_CHANNEL_PATTERN, REDIS_URL
from .cache import ConversationCache
from .publisher import AnalysisPublisher

logger = logging.getLogger(__name__)


class ChatAnalyzerService:
    """
    שירות ניתוח AI – מאזין ל-Redis (chat:conversation:*), מנתח כל הודעה,
    ומפרסם תוצאה ל-Redis (chat:analysis:{conversation_id}).
    """
    
    def __init__(self, redis_url: str = REDIS_URL):
        self.redis_url = redis_url
        self.redis_client: Optional[redis.Redis] = None
        self.pubsub: Optional[redis.client.PubSub] = None
        self.cache: Optional[ConversationCache] = None
        self.publisher: Optional[AnalysisPublisher] = None
    
    async def connect(self):
        """חיבור ל-Redis"""
        self.redis_client = await redis.from_url(self.redis_url, decode_responses=True)
        self.pubsub = self.redis_client.pubsub()
        await self.pubsub.psubscribe(CHAT_CHANNEL_PATTERN)
        self.cache = ConversationCache(self.redis_client)
        self.publisher = AnalysisPublisher(self.redis_client)
        logger.info("✅ Chat Analyzer Service connected to Redis")
    
    async def disconnect(self):
        """סגירת חיבור Redis"""
        if self.pubsub:
            await self.pubsub.unsubscribe()
            await self.pubsub.close()
        if self.redis_client:
            await self.redis_client.close()
        logger.info("⚠️ Chat Analyzer Service disconnected")
    
    async def _analyze_conversation(self, conversation_id: int) -> Optional[RideSummary]:
        """
        מנתח שיחה שלמה ומחזיר RideSummary.
        """
        try:
            # אוסף את ההיסטוריה של השיחה
            conversation_text = await self.cache.get_conversation_history(conversation_id)
            
            if not conversation_text:
                logger.debug(f"No conversation history for {conversation_id}")
                return None
            
            # מנתח את השיחה
            logger.info(f"Analyzing conversation {conversation_id}...")
            result_json = analyze_ride(conversation_text)
            
            # ממיר JSON string חזרה ל-RideSummary
            result_dict = json.loads(result_json)
            ride_summary = RideSummary(**result_dict)
            
            logger.info(f"✅ Analysis complete for conversation {conversation_id}")
            return ride_summary
            
        except Exception as e:
            logger.error(f"❌ Analysis failed for conversation {conversation_id}: {e}", exc_info=True)
            return None
    
    async def _process_message(self, channel: str, message: str):
        """
        מעבד הודעת צ'אט: שומר ב-cache, מנתח את השיחה, מפרסם תוצאה.
        """
        try:
            # פרסור הודעת צ'אט
            msg_data = json.loads(message)
            conversation_id = msg_data.get("conversation_id")
            message_id = msg_data.get("message_id")
            
            if not conversation_id:
                logger.warning(f"Missing conversation_id in message from {channel}")
                return
            
            # שמירה ב-cache
            await self.cache.cache_message(conversation_id, msg_data)
            
            # ניתוח השיחה (כל ההודעות האחרונות)
            analysis = await self._analyze_conversation(conversation_id)
            
            if analysis:
                # פרסום תוצאה ל-Redis
                await self.publisher.publish_analysis(conversation_id, analysis)
            else:
                logger.debug(f"No analysis result for conversation {conversation_id}")
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse chat message from {channel}: {e}")
        except Exception as e:
            logger.error(f"Error processing message from {channel}: {e}", exc_info=True)
    
    async def run(self):
        """
        רץ את השירות – מאזין ל-Redis ומעבד כל הודעה.
        """
        await self.connect()
        
        try:
            logger.info("🚀 Chat Analyzer Service started - listening for chat messages...")
            
            async for message in self.pubsub.listen():
                if message["type"] == "pmessage":
                    channel = message["channel"]
                    payload = message["data"]
                    await self._process_message(channel, payload)
                    
        except asyncio.CancelledError:
            logger.info("Chat Analyzer Service cancelled")
        except Exception as e:
            logger.error(f"❌ Chat Analyzer Service error: {e}", exc_info=True)
        finally:
            await self.disconnect()


async def main():
    """Entry point להרצת השירות"""
    service = ChatAnalyzerService()
    try:
        await service.run()
    except KeyboardInterrupt:
        logger.info("Shutting down Chat Analyzer Service...")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    asyncio.run(main())
