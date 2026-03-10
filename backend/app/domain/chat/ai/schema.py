"""
Schema לניתוח AI של שיחות צ'אט.
"""

from pydantic import BaseModel


class RideSummary(BaseModel):
    """סיכום ניתוח AI של שיחת טרמפ."""

    driver_name: str
    passenger_name: str
    pickup_location: str
    meeting_time: str
    summary_hebrew: str
