"""
עיבוד תמונת אווטאר — resize ל-3 גדלים והעלאה ל-S3.
דורש: Pillow>=10.0.0
"""

import io
import logging
from typing import TYPE_CHECKING

from PIL import Image

if TYPE_CHECKING:
    from app.infrastructure.s3.client import S3Client

logger = logging.getLogger(__name__)

SIZES = {
    "original.webp": (800, 800),
    "400x400.webp": (400, 400),
    "150x150.webp": (150, 150),
}
WEBP_QUALITY = 85


def _crop_center_square(img: Image.Image) -> Image.Image:
    """חיתוך למרכז לריבוע (צד = min(width, height))."""
    w, h = img.size
    side = min(w, h)
    left = (w - side) // 2
    top = (h - side) // 2
    return img.crop((left, top, left + side, top + side))


def _resize_and_encode_webp(img: Image.Image, size: tuple[int, int], quality: int = WEBP_QUALITY) -> bytes:
    """משנה גודל ל-size, ממיר ל-WebP, מחזיר bytes."""
    resized = img.resize(size, Image.Resampling.LANCZOS)
    buf = io.BytesIO()
    resized.save(buf, format="WEBP", quality=quality)
    return buf.getvalue()


async def process_and_save_avatar(
    staging_key: str,
    user_id: str,
    s3_client: "S3Client",
    storage_service,
) -> str:
    """
    1. מוריד תמונה מ-staging_key
    2. משנה גודל ל-3 גדלים (ריבוע מרכזי), WebP
    3. מוחק תיקייה ישנה avatars/{user_id}/
    4. מעלה 3 גרסאות ל-avatars/{user_id}/
    5. מוחק קובץ staging
    מחזיר avatar_key = "avatars/{user_id}/"
    """
    if not staging_key.startswith("avatars/staging/"):
        raise ValueError(f"Invalid staging key: {staging_key}")

    # 1. הורדה מ-staging
    body = await s3_client.get_object_bytes(staging_key)
    img = Image.open(io.BytesIO(body)).convert("RGB")

    # 2. חיתוך לריבוע ומערך של (filename, bytes) לכל גודל
    squared = _crop_center_square(img)
    uploads = []
    for filename, (w, h) in SIZES.items():
        blob = _resize_and_encode_webp(squared, (w, h))
        uploads.append((filename, blob))

    prefix = f"avatars/{user_id}/"

    # 3. מחיקת תיקייה ישנה
    await storage_service.delete_user_avatar_folder(user_id)

    # 4. העלאת 3 גרסאות
    for filename, blob in uploads:
        key = f"{prefix}{filename}"
        await s3_client.upload_fileobj(
            file_data=io.BytesIO(blob),
            key=key,
            content_type="image/webp",
        )
        logger.info("Uploaded avatar variant: %s", key)

    # 5. מחיקת staging
    await s3_client.delete_object(staging_key)
    logger.info("Deleted staging: %s", staging_key)

    return prefix
