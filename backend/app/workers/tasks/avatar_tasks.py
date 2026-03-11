"""
עיבוד אירועי העלאת ומחיקת אווטאר – תור נפרד (avatar_upload_queue).
ה-worker מקבל הודעות מ-exchange 'tasks' עם routing_key user.avatar_upload או user.avatar_remove.
"""

import logging
from typing import Dict, Any
from uuid import UUID

from app.core.utils.validators import slugify_for_avatar
from app.db.session import SessionLocal
from app.domain.users.crud import crud_user
from app.infrastructure.s3.service import storage_service

logger = logging.getLogger(__name__)

AVATAR_UPLOAD_EVENT = "user.avatar_upload"
AVATAR_REMOVE_EVENT = "user.avatar_remove"


async def handle_avatar_upload_event(data: Dict[str, Any], routing_key: str) -> None:
    """
    מעבד אירועי אווטאר: העלאה או מחיקה.
    - user.avatar_upload: finalize ב-S3 + עדכון avatar_url במסד.
    - user.avatar_remove: מחיקה מ-S3 (DB כבר עודכן ב-API).
    """
    if routing_key == AVATAR_UPLOAD_EVENT:
        await _handle_avatar_upload(data)
    elif routing_key == AVATAR_REMOVE_EVENT:
        await _handle_avatar_remove(data)
    else:
        logger.warning("Ignoring non-avatar event: %s", routing_key)


async def _handle_avatar_upload(data: Dict[str, Any]) -> None:
    """
    מעבד אירוע העלאת אווטאר: finalize ב-S3 (שם קובץ = slug משם המשתמש) + עדכון avatar_url במסד.
    payload: { "user_id": int, "staging_key": str }
    הערה: המחיקה של התמונה הישנה כבר בוצעה ב-API (לפי URL, מהיר), אז כאן רק finalize + DB update.
    """
    user_id = data.get("user_id")
    staging_key = data.get("staging_key")
    if user_id is None or not staging_key:
        logger.error(
            "Invalid avatar_upload payload: user_id=%s, staging_key=%s",
            user_id,
            staging_key,
        )
        raise ValueError("user_id and staging_key required")

    user_id = UUID(str(user_id))

    async with SessionLocal() as db:
        try:
            user = await crud_user.get_by_id(db, id=user_id)
            if not user:
                logger.error("User not found for avatar finalize: user_id=%s", user_id)
                raise ValueError(f"User not found: {user_id}")

            # מחיקת תמונה ישנה אם קיימת (לפני finalize)
            old_avatar_url = data.get("old_avatar_url")
            if old_avatar_url:
                try:
                    await storage_service.delete_old_avatar(old_avatar_url)
                    logger.info(
                        "Deleted old avatar before finalize: %s", old_avatar_url[:80]
                    )
                except Exception as e:
                    logger.warning(
                        "Could not delete old avatar URL %s: %s", old_avatar_url[:80], e
                    )

            # גם מוחקים לפי user_id (למקרה של שינוי שם)
            try:
                await storage_service.delete_avatar_by_user_id(user_id)
            except Exception as e:
                logger.warning("Could not delete avatar by user_id %s: %s", user_id, e)

            # Finalize: העברה מ-staging ל-final + עדכון DB
            base_name = slugify_for_avatar(user.full_name) or None
            final_url = await storage_service.finalize_avatar(
                staging_key=staging_key, user_id=user_id, base_name=base_name
            )
            user.avatar_url = final_url
            db.add(user)

            await db.commit()
            await db.refresh(user)
            logger.info("Avatar finalized for user %s: %s", user_id, final_url)

        except Exception:
            await db.rollback()
            logger.exception("Avatar upload processing failed: user_id=%s", user_id)
            raise


async def _handle_avatar_remove(data: Dict[str, Any]) -> None:
    """
    מעבד אירוע מחיקת אווטאר: מוחק מ-S3 לפי user_id.
    payload: { "user_id": int }
    הערה: avatar_url כבר אופס ב-DB ב-API, אז אנחנו רק מוחקים מ-S3.
    """
    user_id = data.get("user_id")
    if user_id is None:
        logger.error("Invalid avatar_remove payload: user_id=%s", user_id)
        raise ValueError("user_id required")

    user_id = UUID(str(user_id))

    async with SessionLocal() as db:
        try:
            # בודק שהמשתמש קיים (ולידציה)
            user = await crud_user.get_by_id(db, id=user_id)
            if not user:
                logger.error("User not found for avatar removal: user_id=%s", user_id)
                raise ValueError(f"User not found: {user_id}")

            # מוחק מ-S3 (DB כבר עודכן ב-API)
            await storage_service.delete_avatar_by_user_id(user_id)

            logger.info("Avatar removed from S3 for user %s", user_id)

        except Exception:
            logger.exception("Avatar removal processing failed: user_id=%s", user_id)
            raise
