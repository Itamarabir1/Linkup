from pydantic import BaseModel, Field
from typing import List
import json

# המודל הבסיסי (כמו מקודם)
class RideSummary(BaseModel):
    driver_name: str
    passenger_name: str
    pickup_location: str
    meeting_time: str
    summary_hebrew: str

# מודל ה-Batch - זה מה שיאפשר לנו לקבל הכל במכה אחת
class BatchRideSummary(BaseModel):
    rides: List[RideSummary]