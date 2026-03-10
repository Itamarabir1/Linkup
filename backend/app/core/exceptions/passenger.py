from .base import LinkupError


class ActiveBookingExistsError(LinkupError):
    message = "כבר יש לך נסיעה פעילה"
    status_code = 409
    error_code = "PSG_ACTIVE_BOOKING"


class InsufficientPermissionsForRide(LinkupError):
    message = "אין לך הרשאה לגשת לנסיעה זו"
    status_code = 403
    error_code = "PSG_RIDE_ACCESS_DENIED"
