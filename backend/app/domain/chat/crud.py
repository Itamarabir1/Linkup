"""
CRUD צ'אט 1:1 – שיחות והודעות.
תמיד שומרים user_id_1 < user_id_2 ב־Conversation.
"""

from uuid import UUID
from sqlalchemy import select, desc, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from datetime import datetime, timedelta

from app.domain.chat.model import Conversation, Message, ChatAnalysis

# --- Conversations ---


async def get_or_create_conversation(
    db: AsyncSession, user_id_a: UUID, user_id_b: UUID
) -> Conversation:
    """
    מחזיר שיחה קיימת בין שני המשתמשים, או יוצר חדשה.
    user_id_1 < user_id_2 תמיד.
    """
    u1_raw, u2_raw = (user_id_a, user_id_b) if user_id_a < user_id_b else (user_id_b, user_id_a)
    u1 = UUID(str(u1_raw)) if isinstance(u1_raw, str) else u1_raw
    u2 = UUID(str(u2_raw)) if isinstance(u2_raw, str) else u2_raw
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
    db: AsyncSession, conversation_id: UUID, participant_user_id: UUID
) -> Conversation | None:
    """
    מחזיר שיחה לפי ID רק אם המשתמש הוא participant (user_id_1 או user_id_2).
    """
    cid = UUID(str(conversation_id)) if isinstance(conversation_id, str) else conversation_id
    pid = UUID(str(participant_user_id)) if isinstance(participant_user_id, str) else participant_user_id
    result = await db.execute(
        select(Conversation)
        .options(
            selectinload(Conversation.user_1),
            selectinload(Conversation.user_2),
        )
        .where(
            Conversation.conversation_id == cid,
            or_(
                Conversation.user_id_1 == pid,
                Conversation.user_id_2 == pid,
            ),
        )
    )
    return result.scalars().first()


async def list_conversations_for_user(
    db: AsyncSession, user_id: UUID
) -> list[Conversation]:
    """
    רשימת כל השיחות של המשתמש (כשותף).
    """
    uid = UUID(str(user_id)) if isinstance(user_id, str) else user_id
    result = await db.execute(
        select(Conversation)
        .options(
            selectinload(Conversation.user_1),
            selectinload(Conversation.user_2),
        )
        .where(
            or_(
                Conversation.user_id_1 == uid,
                Conversation.user_id_2 == uid,
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
    conversation_id: UUID,
    sender_id: UUID,
    body: str,
) -> Message:
    """שומר הודעה חדשה בשיחה."""
    cid = UUID(str(conversation_id)) if isinstance(conversation_id, str) else conversation_id
    sid = UUID(str(sender_id)) if isinstance(sender_id, str) else sender_id
    msg = Message(
        conversation_id=cid,
        sender_id=sid,
        body=body,
    )
    db.add(msg)
    await db.commit()
    await db.refresh(msg)
    return msg


async def get_messages(
    db: AsyncSession,
    conversation_id: UUID,
    limit: int = 50,
    before_message_id: int | None = None,
) -> list[Message]:
    """
    היסטוריית הודעות בשיחה (pagination).
    before_message_id = אופציונלי, לשליפה "לפני" הודעה מסוימת (int – BigInt ב-DB).
    """
    cid = UUID(str(conversation_id)) if isinstance(conversation_id, str) else conversation_id
    q = (
        select(Message)
        .where(Message.conversation_id == cid)
        .order_by(desc(Message.created_at))
        .limit(limit + 1)
    )
    if before_message_id is not None:
        sub = select(Message.created_at).where(Message.message_id == before_message_id)
        q = q.where(Message.created_at < sub.scalar_subquery())
    result = await db.execute(q)
    messages = list(result.scalars().unique().all())
    return messages[::-1]  # ישן → חדש


async def get_last_message(db: AsyncSession, conversation_id: UUID) -> Message | None:
    """הודעה אחרונה בשיחה (להרשימה)."""
    cid = UUID(str(conversation_id)) if isinstance(conversation_id, str) else conversation_id
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == cid)
        .order_by(desc(Message.created_at))
        .limit(1)
    )
    return result.scalars().first()
