import enum
class PassengerStatus(str, enum.Enum):
    ACTIVE = "active"  # DB enum value for new/searching request
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    COMPLETED = "completed"
    EXPIRED = "expired"
    MATCHED = "matched"
    CANCELLED = "cancelled"