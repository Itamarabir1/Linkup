from typing import Any, Dict, Optional
from .base import LinkupError

class StorageServiceError(LinkupError):
    """תקלה בחיבור ל-S3"""
    status_code = 503
    error_code = "INFRA_STORAGE_ERROR"
    message = "שירות אחסון הקבצים אינו זמין כעת"

    def __init__(self, payload: Optional[Dict[str, Any]] = None):
        super().__init__(payload=payload)

class CacheConnectionError(LinkupError):
    """תקלה בחיבור ל-Redis"""
    status_code = 503
    error_code = "INFRA_REDIS_ERROR"
    message = "שגיאת חיבור לשירות הזיכרון (Redis)"

    def __init__(self, payload: Optional[Dict[str, Any]] = None):
        super().__init__(payload=payload)

class QueueServiceError(LinkupError):
    """תקלה בחיבור ל-RabbitMQ"""
    status_code = 503
    error_code = "INFRA_RABBIT_ERROR"
    message = "שגיאת חיבור לשירות ההודעות (RabbitMQ)"
    
    def __init__(self, payload: Optional[Dict[str, Any]] = None):
        super().__init__(payload=payload)



class RouteNotFoundError(LinkupError):
    """נזרקת כאשר לא נמצא מסלול בין שתי נקודות."""
    status_code = 404
    error_code = "GEO_ROUTE_NOT_FOUND"
    message = "לא נמצא מסלול בין המיקומים שנבחרו"

    def __init__(self, origin: str, destination: str):
        super().__init__(
            message=f"לא נמצא מסלול נסיעה בין {origin} ל-{destination}.",
            payload={"origin": origin, "destination": destination}
        )

class GeocodingError(LinkupError):
    status_code = 422
    error_code = "GEO_ADDRESS_NOT_RESOLVED"
    message = "לא הצלחנו לאתר את הכתובת המבוקשת"

    def __init__(self, address: Optional[str] = None):
        super().__init__(
            message=self.message,
            status_code=self.status_code,
            error_code=self.error_code,
            payload={"address": address} if address else None
        )


class InfrastructureError(LinkupError):
    """שגיאות תשתית: Redis, DB, Network, וכו'."""
    status_code = 503
    error_code = "INFRA_ERROR"

    def __init__(self, message: str, detail: Optional[str] = None, error_code: Optional[str] = None):
        payload = {"detail": detail} if detail else None
        super().__init__(message=message, error_code=error_code or self.error_code, payload=payload)