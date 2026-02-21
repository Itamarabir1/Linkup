from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.api.dependencies.auth import get_current_user
from app.api.dependencies.file import validate_avatar
from app.domain.users.service import user_service
from app.domain.users.model import User
from app.domain.users.schema import (
    UserRead,
    UserUpdate,
    FCMTokenUpdate,
    UserLocationUpdate,
    MessageResponse,
    AvatarUploadAcceptedResponse,
    AvatarUploadUrlRequest,
    AvatarUploadUrlResponse,
    AvatarUploadConfirmRequest,
)
from app.domain.rides.schema import RideResponse
from app.domain.bookings.service import BookingService
from app.domain.bookings.schema import NotificationItemResponse
from pydantic import BaseModel, HttpUrl

router = APIRouter(tags=["Users"])  # prefix="/users" ניתן ב-api_router

# --- 1. הפרופיל שלי ---
@router.get("/me", response_model=UserRead)
async def get_my_profile(current_user: User = Depends(get_current_user)):
    """מחזיר את פרטי המשתמש המחובר (כולל מידע רגיש כמו אימות)"""
    return current_user


# --- התראות (מסך התראות) ---
@router.get("/me/notifications", response_model=List[NotificationItemResponse])
async def get_my_notifications(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """כל ההתראות של המשתמש: כנהג – בקשות להצטרפות; כנוסע – אישור/דחייה/ממתין."""
    return await BookingService.get_notifications_for_user(db, current_user.user_id)

# --- 2. עדכון טוקן FCM (פוש נוטיפיקציות) ---
@router.patch("/fcm-token", response_model=MessageResponse)
async def update_fcm_token(
    data: FCMTokenUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await user_service.update_fcm_token(
        db, 
        user_id=current_user.user_id, 
        fcm_token=data.fcm_token
    )
    
    # עדיף להחזיר מופע של הסכמה
    return MessageResponse(
        message="FCM Token updated successfully", 
        status="success"
    )

# --- 5. העלאת תמונת פרופיל (שתי דרכים) ---

# דרך 1: Presigned URL (מומלץ - 202 מהיר יותר)
@router.get(
    "/me/avatar/upload-url",
    response_model=AvatarUploadUrlResponse,
    status_code=status.HTTP_200_OK,
)
async def get_avatar_upload_url(
    filename: Optional[str] = None,
    current_user: User = Depends(get_current_user),
):
    """
    מחזיר presigned URL להעלאה ישירה ל-S3.
    התהליך:
    1. הלקוח קורא endpoint זה → מקבל presigned URL + staging_key
    2. הלקוח מעלה ישירות ל-S3 באמצעות ה-URL (5-8 שניות)
    3. הלקוח קורא ל-POST /me/avatar/confirm עם staging_key
    4. השרת דוחף לתור ומחזיר 202 מיד (שנייה)
    5. Worker מעבד ברקע (finalize + DB update)
    """
    presigned_url, staging_key = await user_service.get_avatar_upload_url(
        user_id=current_user.user_id, filename=filename
    )
    return AvatarUploadUrlResponse(
        upload_url=presigned_url,
        staging_key=staging_key,
        expires_in=300,  # 5 דקות
    )


@router.post(
    "/me/avatar/confirm",
    response_model=AvatarUploadAcceptedResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def confirm_avatar_upload(
    data: AvatarUploadConfirmRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    מאשר העלאה לאחר שהלקוח העלה ישירות ל-S3 באמצעות presigned URL.
    דוחף אירוע לתור ומחזיר 202 מיד - העיבוד (finalize + DB update) מתבצע ברקע.
    """
    await user_service.confirm_avatar_upload(db, current_user, data.staging_key)
    return AvatarUploadAcceptedResponse()


# דרך 2: העלאה דרך API (streaming ישירות, בלי tempfile)
@router.post(
    "/me/avatar",
    response_model=AvatarUploadAcceptedResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def upload_my_avatar(
    file: UploadFile = Depends(validate_avatar),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    מעלה תמונת פרופיל דרך API (streaming ישירות מ-UploadFile ל-S3, בלי tempfile).
    אם יש תמונה קיימת – מוחק מענן ומ-DB ואז מעלה את החדשה.
    מחזיר 202 (התמונה בהעלאה) – העיבוד (S3 + עדכון DB) מתבצע ברקע.
    בפרונט: להציג "התמונה בהעלאה" ולעדכן את avatar_url כשמוכן (polling GET /me או WebSocket).
    
    הערה: מומלץ להשתמש ב-GET /me/avatar/upload-url + POST /me/avatar/confirm לקבלת 202 מהיר יותר.
    """
    await user_service.schedule_avatar_upload(db, current_user, file)
    return AvatarUploadAcceptedResponse()


@router.delete(
    "/me/avatar",
    response_model=AvatarUploadAcceptedResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def remove_my_avatar(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    מסיר תמונת פרופיל: דוחף אירוע לתור ומחזיר 202 מיד.
    העיבוד (מחיקה מ-S3) מתבצע ברקע על ידי ה-worker.
    """
    await user_service.remove_avatar(db, user_id=current_user.user_id)
    return AvatarUploadAcceptedResponse(message="Avatar removal accepted", status="accepted")



# --- עדכון פרטי פרופיל (שם, אימייל וכו') ---
@router.put("/me", response_model=UserRead)
async def update_my_profile(
    data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    עדכון פרטי המשתמש המחובר. 
    מקבל אובייקט UserUpdate ומעביר אותו כפי שהוא לסרוויס.
    """
    return await user_service.update_user_info(
        db, 
        user_id=current_user.user_id, 
        update_data=data # מעביר את כל הסכימה
    )


# --- 3. עדכון מיקום (לחיפוש טרמפים בסביבה) ---
# @router.patch("/me/location", response_model=MessageResponse)
# async def update_my_location(
#     data: UserLocationUpdate,
#     db: AsyncSession = Depends(get_db),
#     current_user: User = Depends(get_current_user),
# ):
#     # הלוגיקה וזריקת LinkupError יקרו בתוך הסרוויס
#     await user_service.update_user_location(
#         db, 
#         user_id=current_user.user_id, 
#         lat=data.latitude, 
#         lon=data.longitude
#     )
    
#     return MessageResponse(
#         message="Location updated successfully", 
#         status="success"
#     )
# --- 4. צפייה בפרופיל ציבורי ---
# @router.get("/{user_id}", response_model=UserPublicRead)
# async def get_user_public_profile(
#     user_id: int, 
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     """צפייה בנהג/נוסע אחר - מחזיר רק שם, תמונה, דירוג ותאריך הצטרפות"""
#     user = await UserService.get_user_by_id(db, user_id=user_id)
#     if not user:
#         raise HTTPException(status_code=404, detail="User not found")
#     return user

