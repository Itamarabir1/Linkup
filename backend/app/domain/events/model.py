from typing import List, Dict, Any
from pydantic import BaseModel, Field

# מייבאים את ה-Enum מהקובץ המרכזי שלו
from app.domain.events.enum import DispatchTarget


class Event(BaseModel):
    """
    Domain Event Schema.
    זהו 'החוזה' של האירוע במערכת.
    """

    name: str = Field(..., min_length=1)
    payload: Dict[str, Any]
    targets: List[DispatchTarget] = Field(..., min_items=1)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        # הופך את האובייקט ל-Immutable (לקריאה בלבד)
        frozen = True
        # מאפשר עבודה חלקה עם אובייקטים של SQLAlchemy
        from_attributes = True
