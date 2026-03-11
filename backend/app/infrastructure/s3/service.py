"""
שירות אחסון S3 – אווטאר: staging (ע"י API או presigned URL) ו-finalize (ע"י worker).
מבנה: avatars/staging/{user_id}_{uuid}.ext → avatars/{base_name}-{user_id}.ext (base_name = slug משם המשתמש).
"""

import uuid
import logging
from typing import Optional, Union
from uuid import UUID

from fastapi import UploadFile

from app.infrastructure.s3.client import s3_client

logger = logging.getLogger(__name__)

STAGING_PREFIX = "avatars/staging/"
FINAL_PREFIX = "avatars/"


def _normalize_avatar_ext(filename: str | None) -> str:
    """מחזיר סיומת תמונה תקינה (jpeg, jpg, png, webp)."""
    ext = (filename or "").split(".")[-1].lower() if "." in (filename or "") else "jpg"
    if ext not in ("jpeg", "jpg", "png", "webp"):
        ext = "jpg"
    return ext


class StorageService:
    def __init__(self):
        self.client = s3_client

    def _ext_from_key(self, key: str) -> str:
        return key.split(".")[-1] if "." in key else "jpg"

    async def upload_avatar_to_staging(self, file: UploadFile, user_id: Union[UUID, int, str]) -> str:
        """
        מעלה קובץ ל-S3 staging. מחזיר staging_key לשימוש ב-outbox ו-worker.
        """
        uid_str = str(user_id)
        ext = _normalize_avatar_ext(file.filename)
        staging_key = f"{STAGING_PREFIX}{uid_str}_{uuid.uuid4().hex}.{ext}"

        # Streaming ישירות מ-UploadFile ל-S3 - בלי tempfile ובלי לקרוא הכל לזיכרון
        await self.client.upload_fileobj(
            file_data=file.file,
            key=staging_key,
            content_type=file.content_type or f"image/{ext}",
        )
        logger.info("Avatar uploaded to staging: key=%s", staging_key)
        return staging_key

    async def generate_avatar_upload_url(
        self, user_id: Union[UUID, int, str], filename: Optional[str] = None, expiration: int = 300
    ) -> tuple[str, str]:
        """
        יוצר presigned URL להעלאה ישירה ל-S3 staging.
        מחזיר: (presigned_url, staging_key)
        """
        uid_str = str(user_id)
        ext = _normalize_avatar_ext(filename)
        staging_key = f"{STAGING_PREFIX}{uid_str}_{uuid.uuid4().hex}.{ext}"
        content_type = f"image/{ext}"

        presigned_url = await self.client.generate_presigned_upload_url(
            key=staging_key,
            content_type=content_type,
            expiration=expiration,
        )

        logger.info("Generated presigned URL for avatar upload: key=%s", staging_key)
        return presigned_url, staging_key

    async def finalize_avatar(
        self, staging_key: str, user_id: Union[UUID, int, str], base_name: Optional[str] = None
    ) -> str:
        """
        מעביר מ-staging ל-final, מוחק staging, מחזיר URL סופי.
        base_name = slug משם המשתמש (full_name) – שם הקובץ יהיה {base_name}-{user_id}.ext.
        """
        uid_str = str(user_id)
        if not staging_key.startswith(STAGING_PREFIX):
            raise ValueError(f"Invalid staging key: {staging_key}")
        ext = self._ext_from_key(staging_key)
        if base_name:
            final_key = f"{FINAL_PREFIX}{base_name}-{uid_str}.{ext}"
        else:
            final_key = f"{FINAL_PREFIX}{uid_str}.{ext}"

        # מחיקת קובץ קיים אם יש (למקרה של החלפה)
        try:
            await self.client.delete_object(final_key)
        except Exception:
            pass  # לא קיים או כבר נמחק - זה בסדר

        final_url = await self.client.copy_object(
            source_key=staging_key, dest_key=final_key
        )
        await self.client.delete_object(staging_key)
        logger.info("Avatar finalized: %s -> %s", staging_key, final_key)
        return final_url

    async def upload_user_avatar(self, file: UploadFile, user_id: Union[UUID, int, str]) -> str:
        """העלאה סינכרונית ישירה (לשימוש לא-תור). מבנה: users/{user_id}/avatars/{uuid}.ext"""
        uid_str = str(user_id)
        ext = (
            (file.filename or "").split(".")[-1]
            if "." in (file.filename or "")
            else "jpg"
        )
        key = f"users/{uid_str}/avatars/{uuid.uuid4()}.{ext}"
        return await self.client.upload_fileobj(
            file_data=file.file,
            key=key,
            content_type=file.content_type or "image/jpeg",
        )

    def _url_to_key(self, url: str) -> Optional[str]:
        """מחלץ S3 object key מ-URL (תומך ב-virtual-hosted ו-path-style)."""
        if not url or not url.strip():
            return None
        raw = url.strip().split("?")[0]
        if ".com/" not in raw:
            return None
        # אחרי .com/ יש path: virtual-hosted = "key" או path-style = "bucket/key"
        path = raw.split(".com/", 1)[-1]
        if not path or path.startswith("http"):
            return None
        # Path-style: path = "bucket/key" – להסיר את שם ה-bucket
        bucket_prefix = self.client.bucket_name + "/"
        if path.startswith(bucket_prefix):
            path = path[len(bucket_prefix) :]
        return path if path else None

    async def delete_old_avatar(self, avatar_url: str) -> None:
        """מחיקת אווטאר ישן לפי URL (מחלץ key מה-URL). זורק אם המחיקה נכשלת."""
        if not avatar_url:
            return
        key = self._url_to_key(avatar_url)
        if not key:
            logger.error("Could not extract S3 key from avatar_url: %s", avatar_url)
            raise ValueError(
                f"Cannot extract S3 key from avatar_url: {avatar_url[:80]!r}"
            )
        logger.info("Deleting avatar from S3: key=%s (url=%s)", key, avatar_url[:80])
        await self.client.delete_object(key)
        logger.info("Avatar deleted from S3: key=%s", key)

    async def delete_avatar_by_user_id(self, user_id: Union[UUID, int, str]) -> None:
        """
        מוחק מ-S3 את תמונת הפרופיל של המשתמש.
        מחפש: avatars/{user_id}.*, avatars/*-{user_id}.*, users/{user_id}/avatars/
        """
        uid_str = str(user_id)
        prefixes = [
            f"{FINAL_PREFIX}{uid_str}",  # avatars/<uuid>.jpg
            f"users/{uid_str}/avatars/",
        ]
        for prefix in prefixes:
            keys = await self.client.list_objects_by_prefix(prefix)
            for key in keys:
                await self._delete_avatar_key(key, uid_str)
        keys_all_avatars = await self.client.list_objects_by_prefix(FINAL_PREFIX)
        for key in keys_all_avatars:
            if f"-{uid_str}." in key:
                await self._delete_avatar_key(key, uid_str)

    async def _delete_avatar_key(self, key: str, user_id_label: str) -> None:
        try:
            await self.client.delete_object(key)
            logger.info("S3 deleted avatar by user_id: key=%s", key)
        except Exception as e:
            logger.error("S3 delete failed for key=%s: %s", key, e, exc_info=True)
            raise

    async def delete_file(self, file_url: str) -> None:
        """מחיקת קובץ לפי URL (חילוץ key)."""
        try:
            key = file_url.split(".com/")[-1].split("?")[0]
            if key:
                await self.client.delete_object(key)
        except Exception as e:
            logger.warning("Failed to delete file %s: %s", file_url, e)


storage_service = StorageService()
