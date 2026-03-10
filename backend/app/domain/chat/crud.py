"""
CRUD צ'אט 1:1 – שיחות והודעות.
תמיד שומרים user_id_1 < user_id_2 ב־Conversation.
"""

from sqlalchemy import select, desc, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from datetime import datetime, timedelta

from app.domain.chat.model import Conversation, Message, ChatAnalysis

# --- Conversations ---


async def get_or_create_conversation(
    db: AsyncSession, user_id_a: int, user_id_b: int
) -> Conversation:
    """
    מחזיר שיחה קיימת בין שני המשתמשים, או יוצר חדשה.
    user_id_1 < user_id_2 תמיד.
    """
    u1, u2 = min(user_id_a, user_id_b), max(user_id_a, user_id_b)
    if u1 == u2:
        raise ValueError("Cannot create conversation with self")

    result = await db.execute(
        select(Conversation).where(
            Conversation.user_id_1 == u1,
            Conversation.user_id_2 == u2,
        )
    )
    conv = result.scalars().first()
    if conv:
        return conv

    conv = Conversation(user_id_1=u1, user_id_2=u2)
    db.add(conv)
    await db.commit()
    await db.refresh(conv)
    return conv


async def get_conversation_by_id(
    db: AsyncSession, conversation_id: int, participant_user_id: int
) -> Conversation | None:
    """
    מחזיר שיחה לפי ID רק אם המשתמש הוא participant (user_id_1 או user_id_2).
    """
    result = await db.execute(
        select(Conversation)
        .options(
            selectinload(Conversation.user_1),
            selectinload(Conversation.user_2),
        )
        .where(
            Conversation.conversation_id == conversation_id,
            or_(
                Conversation.user_id_1 == participant_user_id,
                Conversation.user_id_2 == participant_user_id,
            ),
        )
    )
    return result.scalars().first()


async def list_conversations_for_user(
    db: AsyncSession, user_id: int
) -> list[Conversation]:
    """
    רשימת כל השיחות של המשתמש (כשותף).
    """
    result = await db.execute(
        select(Conversation)
        .options(
            selectinload(Conversation.user_1),
            selectinload(Conversation.user_2),
        )
        .where(
            or_(
                Conversation.user_id_1 == user_id,
                Conversation.user_id_2 == user_id,
            )
        )
        .order_by(desc(Conversation.created_at))
    )
    return list(result.scalars().unique().all())


async def get_conversations_with_timeout(
    db: AsyncSession,
    timeout_hours: int = 24,
) -> list[Conversation]:
    """
    מחזיר שיחות שלא נשלח להן סיכום ושההודעה האחרונה בהן היא לפני timeout_hours שעות.

    Args:
        db: AsyncSession
        timeout_hours: מספר שעות ללא הודעות חדשות (ברירת מחדל: 24)

    Returns:
        רשימת שיחות שצריכות ניתוח
    """
    # זמן גבול: עכשיו פחות timeout_hours
    timeout_threshold = datetime.utcnow() - timedelta(hours=timeout_hours)

    # שאילתה: שיחות שיש להן הודעה אחרונה לפני timeout_threshold
    # ואין להן ניתוח AI (chat_analysis)
    subquery = (
        select(
            Message.conversation_id,
            func.max(Message.created_at).label("last_message_at"),
        )
        .group_by(Message.conversation_id)
        .having(func.max(Message.created_at) < timeout_threshold)
        .subquery()
    )

    # שיחות שיש להן הודעה אחרונה לפני timeout, ואין להן ניתוח
    result = await db.execute(
        select(Conversation)
        .options(
            selectinload(Conversation.user_1),
            selectinload(Conversation.user_2),
        )
        .join(subquery, Conversation.conversation_id == subquery.c.conversation_id)
        .outerjoin(
            ChatAnalysis, Conversation.conversation_id == ChatAnalysis.conversation_id
        )
        .where(ChatAnalysis.conversation_id.is_(None))  # אין ניתוח קיים
    )
    return list(result.scalars().unique().all())


# --- Messages ---


async def create_message(
    db: AsyncSession,
    conversation_id: int,
    sender_id: int,
    body: str,
) -> Message:
    """שומר הודעה חדשה בשיחה."""
    msg = Message(
        conversation_id=conversation_id,
        sender_id=sender_id,
        body=body,
    )
    db.add(msg)
    await db.commit()
    await db.refresh(msg)
    return msg


async def get_messages(
    db: AsyncSession,
    conversation_id: int,
    limit: int = 50,
    before_message_id: int | None = None,
) -> list[Message]:
    """
    היסטוריית הודעות בשיחה (pagination).
    before_message_id = אופציונלי, לשליפה "לפני" הודעה מסוימת.
    """
    q = (
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(desc(Message.created_at))
        .limit(limit + 1)
    )
    if before_message_id is not None:
        sub = select(Message.created_at).where(Message.message_id == before_message_id)
        q = q.where(Message.created_at < sub.scalar_subquery())
    result = await db.execute(q)
    messages = list(result.scalars().unique().all())
    return messages[::-1]  # ישן → חדש


async def get_last_message(db: AsyncSession, conversation_id: int) -> Message | None:
    """הודעה אחרונה בשיחה (להרשימה)."""
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(desc(Message.created_at))
        .limit(1)
    )
    return result.scalars().first()
