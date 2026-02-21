"""
ניתוח AI של שיחות צ'אט - שירותים לניתוח ושימוש בתוצאות.
"""
import logging
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.chat import crud as chat_crud

logger = logging.getLogger(__name__)


async def get_conversation_text_for_analysis(
    db: AsyncSession,
    conversation_id: int,
    current_user_id: int,
    limit: int = 50,
) -> Optional[str]:
    """
    אוסף את טקסט השיחה לניתוח AI.
    מחזיר None אם המשתמש לא participant או השיחה לא קיימת.
    
    Returns:
        מחרוזת טקסט בפורמט: "User_{sender_id}: {body}\nUser_{sender_id}: {body}..."
    """
    # וידוא שהמשתמש participant
    conv = await chat_crud.get_conversation_by_id(db, conversation_id, current_user_id)
    if not conv:
        return None
    
    # איסוף הודעות
    messages = await chat_crud.get_messages(
        db,
        conversation_id=conversation_id,
        limit=limit,
        before_message_id=None,
    )
    
    if not messages:
        return None
    
    # בניית טקסט שיחה
    conversation_lines = []
    for msg in messages:
        conversation_lines.append(f"User_{msg.sender_id}: {msg.body}")
    
    return "\n".join(conversation_lines)
