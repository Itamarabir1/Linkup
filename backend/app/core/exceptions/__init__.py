# app/core/exceptions/__init__.py
"""ייצוא מרכזי של כל שגיאות הדומיין – שימוש: from app.core.exceptions import LinkupError, UserNotFoundError, ..."""
from .base import LinkupError

# Auth
from .auth import (
    SessionExpiredError,
    PermissionDeniedError,
    InvalidVerificationCodeError,
    InvalidCredentialsError,
    UserNotVerifiedError,
    InvalidResetCodeError,
    InvalidRefreshTokenError,
    InvalidPasswordError,
    PasswordTooWeakError,
    PasswordsDoNotMatchError,
    NewPasswordSameAsOldError,
    VerificationCodeExpiredError,
)

# User
from .user import (
    UserNotFoundError,
    PhoneAlreadyRegisteredError,
    EmailAlreadyRegisteredError,
    PasswordSameAsOldError,
)

# Ride
from .ride import (
    RideNotFoundError,
    InvalidRideStatusError,
    InvalidRouteError,
    InvalidDateTimeError,
    RideFullError,
    SessionExpiredError as RideSessionExpiredError,
    RideAlreadyCancelledError,
)

# Booking
from .booking import (
    RideNotAvailableError,
    BookingAlreadyExistsError,
    PassengerRequestNotFoundError,
    BookingNotFoundError,
    ForbiddenRideActionError,
)

# Passenger
from .passenger import (
    ActiveBookingExistsError,
    InsufficientPermissionsForRide,
)

# Validation
from .validation import (
    InvalidEmailError,
    InvalidPhoneError,
    InvalidFileTypeError,
    FileTooLargeError,
    InvalidLocationError,
    InsufficientSeatsError,
    SameOriginDestinationError,
)

# Infrastructure
from .infrastructure import (
    StorageServiceError,
    CacheConnectionError,
    QueueServiceError,
    RouteNotFoundError,
    GeocodingError,
    InfrastructureError,
)

# Notification
from .notification import (
    NotificationError,
    RecipientResolverError,
    ContextBuilderError,
)

__all__ = [
    "LinkupError",
    "SessionExpiredError",
    "PermissionDeniedError",
    "InvalidVerificationCodeError",
    "InvalidCredentialsError",
    "UserNotVerifiedError",
    "InvalidResetCodeError",
    "InvalidRefreshTokenError",
    "InvalidPasswordError",
    "PasswordTooWeakError",
    "PasswordsDoNotMatchError",
    "NewPasswordSameAsOldError",
    "VerificationCodeExpiredError",
    "UserNotFoundError",
    "PhoneAlreadyRegisteredError",
    "EmailAlreadyRegisteredError",
    "PasswordSameAsOldError",
    "RideNotFoundError",
    "InvalidRideStatusError",
    "InvalidRouteError",
    "InvalidDateTimeError",
    "RideFullError",
    "RideSessionExpiredError",
    "RideAlreadyCancelledError",
    "RideNotAvailableError",
    "BookingAlreadyExistsError",
    "PassengerRequestNotFoundError",
    "BookingNotFoundError",
    "ForbiddenRideActionError",
    "ActiveBookingExistsError",
    "InsufficientPermissionsForRide",
    "InvalidEmailError",
    "InvalidPhoneError",
    "InvalidFileTypeError",
    "FileTooLargeError",
    "InvalidLocationError",
    "InsufficientSeatsError",
    "SameOriginDestinationError",
    "StorageServiceError",
    "CacheConnectionError",
    "QueueServiceError",
    "RouteNotFoundError",
    "GeocodingError",
    "InfrastructureError",
    "NotificationError",
    "RecipientResolverError",
    "ContextBuilderError",
]
