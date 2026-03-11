import logging
from typing import Union
from uuid import UUID
from fastapi import WebSocket, WebSocketDisconnect

# התיקון הארכיטקטוני: במקום לייבא את Redis ישירות, מייבאים את ה-Bus
from app.infrastructure.websocket_bus import ws_infra

logger = logging.getLogger(__name__)


class NotificationStreamer:
    """
    אחראי על הזרמת מידע בזמן אמת מהתשתית (Bus) לצינור הפיזי (WebSocket).
    """

    async def stream_user_notifications(
        self, websocket: WebSocket, user_id: Union[UUID, str, int]
    ):
        """
        פותח האזנה לערוץ המשתמש ומזרים הודעות עד לניתוק.
        """
        channel_name = f"user_{user_id}"

        try:
            # שלב 1: קבלת הסאבסקרייבר מהתשתית (ws_infra)
            # שימוש ב-await כי get_subscriber היא פונקציה אסינכרונית
            subscriber_ctx = await ws_infra.get_subscriber(channel_name)

            async with subscriber_ctx as subscriber:
                logger.info(f"🔌 WebSocket subscription active for: {channel_name}")

                # שלב 2: לולאת הזרמה (Event Loop)
                async for event in subscriber:
                    try:
                        # שליחת ההודעה לקליינט בפורמט טקסט
                        await websocket.send_text(event.message)

                    except (WebSocketDisconnect, ConnectionResetError):
                        # ניתוק תקין של המשתמש (סגר טאב/איבד אינטרנט)
                        logger.info(f"👋 User {user_id} disconnected from WebSocket.")
                        break

                    except Exception as send_error:
                        # שגיאה בלתי צפויה בשליחה
                        logger.error(
                            f"⚠️ Failed to push message to user {user_id}: {send_error}"
                        )
                        break

        except Exception as e:
            # שגיאה קריטית בתשתית (למשל ה-Broker נפל)
            logger.error(f"❌ Critical Streamer error for user {user_id}: {str(e)}")

        finally:
            # שלב 3: ניקוי משאבים תמיד קורה כאן
            logger.debug(f"🧹 Cleaned up stream resources for user {user_id}")


# Singleton instance לשימוש ב-Router
notification_streamer = NotificationStreamer()
