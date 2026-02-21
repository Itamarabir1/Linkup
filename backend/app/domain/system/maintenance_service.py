import logging
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.system.maintenance_crud import crud_maintenance

logger = logging.getLogger(__name__)

class MaintenanceService:
    """
    Service layer to manage system-wide maintenance.
    Encapsulates transaction logic and business rules.
    """

    async def run_full_system_cleanup(self, db: AsyncSession) -> dict:
        """מנהל את תהליך הניקוי ברמת השירות"""
        now = datetime.now()
        try:
            results = await crud_maintenance.bulk_update_expired_entities(db, now)
            await db.commit()
            rides, req_exp, req_comp, bookings = results
            return {
                "rides": rides,
                "expired_requests": req_exp,
                "completed_requests": req_comp,
                "bookings": bookings
            }
        except Exception as e:
            await db.rollback()
            logger.error(f"❌ Maintenance Service Error: {str(e)}", exc_info=True)
            raise

# יצירת מופע יחיד לייבוא בשאר המערכת
maintenance_service = MaintenanceService()