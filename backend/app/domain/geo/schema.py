from pydantic import BaseModel, Field
from typing import List, Optional


class GeoLocation(BaseModel):
    lat: float
    lon: float


class AddressFromCoordsResponse(BaseModel):
    """תשובה משותפת ל־reverse geocoding – נהג ונוסע ממלאים שדה מקום ממיקום נוכחי."""

    address: str = Field(..., description="כתובת קריאה (reverse geocode)")
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)


class RouteOptionData(BaseModel):
    summary: str
    duration_min: float
    distance_km: float
    coords: List[List[float]]  # רשימה של [lat, lon]


class LocationUpdate(BaseModel):
    booking_id: int
    latitude: float = Field(..., alias="lat")  # תמיכה גם ב-lat וגם ב-latitude
    longitude: float = Field(..., alias="lon")
    heading: Optional[float] = 0.0  # כיוון הנסיעה באייקון

    class Config:
        populate_by_name = True  # מאפשר לשלוח גם 'lat' וגם 'latitude'
