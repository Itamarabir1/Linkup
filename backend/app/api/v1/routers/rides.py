import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.domain.rides.schema import RidePreviewResponse, RideCreate, RidePreviewCreate, RideResponse, RideUpdate
from app.core.exceptions.ride import RideNotFoundError
from app.infrastructure.redis.broadcast import broadcast
from app.domain.users.model import User
from app.api.dependencies.auth import get_current_user
from app.domain.rides.service import ride_service

logger = logging.getLogger(__name__)
router = APIRouter()

# --- Routes רגילים (HTTP) ---
@router.post("/preview-routes", response_model=RidePreviewResponse)
async def preview_ride_options(
    preview_in: RidePreviewCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user) # הוספנו את המשתמש המחובר
):
    """שלב 1: קבלת אפשרויות מסלול ומחירים"""
    return await ride_service.get_ride_preview(preview_in)



@router.post("/", status_code=status.HTTP_201_CREATED, response_model=RideResponse)
async def create_new_ride(
    ride_in: RideCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # הראוטר רק "מזמין" את הפעולה. הוא לא מנהל לוגיקה או שגיאות.
    return await ride_service.create_ride(
        db=db, 
        ride_in=ride_in, 
        current_user_id=current_user.user_id
    )

@router.get("/me", response_model=List[RideResponse])
async def get_my_rides(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    status: Optional[str] = Query(None, description="סנן לפי סטטוס: open, full, cancelled, completed"),
):
    """רשימת הנסיעות שלי כנהג."""
    return await ride_service.get_my_rides(db, current_user.user_id, status=status)


@router.patch("/{ride_id}", response_model=RideResponse)
async def update_ride(
    ride_id: int,
    payload: RideUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """עדכון חלקי לנסיעה – זמן יציאה ו/או מספר מושבים (רק הנהג בעלים)."""
    try:
        return await ride_service.update_ride(db, ride_id, current_user.user_id, payload)
    except RideNotFoundError:
        raise HTTPException(status_code=404, detail="נסיעה לא נמצאה או שאין הרשאה")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{ride_id}/cancel", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_ride(
    ride_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await ride_service.cancel_ride_by_driver(
        db=db,
        ride_id=ride_id,
        driver_id=current_user.user_id,
    )

@router.get("/{ride_id}", response_model=RideResponse)
async def read_ride(ride_id: int, db: AsyncSession = Depends(get_db)):
    ride = await ride_service.get_ride_by_id(db, ride_id)
    if not ride:
        raise HTTPException(status_code=404, detail="נסיעה לא נמצאה")
    return ride

# --- הצינור החי (WebSocket) ---

@router.websocket("/ws/{ride_id}")
async def ride_status_websocket(websocket: WebSocket, ride_id: int):
    """
    כאן קורה הקסם: הדפדפן מתחבר לכתובת הזו ונשאר בהאזנה.
    """
    await websocket.accept()
    channel_name = f"ride_{ride_id}"
    logger.info(f"Client connected to WebSocket for ride: {ride_id}")
    
    try:
        # הראוטר נכנס להאזנה לרדיס על הערוץ הספציפי של הנסיעה
        async with broadcast.subscribe(channel=channel_name) as subscriber:
            async for event in subscriber:
                # כשמגיעה הודעה (כמו color: red), היא נשלחת מיד לדפדפן
                await websocket.send_text(event.message)
                
    except WebSocketDisconnect:
        logger.info(f"Client disconnected from ride {ride_id}")