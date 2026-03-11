"""
שירות צ'אט 1:1 – לוגיקה מעל CRUD, בניית תשובות (partner, last message).
אחרי שמירת הודעה – מפרסם ל-Redis Pub/Sub (שרת ה-WS ב-Go מאזין).
"""

import logging
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.domain.chat import crud as chat_crud
from app.domain.chat.schema import (
    ConversationListItem,
    ConversationDetail,
    ConversationPartner,
    MessageResponse,
)
from app.domain.users.crud import crud_user
from app.domain.bookings.model import Booking
from app.domain.bookings.enum import BookingStatus
from app.domain.rides.model import Ride
from app.infrastructure.events.publishers.redis import publish_chat_message

logger = logging.getLogger(__name__)


async def can_chat_about_booking(
    db: AsyncSession, booking_id: UUID, current_user_id: UUID
) -> tuple[bool, Booking | None]:
    """
    בודק אם המשתמש הנוכחי יכול לדבר על booking זה.
    מחזיר (is_allowed, booking) - רק אם המשתמש הוא הנהג או הנוסע של ה-booking
    והסטטוס הוא pending_approval או confirmed.
    """
    bid = UUID(str(booking_id)) if isinstance(booking_id, str) else booking_id
    result = await db.execute(
        select(Booking)
        .where(Booking.booking_id == bid)
    )
    booking = result.scalars().first()
    if not booking:
        return False, None

    # Load ride to get driver_id
    ride_result = await db.execute(select(Ride).where(Ride.ride_id == booking.ride_id))
    ride = ride_result.scalars().first()
    if not ride:
        return False, None

    # Check if current user is driver or passenger
    is_driver = ride.driver_id == current_user_id
    is_passenger = booking.passenger_id == current_user_id

    if not (is_driver or is_passenger):
        return False, None

    # Check status: only pending_approval or confirmed allow chat
    allowed_statuses = {BookingStatus.PENDING, BookingStatus.CONFIRMED}
    if booking.status not in allowed_statuses:
        return False, booking

    return True, booking


async def get_or_create_conversation(
    db: AsyncSession, current_user_id: UUID, other_user_id: UUID
) -> ConversationDetail:
    """
    מחזיר או יוצר שיחה בין current_user ל־other_user.
    מחזיר ConversationDetail (לשימוש בראוטר).
    """
    if other_user_id == current_user_id:
        raise ValueError("Cannot start conversation with yourself")
    other = await crud_user.get_by_id(db, id=other_user_id)
    if not other:
        raise ValueError("User not found")
    conv = await chat_crud.get_or_create_conversation(
        db, current_user_id, other_user_id
    )
    partner = ConversationPartner(
        user_id=other.user_id,
        full_name=other.full_name,
        avatar_url=other.avatar_url,
    )
    return ConversationDetail(
        conversation_id=conv.conversation_id,
        partner=partner,
        created_at=conv.created_at,
    )


async def get_or_create_conversation_by_booking(
    db: AsyncSession, booking_id: UUID, current_user_id: UUID
) -> ConversationDetail:
    """
    מחזיר או יוצר שיחה בין נהג לנוסע על בסיס booking_id.
    בודק הרשאות: רק נהג או נוסע של ה-booking יכולים לפתוח שיחה,
    ורק אם הסטטוס הוא pending_approval או confirmed.
    """
    is_allowed, booking = await can_chat_about_booking(db, booking_id, current_user_id)
    if not is_allowed:
        if booking is None:
            raise ValueError("Booking not found")
        raise ValueError(
            "You can only chat with the driver/passenger of a booking "
            "if the booking status is pending_approval or confirmed"
        )

    # Get the other user (driver if current is passenger, passenger if current is driver)
    ride_result = await db.execute(select(Ride).where(Ride.ride_id == booking.ride_id))
    ride = ride_result.scalars().first()
    if not ride:
        raise ValueError("Ride not found")

    driver_id = ride.driver_id
    passenger_id = booking.passenger_id

    # Determine the other user
    other_user_id = driver_id if current_user_id == passenger_id else passenger_id

    if other_user_id == current_user_id:
        raise ValueError("Cannot start conversation with yourself")

    other = await crud_user.get_by_id(db, id=other_user_id)
    if not other:
        raise ValueError("Other user not found")

    conv = await chat_crud.get_or_create_conversation(
        db, current_user_id, other_user_id
    )
    partner = ConversationPartner(
        user_id=other.user_id,
        full_name=other.full_name,
        avatar_url=other.avatar_url,
    )
    return ConversationDetail(
        conversation_id=conv.conversation_id,
        partner=partner,
        created_at=conv.created_at,
        booking_id=booking.booking_id,
    )


def _partner_from_conversation(conv, current_user_id: UUID) -> ConversationPartner:
    """מחזיר את הצד השני בשיחה (User → ConversationPartner)."""
    user = conv.user_2 if conv.user_id_1 == current_user_id else conv.user_1
    return ConversationPartner(
        user_id=user.user_id,
        full_name=user.full_name,
        avatar_url=user.avatar_url,
    )


async def list_my_conversations(
    db: AsyncSession, current_user_id: UUID
) -> list[ConversationListItem]:
    """
    רשימת שיחות של המשתמש עם פרטי הצד השני והודעה אחרונה.
    """
    convs = await chat_crud.list_conversations_for_user(db, current_user_id)
    out = []
    for conv in convs:
        partner_user = conv.user_2 if conv.user_id_1 == current_user_id else conv.user_1
        partner = ConversationPartner(
            user_id=partner_user.user_id,
            full_name=partner_user.full_name,
            avatar_url=partner_user.avatar_url,
        )
        last = await chat_crud.get_last_message(db, conv.conversation_id)
        out.append(
            ConversationListItem(
                conversation_id=conv.conversation_id,
                partner=partner,
                last_message_at=last.created_at if last else None,
                last_message_preview=(last.body[:80] + "…")
                if last and len(last.body) > 80
                else (last.body if last else None),
            )
        )
    return out


async def get_conversation_detail(
    db: AsyncSession, conversation_id: UUID, current_user_id: UUID
) -> ConversationDetail | None:
    """
    פרטי שיחה אחת – רק אם המשתמש participant.
    """
    conv = await chat_crud.get_conversation_by_id(db, conversation_id, current_user_id)
    if not conv:
        return None
    partner = _partner_from_conversation(conv, current_user_id)
    return ConversationDetail(
        conversation_id=conv.conversation_id,
        partner=partner,
        created_at=conv.created_at,
    )


async def send_message(
    db: AsyncSession,
    conversation_id: UUID,
    sender_id: UUID,
    body: str,
) -> MessageResponse | None:
    """
    שולח הודעה בשיחה: שמירה ב-DB + פרסום ל-Redis (שרת ה-WS ב-Go מאזין).
    אם ההודעה היא הודעת סיום — מפרסם אירוע ל-Redis DB=1; worker יטפל בניתוח AI.
    מחזיר MessageResponse אם המשתמש participant והשיחה קיימת.
    """
    from app.domain.chat.completion.detector import is_conversation_completion_message
    from app.infrastructure.redis.chat_completion_publish import (
        publish_chat_completion_event,
    )

    conv = await chat_crud.get_conversation_by_id(db, conversation_id, sender_id)
    if not conv:
        return None
    msg = await chat_crud.create_message(
        db, conversation_id=conversation_id, sender_id=sender_id, body=body
    )
    recipient_id = conv.user_id_2 if conv.user_id_1 == sender_id else conv.user_id_1
    payload = {
        "message_id": msg.message_id,
        "conversation_id": str(msg.conversation_id),
        "sender_id": str(msg.sender_id),
        "recipient_id": str(recipient_id),
        "body": msg.body,
        "created_at": msg.created_at.isoformat() if msg.created_at else None,
    }
    await publish_chat_message(conversation_id, payload)

    # בדיקה אם זו הודעת סיום — מפרסם ל-Redis DB=1; worker יטפל בניתוח AI
    if is_conversation_completion_message(body):
        try:
            await publish_chat_completion_event(conversation_id, sender_id)
        except Exception as e:
            logger.error("Error publishing chat completion event: %s", e, exc_info=True)

    return MessageResponse(
        message_id=msg.message_id,
        conversation_id=msg.conversation_id,
        sender_id=msg.sender_id,
        body=msg.body,
        created_at=msg.created_at,
    )


async def get_messages(
    db: AsyncSession,
    conversation_id: UUID,
    current_user_id: UUID,
    limit: int = 50,
    before_message_id: int | None = None,
) -> list[MessageResponse] | None:
    """
    היסטוריית הודעות בשיחה (pagination). None אם המשתמש לא participant.
    before_message_id remains int (BigInt in DB).
    """
    conv = await chat_crud.get_conversation_by_id(db, conversation_id, current_user_id)
    if not conv:
        return None
    messages = await chat_crud.get_messages(
        db,
        conversation_id=conversation_id,
        limit=limit,
        before_message_id=before_message_id,
    )
    return [
        MessageResponse(
            message_id=m.message_id,
            conversation_id=m.conversation_id,
            sender_id=m.sender_id,
            body=m.body,
            created_at=m.created_at,
        )
        for m in messages
    ]
