import logging
from typing import Dict, Any, Optional
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

# 1. Core, Security & Exceptions
from app.core.exceptions.user import (
    UserNotFoundError,
    EmailAlreadyRegisteredError,
)
from app.core.exceptions.validation import InvalidLocationError

# 2. Domain Schemas & Models
from app.domain.users.model import User
from app.domain.users.schema import UserUpdate
from app.domain.events.outbox import publish_to_outbox

# 3. Infrastructure & Services
from app.infrastructure.s3.service import storage_service
from app.domain.users.crud import crud_user
from app.domain.auth.service import auth_service

logger = logging.getLogger(__name__)
class UserService:
    def __init__(self):
        # הצמדת המופעים שהזרקנו מהייבוא ל-self
        self.s3 = storage_service 
        self.crud = crud_user
        # הוספנו את זה כדי שלא נצטרך לקרוא ל-auth_service גלובלי באמצע פונקציה
        self.auth = auth_service 

    async def get_user_by_id(self, db: AsyncSession, user_id: int) -> User:
        user = await self.crud.get_by_id(db, id=user_id)
        if not user:
            raise UserNotFoundError(user_id=user_id)
        return user

    async def schedule_avatar_upload(self, db: AsyncSession, user: User, file: UploadFile) -> None:
        """
        מעלה תמונת פרופיל דרך API: אם יש תמונה קיימת – מוחק אותה מה-S3 (לפי URL, מהיר),
        אז מעלה את החדשה ל-staging וכותב לאוטבוקס.
        ה-worker יעבד ברקע: finalize ל-S3 (שם קובץ = slug משם המשתמש) + עדכון avatar_url במסד.
        העלאה מתבצעת באמצעות streaming ישירות מ-UploadFile ל-S3 (בלי tempfile).
        """
        # מחיקה לפי user_id (מכסה גם מקרים של שינוי שם)
        try:
            await self.s3.delete_avatar_by_user_id(user.user_id)
            logger.info("Deleted old avatar(s) for user %s", user.user_id)
        except Exception as e:
            # לא נכשל אם המחיקה נכשלה - רק נרישום warning
            logger.warning("Could not delete old avatar(s) for user %s: %s", user.user_id, e)
        
        # מאפס avatar_url ב-DB (כדי שהמשתמש יראה שהתמונה מתעדכנת)
        await self.crud.update(db, db_obj=user, obj_in={"avatar_url": None})
        
        # מעלה את התמונה החדשה ל-staging (streaming ישירות, בלי tempfile)
        staging_key = await self.s3.upload_avatar_to_staging(file=file, user_id=user.user_id)
        
        # דוחף אירוע לתור - ה-worker יעשה finalize ברקע
        await publish_to_outbox(
            db,
            event_name="user.avatar_upload",
            payload={"user_id": user.user_id, "staging_key": staging_key},
        )
        await db.commit()
        logger.info("Avatar upload scheduled for user %s (staging_key=%s)", user.user_id, staging_key)

    async def get_avatar_upload_url(
        self, user_id: int, filename: Optional[str] = None, expiration: int = 300
    ) -> tuple[str, str]:
        """
        מחזיר presigned URL להעלאה ישירה ל-S3 staging.
        מחזיר: (presigned_url, staging_key)
        """
        presigned_url, staging_key = await self.s3.generate_avatar_upload_url(
            user_id=user_id, filename=filename, expiration=expiration
        )
        logger.info("Generated presigned URL for user %s: staging_key=%s", user_id, staging_key)
        return presigned_url, staging_key

    async def confirm_avatar_upload(
        self, db: AsyncSession, user: User, staging_key: str
    ) -> None:
        """
        מאשר העלאה לאחר שהלקוח העלה ישירות ל-S3 באמצעות presigned URL.
        דוחף אירוע לתור לעיבוד ברקע (finalize + DB update).
        """
        # וולידציה: בודק שה-staging_key שייך למשתמש
        if not staging_key.startswith(f"avatars/staging/{user.user_id}_"):
            logger.warning(
                "Invalid staging_key for user %s: %s (does not match user_id)",
                user.user_id,
                staging_key,
            )
            raise ValueError(f"Invalid staging_key for user {user.user_id}")

        # שמירת URL ישן לפני איפוס (למחיקה ב-worker)
        old_avatar_url = user.avatar_url
        await self.crud.update(db, db_obj=user, obj_in={"avatar_url": None})
        
        await publish_to_outbox(
            db,
            event_name="user.avatar_upload",
            payload={
                "user_id": user.user_id,
                "staging_key": staging_key,
                "old_avatar_url": old_avatar_url,
            },
        )
        await db.commit()
        logger.info("Avatar upload confirmed for user %s (staging_key=%s)", user.user_id, staging_key)

    async def remove_avatar(self, db: AsyncSession, user_id: int) -> None:
        """
        מסיר תמונת פרופיל: דוחף אירוע לתור לעיבוד ברקע (מחיקה מ-S3 + עדכון DB).
        מחזיר 202 מיד - העיבוד מתבצע ברקע על ידי ה-worker.
        """
        user = await self.get_user_by_id(db, user_id=user_id)
        
        # מאפס avatar_url ב-DB מיד (כדי שהמשתמש יראה שהתמונה נמחקה)
        await self.crud.update(db, db_obj=user, obj_in={"avatar_url": None})
        
        # דוחף אירוע לתור - ה-worker ימחק מ-S3 ברקע
        await publish_to_outbox(
            db,
            event_name="user.avatar_remove",
            payload={"user_id": user.user_id},
        )
        await db.commit()
        logger.info("Avatar removal scheduled for user %s", user_id)

    async def update_avatar(self, db: AsyncSession, user: User, file: UploadFile) -> str:
        old_avatar_url = user.avatar_url
        new_avatar_url = await self.s3.upload_user_avatar(file=file, user_id=user.user_id)
        
        user.avatar_url = new_avatar_url
        db.add(user)
        db.commit()
        db.refresh(user)
    
        if old_avatar_url:
            await self.s3.delete_old_avatar(old_avatar_url)

        logger.info(f"Avatar updated for user {user.user_id}")
        return new_avatar_url

    async def update_user_location(self, db: AsyncSession, user_id: int, lat: float, lon: float) -> bool:
        if not (-90 <= lat <= 90) or not (-180 <= lon <= 180) or (lat == 0 and lon == 0):
            raise InvalidLocationError(lat=lat, lon=lon)

        success = self.crud.update_location(db, user_id=user_id, lat=lat, lon=lon)
        if not success:
            raise UserNotFoundError(user_id=user_id)
        return True

    async def update_user_info(self, db: AsyncSession, user_id: int, update_data: UserUpdate) -> User:
        db_user = await self.get_user_by_id(db, user_id=user_id)
        update_dict = update_data.model_dump(exclude_unset=True)

        email_changed = False
        if "email" in update_dict and update_dict["email"] != db_user.email:
            if await self.crud.get_by_email(db, email=update_dict["email"]):
                raise EmailAlreadyRegisteredError(email=update_dict["email"])
            
            update_dict["is_verified"] = False
            email_changed = True

        updated_user = await self.crud.update(db, db_obj=db_user, obj_in=update_dict)

        if email_changed:
            # שימוש ב-self.auth במקום auth_service גלובלי
            await self.auth.initiate_email_verification(db, email=updated_user.email)

        return updated_user

    async def update_fcm_token(self, db: AsyncSession, user_id: int, fcm_token: str) -> bool:
        db_user = await self.get_user_by_id(db, user_id=user_id)
        await self.crud.update_fcm_token(db, user=db_user, token=fcm_token)
        return True

# יצירת המופע היחיד (Singleton)
user_service = UserService()