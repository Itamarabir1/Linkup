import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, status
from app.api.dependencies.auth import get_current_user_ws

# כאן הטעות שלך - צריך לייבא את הסרוויס שמכיל את הפונקציה
from app.domain.notifications.services.notification_service import notification_service
logger = logging.getLogger(__name__)
router = APIRouter()

@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    user = Depends(get_current_user_ws),
):
    if not user:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await websocket.accept()
    logger.info(f"🔌 WebSocket connection accepted for user: {user.id}")
    
    try:
        # הקריאה הנכונה דרך ה-Instance של ה-Service
        await notification_service.stream_user_notifications(websocket, user.id)
        
    except WebSocketDisconnect:
        logger.info(f"👋 User {user.id} disconnected")
    except Exception as e:
        logger.error(f"❌ Unexpected error in WebSocket for user {user.id}: {e}")
        # כאן אפשר להשתמש ב-LinkupError אם תרצה לעטוף שגיאות תשתית